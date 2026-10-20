import re

import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def trigger_reconciliation_for_queued_docs():
    if not frappe.db.get_single_value("Accounts Settings", "auto_reconcile_payments"):
        frappe.msgprint(
            _("Auto Reconciliation of Payments has been disabled. Enable it through {0}").format(
                get_link_to_form("Accounts Settings", "Accounts Settings")
            )
        )    
        return
        
    all_queued = frappe.db.get_all(
        "Process Payment Reconciliation",
        filters={"docstatus": 1, "status": "Queued"},
        order_by="creation desc",
        as_list=1,
    )
    
    docs_to_trigger = []
    unique_filters = set()
    queue_size = 5
    
    fields = ["company", "party_type", "party", "receivable_payable_account"]


@frappe.whitelist()
def get_upload_progress(progress_id):
    """Latest progress of upload_landed_cost_file (polled by the browser)."""
    return frappe.cache.get_value(f"landed_cost_progress:{progress_id}") or {}


@frappe.whitelist()
def upload_landed_cost_file(file_url, against_account, purchase_receipt, progress_id=None):
    """Read the uploaded PDF with landed_cost_invoice_reader.execute and return the rows as JSON."""
    from ksa_customizations.landed_cost_invoice_reader import execute

    frappe.flags.landed_cost_progress_id = progress_id
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    rows = execute(file_doc.get_full_path())

    seller_name = next((row.get("account") for row in rows if row.get("account")), "")
    # Account for each line, from its Landed Cost Expense Category
    for row in rows:
        row["account"] = row.get("expense_account") or ""
    invoice = {
        "invoice_date": next((row.get("invoice_date") for row in rows if row.get("invoice_date")), ""),
        "invoice_no": next((row.get("invoice_no") for row in rows if row.get("invoice_no")), ""),
        "seller_tax_id": next((row.get("sell_trn") for row in rows if row.get("sell_trn")), ""),
        "seller_name": seller_name,
    }
    # Kept on the server for create_landed_cost_journal_entry, so the browser only sends the table rows
    frappe.cache.set_value(upload_cache_key(file_url), invoice, expires_in_sec=24 * 60 * 60)
    buyer_check = check_buyer(
        frappe.db.get_value("Purchase Receipt", purchase_receipt, "company"),
        next((row.get("bill_name") for row in rows if row.get("bill_name")), ""),
        next((row.get("bill_TRN") for row in rows if row.get("bill_TRN")), ""),
    )
    return {"against_account": against_account, "purchase_receipt": purchase_receipt, "rows": rows,
            "file_url": file_url, "buyer_check": buyer_check, **invoice}


def upload_cache_key(file_url):
    return f"landed_cost_upload:{frappe.session.user}:{file_url}"


BUYER_NAME_MIN_SCORE = 0.8                       # buyer_name counts as the company name from this similarity
# Words that do not tell companies apart, dropped before comparing names
COMPANY_FILLER_WORDS = {"شركه", "مؤسسه", "مصنع", "مكتب", "مجموعه", "للتجاره", "التجاريه", "تجاره", "ذات",
                        "المسئوليه", "المسؤوليه", "المحدوده", "محدوده", "llc", "ltd", "co", "company", "est",
                        "trading", "trade", "group", "corp", "inc", "for", "the", "and"}


def company_name_key(name):
    """Name reduced for comparing: normalized, no punctuation, no filler words."""
    from ksa_customizations.landed_cost_invoice_reader import normalize

    words = re.sub(r"[^\w\s]", " ", normalize(name)).split()
    words = [w for w in words if w not in COMPANY_FILLER_WORDS] or words
    return " ".join(words)


def name_similarity(a, b):
    """0..1: how close two company names are (1 = same after normalizing, or one contains the other)."""
    from difflib import SequenceMatcher

    a, b = company_name_key(a), company_name_key(b)
    if not a or not b:
        return 0.0
    if a == b or a in b or b in a:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def check_buyer(company, buyer_name, buyer_vat_id):
    """Compare the invoice's buyer (bill_name: close to company_name_in_arabic, bill_TRN: exactly tax_id)
    with the Company of the Purchase Receipt.
    Each status is "match", "mismatch" or "missing" (not found in the invoice / not set on the Company)."""
    fields = ["tax_id"]
    if frappe.get_meta("Company").has_field("company_name_in_arabic"):
        fields.append("company_name_in_arabic")
    doc = frappe.db.get_value("Company", company, fields, as_dict=True) or frappe._dict()
    company_name = doc.get("company_name_in_arabic") or ""
    company_vat = re.sub(r"\D", "", doc.get("tax_id") or "")

    score = name_similarity(buyer_name, company_name)
    if not buyer_name or not company_name:
        name_status = "missing"
    else:
        name_status = "match" if score >= BUYER_NAME_MIN_SCORE else "mismatch"

    invoice_vats = {re.sub(r"\D", "", part) for part in (buyer_vat_id or "").split(",")} - {""}
    if not invoice_vats or not company_vat:
        vat_status = "missing"
    else:
        vat_status = "match" if company_vat in invoice_vats else "mismatch"

    return {"company": company, "company_name": company_name, "company_vat_id": company_vat,
            "buyer_name": buyer_name or "", "buyer_vat_id": buyer_vat_id or "",
            "name_status": name_status, "name_score": round(score * 100),
            "vat_status": vat_status}


def find_vendor_by_tax_id(tax_id):
    """The Vendor whose vendor_tax_id matches the seller's VAT number (digits only). None if no match."""
    numbers = {re.sub(r"\D", "", part) for part in (tax_id or "").split(",")} - {""}
    if not numbers:
        return None
    for vendor in frappe.get_all("Vendor", filters={"vendor_tax_id": ["is", "set"]},
                                 fields=["name", "vendor_name", "vendor_tax_id"]):
        if re.sub(r"\D", "", vendor.vendor_tax_id) in numbers:
            return vendor
    return None


@frappe.whitelist()
def create_landed_cost_journal_entry(purchase_receipt, accounts, file_url=None):
    """Create a draft Landed Cost Entry journal entry from the dialog table, dated on the invoice date
    (also bill_date, with bill_no = the invoice number) and with the processed invoice PDF attached.
    party_name / party_tax_id come from the Vendor whose vendor_tax_id matches the seller's VAT number.
    The invoice fields come from the server cache filled by upload_landed_cost_file.

    accounts: list of {account, account_ar, debit, credit} (description is ignored).
    """
    accounts = frappe.parse_json(accounts)
    if not accounts:
        frappe.throw(_("There are no accounting entries to post"))

    invoice = (frappe.cache.get_value(upload_cache_key(file_url)) if file_url else None) or {}
    invoice_date = invoice.get("invoice_date")
    invoice_no = invoice.get("invoice_no")
    seller_tax_id = invoice.get("seller_tax_id")

    company = frappe.db.get_value("Purchase Receipt", purchase_receipt, "company")
    if not company:
        frappe.throw(_("Purchase Receipt {0} was not found").format(purchase_receipt))

    has_category_field = frappe.get_meta("Journal Entry Account").has_field("landed_cost_category")

    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Landed Cost Entry"
    je.company = company
    try:
        je.bill_date = frappe.utils.getdate(invoice_date) if invoice_date else None
    except Exception:                                # date not readable -> no bill date
        je.bill_date = None
    je.posting_date = je.bill_date or frappe.utils.today()
    je.bill_no = (invoice_no or "").strip()

    vendor = find_vendor_by_tax_id(seller_tax_id)
    if vendor and frappe.get_meta("Journal Entry").has_field("party_name"):
        je.party_name = vendor.name
        je.party_tax_id = vendor.vendor_tax_id

    for row in accounts:
        category = (row.get("account_ar") or "").strip()
        line = {
            "account": row.get("account"),
            "debit_in_account_currency": flt(row.get("debit")),
            "credit_in_account_currency": flt(row.get("credit")),
            "reference_type": "Purchase Receipt",
            "reference_name": purchase_receipt,
            "landed_cost_category": row.get("account_ar")
        }
        je.append("accounts", line)

    je.insert()

    # Attach the processed invoice (same file, linked to the journal entry)
    if file_url:
        source = frappe.db.get_value("File", {"file_url": file_url}, ["file_name", "is_private"], as_dict=True)
        if source:
            frappe.get_doc({
                "doctype": "File",
                "file_url": file_url,
                "file_name": source.file_name,
                "is_private": source.is_private,
                "attached_to_doctype": "Journal Entry",
                "attached_to_name": je.name,
            }).insert()
    # Vendor found by VAT number: check that its name is close to the seller name on the invoice
    seller_name = invoice.get("seller_name") or ""
    vendor_name = (vendor.vendor_name or vendor.name) if vendor else ""
    vendor_name_score = round(name_similarity(seller_name, vendor_name) * 100) if vendor and seller_name else None
    return {"name": je.name, "vendor": vendor.name if vendor else None, "seller_tax_id": seller_tax_id or "",
            "bill_no": je.bill_no, "bill_date": je.bill_date,
            "seller_name": seller_name, "vendor_name": vendor_name, "vendor_name_score": vendor_name_score,
            "vendor_name_matches": vendor_name_score is None or vendor_name_score >= BUYER_NAME_MIN_SCORE * 100}


def get_old_landed_cost_vouchers(purchase_receipt):
    return frappe.get_all(
        "Landed Cost Purchase Receipt",
        filters={"receipt_document_type": "Purchase Receipt", "receipt_document": purchase_receipt},
        pluck="parent",
        distinct=True,
    )


@frappe.whitelist()
def create_actual_landed_cost_voucher(purchase_receipt):
    """Replace the Landed Cost Vouchers of a Purchase Receipt with one built from the journal entries
    that reference it (Landed Cost Entry lines), using Landed Cost Settings to pick the accounts."""
    pr = frappe.get_doc("Purchase Receipt", purchase_receipt)
    if pr.docstatus != 1:
        frappe.throw(_("Purchase Receipt {0} must be submitted").format(purchase_receipt))

    # 1. Landed Cost Settings rows by account
    categories = frappe.get_list("Landed Cost Expense Category", fields=["*"])
    mapping = {}
    for row in categories:
        if row.expense_account:
            mapping.setdefault(row.expense_account, row)

    # 2. Net amount (debit - credit) per account and category from the journal entries that reference the receipt
    has_category = frappe.get_meta("Journal Entry Account").has_field("landed_cost_category")
    category_select = "ifnull(jea.landed_cost_category, '')" if has_category else "''"
    movements = frappe.db.sql(
        f"""
        select jea.account, {category_select} as category,
            sum(jea.debit_in_account_currency) - sum(jea.credit_in_account_currency) as amount
        from `tabJournal Entry Account` jea
        inner join `tabJournal Entry` je on je.name = jea.parent
        where je.docstatus = 1
            and jea.reference_type = 'Purchase Receipt'
            and jea.reference_name = %s
        group by jea.account, {category_select}
        """,
        purchase_receipt,
        as_dict=True,
    )

    # 3. Only accounts marked include_in_lcv become rows of the voucher, with the category as description
    charges = []
    for m in movements:
        row = mapping.get(m.account)
        if row and row.include_in_landed_cost_voucher and flt(m.amount):
            charges.append(
                {
                    "expense_account": m.account,
                    "description": row.category or row.category_en or m.account,
                    "amount": flt(m.amount),
                }
            )
    if not charges:
        frappe.throw(_("No journal entry amounts to include in a Landed Cost Voucher for {0}").format(purchase_receipt))

    # Remove the old Landed Cost Vouchers of this receipt
    old_vouchers = get_old_landed_cost_vouchers(purchase_receipt)
    for name in old_vouchers:
        others = frappe.db.count(
            "Landed Cost Purchase Receipt", {"parent": name, "receipt_document": ["!=", purchase_receipt]}
        )
        if others:
            frappe.throw(
                _("Landed Cost Voucher {0} also includes other receipts, remove it manually first").format(name)
            )
    for name in old_vouchers:
        old = frappe.get_doc("Landed Cost Voucher", name)
        if old.docstatus == 1:
            old.cancel()
        frappe.delete_doc("Landed Cost Voucher", name)

    # 4. New voucher
    lcv = frappe.new_doc("Landed Cost Voucher")
    lcv.company = pr.company
    lcv.posting_date = frappe.utils.today()
    lcv.shipment = pr.title
    lcv.append(
        "purchase_receipts",
        {
            "receipt_document_type": "Purchase Receipt",
            "receipt_document": pr.name,
            "supplier": pr.supplier,
            "posting_date": pr.posting_date,
            "grand_total": pr.base_grand_total,
        },
    )
    lcv.get_items_from_purchase_receipts()
    for charge in charges:
        lcv.append("taxes", charge)
    lcv.insert()
    lcv.submit()
    return lcv.name


ESTIMATED_LCV_DESCRIPTION = "تقديري"


def get_estimated_landed_cost(purchase_receipt):
    """Estimated landed cost (company currency) and its account, from the Estimated Landed Cost of the
    item groups of the receipt and the linked Purchase Invoice."""
    result = frappe.db.sql(
        """
        WITH
        landed_cost_breakdown AS (
            SELECT elc.name AS item_group, elc.estimated_landed_cost_account, elc.exchange_rate, elcd.expense_name, elcd.expense_type, elcd.value
            FROM `tabEstimated Landed Cost Detail` elcd
            INNER JOIN `tabEstimated Landed Cost` elc ON elcd.parent = elc.name
        ),
        purchase_receipt_detail AS (
            SELECT DISTINCT i.item_group, pi.cntr_vol, pi.pod, pr.grand_total,
                   IF(pi.incoterm = 'FOB', pi.cntr_vol * pi.freight_per_cntr, 0) AS freight
            FROM `tabPurchase Receipt Item` pri
            INNER JOIN `tabPurchase Receipt` pr ON pri.parent = pr.name
            INNER JOIN `tabPurchase Invoice` pi ON pri.purchase_invoice = pi.name
            INNER JOIN `tabItem` i ON pri.item_code = i.name
            WHERE pri.docstatus = 1 AND pr.is_return = 0
              AND pr.name = %(purchase_receipt)s
        )
        SELECT MAX(lcbd.estimated_landed_cost_account) AS expense_account,
            ROUND((SUM(
            CASE
                WHEN lcbd.expense_type = 'Percentage-wise' AND lcbd.expense_name = 'Customs Duties' THEN pid.grand_total * lcbd.exchange_rate * lcbd.value + pid.grand_total * lcbd.exchange_rate * lcbd.value * 0.03 + pid.freight * 3.76 * lcbd.value
                WHEN lcbd.expense_type = 'Percentage-wise' AND lcbd.expense_name != 'Customs Duties' THEN pid.grand_total * lcbd.exchange_rate * lcbd.value
                WHEN lcbd.expense_type = 'Container-wise' AND lcbd.expense_name = 'DMM to JED Transport' AND pid.pod = 'Dammam' THEN pid.cntr_vol * lcbd.value
                WHEN lcbd.expense_type = 'Container-wise' AND lcbd.expense_name = 'Transportation' AND pid.pod != 'Dammam' THEN pid.cntr_vol * lcbd.value
                WHEN lcbd.expense_type = 'Container-wise' AND lcbd.expense_name NOT IN ('DMM to JED Transport', 'Transportation') THEN pid.cntr_vol * lcbd.value
                WHEN lcbd.expense_type = 'Shipment-wise' THEN lcbd.value
                ELSE 0
            END) + MAX(prd.freight) * 3.76) * 1.03, 2) AS cost
        FROM landed_cost_breakdown lcbd
        INNER JOIN purchase_receipt_detail prd ON lcbd.item_group = prd.item_group
        """,
        {"purchase_receipt": purchase_receipt},
        as_dict=True,
    )
    row = result[0] if result else {}
    return flt(row.get("cost")), row.get("expense_account")


@frappe.whitelist()
def create_estimated_landed_cost_voucher(purchase_receipt):
    """Create a draft Landed Cost Voucher with the estimated landed cost of a Purchase Receipt."""
    pr = frappe.get_doc("Purchase Receipt", purchase_receipt)
    if pr.docstatus != 1 or pr.is_return:
        frappe.throw(_("Purchase Receipt {0} must be submitted and not a return").format(purchase_receipt))

    amount, expense_account = get_estimated_landed_cost(purchase_receipt)
    if not amount:
        frappe.throw(
            _(
                "No estimated landed cost found for this receipt. Check the item group's Estimated Landed Cost and the linked Purchase Invoice."
            )
        )
    if not expense_account:
        frappe.throw(_("Estimated Landed Cost Account is not set for this item group's Estimated Landed Cost."))

    lcv = frappe.new_doc("Landed Cost Voucher")
    lcv.company = pr.company
    lcv.posting_date = frappe.utils.today()
    if frappe.get_meta("Landed Cost Voucher").has_field("shipment"):
        lcv.shipment = pr.title
    lcv.append(
        "purchase_receipts",
        {
            "receipt_document_type": "Purchase Receipt",
            "receipt_document": pr.name,
            "supplier": pr.supplier,
            "posting_date": pr.posting_date,
            "grand_total": pr.base_grand_total,
        },
    )
    lcv.get_items_from_purchase_receipts()
    # the cost is in company currency, so the exchange rate is 1
    lcv.append(
        "taxes",
        {
            "expense_account": expense_account,
            "description": ESTIMATED_LCV_DESCRIPTION,
            "amount": amount,
            "exchange_rate": 1,
            "base_amount": amount,
        },
    )
    lcv.insert()
    return lcv.name
