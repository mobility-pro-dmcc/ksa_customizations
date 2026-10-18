import base64, io, json, re

import anthropic
import frappe
import pypdfium2 as pdfium
from frappe import _

MAX_PAGES = 8                                  # pages sent per PDF

# ── Accounts ────────────────────────────────────────────────────────────────
# The account list comes from the "Landed Cost Expense Category" doctype (loaded in execute()).
# ACCOUNTS = {expense_category_en: row}; row has expense_category_en/ar, expense_account, include_in_lcv
# and keywords (backup: words in the description -> account, used only if Claude's choice is not in the list).
ACCOUNTS = {}
VAT_ACCOUNT = "VAT"                            # expense_category_en or keyword of the VAT row

# ── Fields to extract ───────────────────────────────────────────────────────
# How to find the بوليصة — used in the main prompt and in the second search.
BL_HINTS = """Search EVERY line of EVERY page, including titles, notes (ملاحظات / NOTS), descriptions and
reference boxes, for any of these words, then take the code written next to it:
    بوليصة / بوليصه / البوليصة / البوليصه / رقم البوليصة / رقم البوليصه / بوليصة رقم / بوليصه رقم /
    بوليصة الشحن / رقم بوليصة الشحن / ب/ش / B/L / BL / B/L No / BL No / Bill of Lading / Bill Number /
    MBL / HBL / OBL.
  Examples: "فاتورة 10864 لنا المستقبل بوليصه رقم SZX601041200 عدد الحاويات (1)" -> SZX601041200;
            "ملاحظات: فاتورة 11034 ... بوليصة رقم TASU60409400" -> TASU60409400;
            "رقم البوليصة: PUSG00733804" -> PUSG00733804.
  Some suppliers put it in PO No / رقم امرالشراء / Reference / المرجع with no بوليصة label (e.g. HLCUSEL251203412).
  On a customs declaration (بيان جمركي) it is in the box "رقم البوليصة/المانفست | B/L-AWB NO. / MANIF": take the
  value after "B" (e.g. "M 1841  B QAF557645JEH" -> QAF557645JEH); the "M" value is the manifest.
  A بوليصة number is usually 8-16 letters and digits. It is NOT: a container number (4 letters + 7 digits,
  e.g. FCIU8969453), the invoice number, a SADAD number, a VAT number, a declaration (بيان) number or a
  manifest (مانفست) number.
  If part of it is hidden or cut off, return only what you can read. Never invent it"""

# How to find the customer COMPANY name — used in the main prompt and in the second search.
BILL_NAME_HINTS = """It must be a COMPANY / establishment name, never a person's name.
  Where to look on the main document: the customer box (العميل / اسم العميل / Customer Name / Buyer / المشتري /
  Bill To / Invoice To / فاتورة الى / الى السادة / To Invited / المستفيد / Consignee).
  A company name usually starts with شركة / مؤسسة / مصنع / مكتب / مجموعة, or ends with للتجارة / التجارية /
  LLC / Ltd / Co. / Company / Est. / Trading / Group.
  - If Arabic and English are both printed, return the Arabic company name as printed
    (e.g. "شركة لنا المستقبل للتجارة", not "Lana Mustaqbal").
  - If a person's name is attached to the company (after "/", "-", "Attn", "c/o", contact person),
    drop the person and keep only the company: "LANA ALMOSTAQBAL FOR TRADING LLC/ياسين يوسف" ->
    "LANA ALMOSTAQBAL FOR TRADING LLC".
  - If the customer box shows only a person, look for the customer company elsewhere on the main document
    (a title line such as "فاتورة 10864 لنا المستقبل ..." or notes), then on the attachments ONLY in the
    importer / consignee / owner of goods field (المستورد / صاحب البضاعة / Consignee / Importer).
    Never use the clearing agent (المخلص), shipping line, port, Fasah or Mawani as the customer.
  - Never return a phone, address, branch (الفرع), department or VAT number.
  - It is never the seller (the company that issued the document).
  If no company name is printed, return "". Never invent it"""

# How to find the customer VAT number — used in the main prompt and in the second search.
BILL_TRN_HINTS = """Take it ONLY from the customer section of the main document (next to the customer name:
  العميل / Customer / Buyer / Bill To / الى السادة / To Invited).
  It is the number labeled with any of:
    VAT NO / VAT No. / VAT Number / Customer VAT NO / VAT Registration Number / VAT Reg. No / TRN / Tax No /
    الرقم الضريبي / رقم الضريبي / الرمز الضريبي / رمز الضريبي / رقم التسجيل الضريبي / الرقم الضريبي للعميل /
    رقم ضريبة القيمة المضافة.
  A Saudi VAT number is 15 digits, starting with 3 and ending with 3 (e.g. 310998667300003).
  It is NOT: the seller's VAT number (in the seller header / Seller / Sell From box), the commercial register
  (السجل التجاري / CR, 10 digits), a 10-digit TIN, a phone number, an IBAN or an invoice number.
  Copy the digits exactly as printed, even if they look different from other documents.
  If the customer section has no VAT number, return "". Never invent it"""

# Column name : what Claude should look for.
FIELDS = {
    "account": "the company that ISSUED the document (seller / supplier / المورد / البائع / Sell From / "
               "the company in the letterhead), in Arabic if printed in Arabic",
    "invoice_no": "the number of the MAIN document (Invoice No / رقم الفاتورة / Credit Note No / رقم الإشعار), "
                  "exactly as printed. Not the بوليصة, VAT, customer, PO or reference number",
    "invoice_date": "the issue date of the document (not the due date), as YYYY-MM-DD. Saudi documents print "
                    "the DAY first (04/05/2026 = 2026-05-04). If Hijri and Gregorian are both printed, use Gregorian",
    "sell_trn": "the SELLER's VAT number: the VAT number printed next to the SELLER's name (letterhead, "
                "Seller / Sell From / المورد box). If the only VAT number on the page is in the CUSTOMER section "
                "(next to the customer name, e.g. under 'To Invited / الى السادة'), it is NOT the seller's: "
                "return \"\" for sell_trn",
    "bill_of_lading": "the بوليصة (bill of lading) number. " + BL_HINTS,
    "bill_name": "the name of the CUSTOMER company the document is billed to. " + BILL_NAME_HINTS,
    "bill_TRN": "the CUSTOMER's VAT number. " + BILL_TRN_HINTS,
}

# Fields that may be taken from attachment pages when they are not on the main document.
SEARCH_ATTACHMENTS = ["bill_of_lading", "bill_name"]

# Fields kept as text (IDs).
TEXT_FIELDS = ["sell_trn", "bill_of_lading", "bill_TRN"]


def load_accounts():
    """{expense_category_en: row} from the Landed Cost Expense Category doctype.
    row.keywords = the category names + the Keywords field (one per line)."""
    rows = frappe.db.sql("""
        select category_en as expense_category_en, category as expense_category_ar, expense_account,
               include_in_landed_cost_voucher as include_in_lcv, keywords
        from `tabLanded Cost Expense Category`
    """, as_dict=True)
    for r in rows:
        words = [r.expense_category_ar, r.expense_category_en, *(r.keywords or "").splitlines()]
        r.keywords = list(dict.fromkeys(w.strip() for w in words if w and w.strip()))
    return {r.expense_category_en.strip(): r for r in rows if r.expense_category_en}


def vat_row():
    """The VAT category: VAT_ACCOUNT as its English name or one of its keywords. None if missing."""
    return next((r for r in ACCOUNTS.values()
                 if normalize(VAT_ACCOUNT) in map(normalize, r.keywords)), None)


def load_known_trn():
    """{normalized company name: tax_id} from Company (English name and company_name_in_arabic).
    Used only to fill an EMPTY sell_trn / bill_TRN."""
    fields = ["company_name", "tax_id"]
    if frappe.get_meta("Company").has_field("company_name_in_arabic"):
        fields.append("company_name_in_arabic")
    known = {}
    for c in frappe.get_all("Company", filters={"tax_id": ["is", "set"]}, fields=fields):
        for name in (c.get("company_name_in_arabic"), c.company_name):
            if normalize(name):
                known[normalize(name)] = c.tax_id.strip()
    return known


def build_prompt():
    field_lines = "\n".join(f"- {name}: {desc}." for name, desc in FIELDS.items())
    schema = {**{name: "" for name in FIELDS},
              "vat_numbers": [{"number": "", "company": "", "side": "seller or customer"}],
              "items": [{"description": "", "value": 0, "vat_rate": 0, "line_account": ""}],
              "vat": 0, "vat_percent": 0, "taxable_amount": 0, "total_after_vat": 0}
    attach = ", ".join(SEARCH_ATTACHMENTS) or "none"
    account_lines = "\n".join(f"    {en}  ({r.expense_category_ar or ''})  keywords: {', '.join(r.keywords)}"
                              for en, r in ACCOUNTS.items() if r is not vat_row())
    return f"""
    read only first invoice  
    You will see the pages of ONE PDF. Layouts, languages (Arabic / English) and suppliers vary.

1. Find the MAIN document: the invoice, tax invoice, credit note or debit note that the PDF is about
   (usually page 1). Any other pages are attachments (customs declarations, port or government invoices,
   shipping-line invoices, receipts, etc.).
2. Take every value from the MAIN document only. Exception — these fields may be taken from an attachment
   if the main document does not show them: {attach}.
   NEVER take items or VAT from an attachment.

Fields:
{field_lines}

VAT numbers — do this BEFORE filling sell_trn and bill_TRN:
- List EVERY VAT number (15 digits, starts and ends with 3) printed on the main document in "vat_numbers".
- For each one, write the company name printed in the SAME box / next to it, and its side:
  "seller" (the company that issued the document) or "customer" (the company it is addressed to).
- A VAT number belongs to the company it is printed next to — never to the other party.
  Example: credit note with "الى السادة: شركة لنا المستقبل للتجارة" and right under it
  "VAT NO / الرمز الضريبي 310998667300003", and no VAT number in the seller header ->
  vat_numbers = [{{"number": "310998667300003", "company": "شركة لنا المستقبل للتجارة", "side": "customer"}}],
  bill_TRN = "310998667300003", sell_trn = "".
- Then sell_trn = the seller's number and bill_TRN = the customer's number from this list.

Items: every line of the main document's table.
- The table's HEADER row (اسم المادة / البيان / الوصف / الصنف / الكمية / السعر / الإجمالي / Description / Item /
  Qty / Price / Total / Amount) is NEVER a line. Never use a header word as a description.
- Scanned tables are often misaligned: a description can look higher or lower than its numbers, and the first
  amount can look like it sits on the header row. Pair descriptions and amounts IN ORDER, top to bottom:
  the 1st description with the 1st amount, the 2nd with the 2nd, and so on. Every description row — including
  the LAST one — gets an amount.
  Example (misaligned scan): header "اسم المادة | الكمية | السعر | الاجمالي" with 1,100.00 printed on its right,
  then descriptions اجور الموانئ, اجور التفريغ, اجور النقل, اجور التخليص, حجز موعد and amounts
  1,100.00, 631.75, 700.00, 200.00, 30.00 ->
  اجور الموانئ=1100, اجور التفريغ=631.75, اجور النقل=700, اجور التخليص=200, حجز موعد=30.
  Check: the sum of the line values must equal the printed total before VAT.
- description: as printed (keep Arabic, keep numbers that are part of the text).
- value: the line amount BEFORE VAT. If not printed, use quantity × unit price.
  Pass-through lines that show 0.00 in a taxable column but have a price: use quantity × price.
- vat_rate: the VAT percentage of the line as a number (15 for 15%), from the line's VAT % / نسبة الضريبة /
  معدل الضريبة column. If there is no per-line rate but the document shows one rate for everything
  (e.g. "ضريبة القيمة المضافة 15%" / "Total VAT 15%"), use that rate for every taxable line.
  Use 0 for lines marked 0%, exempt, or pass-through lines with no VAT.
- line_account: the expense account this line belongs to, chosen from this list ONLY (return the English name exactly):
{account_lines}
  Decide by the MEANING of the description (Arabic or English), for example:
    "اجور التخليص" / "خدمة تخلص حاوية" / "REVENUE - CLEARANCE" -> Customs Clearance
    "اجور الموانئ" / "سداد اجور موانئ" / "PORT FEES" / "اجور التفريغ" / "رسوم مناولة بوابة" -> Port Charges
    "اجور النقل" / "Transportation Charges" / "نقل كونتينرات الميناء" -> Cargo Transportation
    "اجور اذن التسليم" / "رسوم اذن التسليم" -> Delivery Order
    "اجور ارضيات" (port storage days) -> Port Demurrage
    "DEMURRAGE CHARGES" / "تمديد" / "غرامات تأخير الحاويات" (shipping line) -> Shipping Line Demurrage
    "INSPECTION CHARGE" / "اجرة المعاينة" / "SCAN UPON CHECK" -> Inspection Fees
    "LOCAL SHIPPING LINE CHARGES" / "CONTAINER SERVICE CHARGE" / "DOCUMENTATION SERVICES" -> Shipping Line Fees
    "اجور تخزين" / "Storage" -> Storage Fees
    "حجز موعد" / "رسوم حجز موعد كونتينرات" -> Appointment Booking
    "الرسوم الجمركية" / "Customs Duty" -> Customs Duties
    "شهادة مطابقة" / "SABER" / "COC" -> COC
  If no account fits, return "".
- Sub-lines (references, notes, "فاتورة سداد رقم ...") are not separate lines.

VAT (from the main document only):
- vat: the total VAT AMOUNT exactly as printed (إجمالي الضريبة / اجمالي ضريبة / Total VAT / ضريبة القيمة المضافة /
  مبلغ الضريبة / VAT). If no amount is printed, or it is printed as 0.00, return 0. Do not calculate it.
- vat_percent: the VAT PERCENTAGE printed anywhere on the main document, as a number (15 for "15%" or "15.00").
  Look in: a VAT % / نسبة الضريبة / معدل الضريبة / ضريبة القيمة المضافة % column, a totals label such as
  "ضريبة القيمة المضافة 15%" / "Total VAT 15%" / "VAT 15%", or a note. ALWAYS return it when it is printed,
  even if the VAT amount is missing or 0.00. Return 0 only if no percentage is printed anywhere.
- taxable_amount: the total BEFORE VAT as printed (المجموع قبل الضريبة / الإجمالي قبل الضريبة / المبلغ الخاضع
  للضريبة / Total / Total Before VAT / Value Excluding VAT / Taxable Amount). 0 if not printed.
- total_after_vat: the total AFTER VAT as printed (المجموع بعد الضريبة / الإجمالي بعد الضريبة / المجموع الصافي /
  Last Total / Total Including VAT / Value Including VAT / Amount Due). 0 if not printed.
  Example (credit note): Total 1500.00, VAT 0.00, "ضريبة القيمة المضافة 15%", نسبة الضريبة 15.00, Last Total 1,725.00 ->
  vat = 0, vat_percent = 15, taxable_amount = 1500, total_after_vat = 1725, and the line's vat_rate = 15.

Rules:
- Seller and customer are different parties: never put the same name or VAT number in both.
- Numbers: positive, plain, no thousands separators or currency ("1 875.000" -> 1875, "2,567.50" -> 2567.5).
- IDs (VAT numbers, B/L, references): text in quotes, uppercase, no spaces, dashes or slashes.
  If an ID is printed reversed (digits first, letters last), put the letters first.
- If a field is not printed anywhere it is allowed, return "". Do not guess.

Return raw JSON only, exactly in this shape:
{json.dumps(schema, ensure_ascii=False)}

- value: the line amount BEFORE VAT — the taxable / before-VAT column (المبلغ الخاضع للضريبة / المبلغ قبل الضريبة /
  القيمة / Taxable Amount / Total Excl. VAT / Line Total). NEVER the after-VAT column (المبلغ بعد الضريبة /
  الإجمالي شامل الضريبة / Total Incl. VAT / Price After VAT) and never the VAT column (الضريبة / VAT Amount).
  Example: columns "السعر 220.00 | الكمية 4.00 | المبلغ الخاضع للضريبة 880.00 | الضريبة 132.00 15% |
  المبلغ بعد الضريبة 1,012.00" -> value = 880, vat_rate = 15 (not 1012).
  If not printed, use quantity × unit price.
"""


# Table header words: a line with one of these as its description was read wrongly.
HEADER_WORDS = {"اسم المادة", "المادة", "البيان", "الوصف", "الصنف", "اسم الصنف", "وصف الصنف", "الكمية", "السعر",
                "الاجمالي", "الإجمالي", "المبلغ", "description", "item", "items", "item name", "qty", "quantity",
                "price", "unit price", "total", "amount"}


def has_header_row(items):
    return any(as_text(i.get("description")).strip().lower() in HEADER_WORDS for i in items)


TABLE_RETRY_NOTE = """
IMPORTANT — your previous answer used the table's column header (e.g. "اسم المادة") as a line.
Read the table again: skip the header row, then pair descriptions and amounts in order, top to bottom,
so that EVERY description (including the last one) gets its amount. The sum must equal the total before VAT.
"""


def is_vat_number(value):
    return bool(re.fullmatch(r"3\d{13}3", value))


def looks_like_company(name):
    return bool(re.search(r"شركة|مؤسسة|مصنع|مكتب|مجموعة|للتجارة|التجارية|\b(LLC|LTD|CO|COMPANY|EST|TRADING|GROUP|CORP|INC)\b",
                          name, re.IGNORECASE))


# Second search: field -> (what to look for, check that the value is right; if not, search again)
SECOND_SEARCH = {
    "bill_of_lading": ("the بوليصة (bill of lading) number. " + BL_HINTS,
                       lambda v, info: bool(v)),
    "bill_name": ("the name of the CUSTOMER company the document is billed to. " + BILL_NAME_HINTS,
                  lambda v, info: looks_like_company(v) and v != info["account"]),
    "bill_TRN": ("the CUSTOMER's VAT number. " + BILL_TRN_HINTS,
                 lambda v, info: is_vat_number(v) and v != info["sell_trn"]),
    "sell_trn": ("the SELLER's VAT number: 15 digits starting and ending with 3, printed in the seller's "
                 "letterhead / header (often after 'الرقم الضريبي' / 'VAT No' near the seller's name and address) "
                 "or in the Seller / Sell From box. It is NOT the customer's VAT number. Return \"\" if not printed",
                 lambda v, info: is_vat_number(v) and v != info["bill_TRN"]),
}


def second_search_prompt(field, hints, info):
    return f"""These pages are ONE PDF. Page 1 is usually the main invoice / credit note; other pages are attachments.
Already known: seller = "{info['account']}", customer = "{info['bill_name']}".
Find only this: {field} = {hints}

Return raw JSON only: {{{json.dumps(field)}: ""}}  (use "" if it is not printed anywhere)
"""


def pdf_pages(path):
    pdf = pdfium.PdfDocument(str(path))
    content = []
    for i in range(min(len(pdf), MAX_PAGES)):
        for scale in (2, 1.5, 1):                       # API limit is 5 MB per image
            buf = io.BytesIO()
            pdf[i].render(scale=scale).to_pil().convert("RGB").save(buf, format="JPEG", quality=85)
            data = base64.b64encode(buf.getvalue()).decode()
            if len(data) < 4_500_000:
                break
        content.append({"type": "text", "text": f"Page {i + 1}:"})
        content.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}})
    pdf.close()
    return content


def ask(pages, prompt):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system="Reply with the JSON object only. No explanation, no markdown.",
        messages=[{"role": "user", "content": [*pages, {"type": "text", "text": prompt}]}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    return json.loads(re.search(r"\{[\s\S]*\}", text).group(0))


def as_text(value):
    """Keep IDs as text."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return "" if value is None else str(value).strip()


ARABIC_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه"})


def normalize(value):
    """For matching names / keywords: lower case, أ/إ/آ -> ا, ة -> ه."""
    return as_text(value).lower().translate(ARABIC_LETTERS)


def num(value):
    """'15%' -> 15.0, '1,725.00' -> 1725.0, '' -> 0.0"""
    try:
        return float(re.sub(r"[^\d.\-]", "", str(value)) or 0)
    except ValueError:
        return 0.0


def clean_id(value):
    parts = []
    for part in as_text(value).split(","):
        part = re.sub(r"[\s\-/\\.]", "", part.upper())
        m = re.fullmatch(r"(\d+)([A-Z]{2,})", part)  # printed reversed: digits first
        parts.append(m.group(2) + m.group(1) if m else part)
    return ", ".join(p for p in parts if p)


def clean_bl(value):
    """Like clean_id, but drops container numbers (ABCU1234567) that are not a بوليصة."""
    return ", ".join(p for p in clean_id(value).split(", ") if p and not re.fullmatch(r"[A-Z]{3}U\d{7}", p))


def percent(value):
    """15, '15%', '15.00' -> 15.0 ; 0.15 -> 15.0"""
    p = num(value)
    return p * 100 if 0 < p < 1 else p


def get_vat(data, items):
    """Printed VAT amount; if there is none, calculate it from the VAT percentage."""
    vat = num(data.get("vat"))
    if vat:
        return vat, "printed"

    # 1. each line × its own VAT %
    vat = round(sum(num(i.get("value")) * percent(i.get("vat_rate")) / 100 for i in items), 2)
    if vat:
        return vat, "line VAT %"

    # 2. total before VAT × the document's VAT %
    rate = percent(data.get("vat_percent"))
    base = num(data.get("taxable_amount")) or sum(num(i.get("value")) for i in items)
    if rate and base:
        return round(base * rate / 100, 2), f"{base:,.2f} × {rate:g}%"

    # 3. total after VAT − total before VAT
    after = num(data.get("total_after_vat"))
    if after and base and after > base:
        return round(after - base, 2), f"{after:,.2f} − {base:,.2f}"

    return 0.0, "no VAT"


def account_for(item):
    """The Landed Cost Expense Category row for this line: Claude's choice, else the keywords.
    None if no match."""
    choice = normalize(item.get("line_account"))
    for en, row in ACCOUNTS.items():
        if choice and choice in (normalize(en), normalize(row.expense_category_ar)):
            return row
    text = normalize(item.get("description"))
    best, best_len = None, 0
    for row in ACCOUNTS.values():
        for w in row.keywords:
            # English words must start a word ("port" matches "Port Fees", not "Import"); Arabic: anywhere
            hit = re.search(r"\b" + re.escape(normalize(w)), text) if w.isascii() else normalize(w) in text
            if hit and len(w) > best_len:            # longest (most specific) keyword wins
                best, best_len = row, len(w)
    return best


def account_columns(row):
    """The account columns added to each result row."""
    row = row or {}
    return {"account_ar": row.get("expense_category_ar") or "", "account_en": row.get("expense_category_en") or "",
            "expense_account": row.get("expense_account") or "", "include_in_lcv": row.get("include_in_lcv") or 0}


def assign_vat_numbers(info, vat_numbers):
    """Put each VAT number on the side (seller / customer) of the company it is printed next to."""
    seller, customer = [], []
    for v in vat_numbers or []:
        number = clean_id(v.get("number"))
        if not is_vat_number(number):
            continue
        side, company = as_text(v.get("side")).lower(), as_text(v.get("company"))
        if "customer" in side or (company and company == info["bill_name"]):
            customer.append(number)
        elif "seller" in side or (company and company == info["account"]):
            seller.append(number)
    if customer and not is_vat_number(info["bill_TRN"]) or info["bill_TRN"] in seller:
        info["bill_TRN"] = customer[0] if customer else ""
    if info["sell_trn"] in customer:                     # customer's number put in the seller column
        info["sell_trn"] = seller[0] if seller else ""
    if seller and not is_vat_number(info["sell_trn"]):
        info["sell_trn"] = seller[0]
    if info["sell_trn"] and info["sell_trn"] == info["bill_TRN"]:   # same number on both sides: keep it as the customer's
        info["sell_trn"] = ""


TOTAL_STEPS = 7


def progress(step, message):
    """Show the user the current step of execute().

    The step is stored in the cache (polled by the browser through api.get_upload_progress) and also
    published over realtime.
    """
    percent = step * 100 / TOTAL_STEPS
    progress_id = frappe.flags.get("landed_cost_progress_id")
    if progress_id:
        frappe.cache.set_value(f"landed_cost_progress:{progress_id}", {"percent": percent, "message": message},
                               expires_in_sec=600)
    frappe.publish_progress(percent, title=_("Reading PDF"), description=message)


def execute(pdf_file):
    """Read one PDF and return a list of rows (one per line + one VAT row)."""
    global client, MODEL, ACCOUNTS
    progress(0, _("Step 1/7: Loading AI settings and account mapping"))
    keys = frappe.get_single("KSA Customization Settings").get_ai_info()
    MODEL = keys["model"]
    client = anthropic.Anthropic(api_key=keys["api_key"], max_retries=5,
                                 default_headers={"Accept-Encoding": "gzip, deflate"})
    ACCOUNTS = load_accounts()
    if not ACCOUNTS:
        frappe.throw(_("Landed Cost Mapping is empty"))
    prompt = build_prompt()                          # built with the accounts from Landed Cost Mapping

    try:
        progress(1, _("Step 2/7: Converting PDF pages to images"))
        pages = pdf_pages(pdf_file)
        progress(2, _("Step 3/7: Extracting invoice data with AI"))
        data = ask(pages, prompt)
        if has_header_row(data.get("items", [])):          # header read as a line -> read the table again
            print("   table header read as a line -> reading the table again")
            retry = ask(pages, prompt + TABLE_RETRY_NOTE)
            if retry.get("items") and not has_header_row(retry["items"]):
                data["items"] = retry["items"]
    except Exception as e:
        frappe.throw(f"Could not read the PDF: {e}")

    progress(3, _("Step 4/7: Cleaning extracted fields and VAT numbers"))
    info = {name: clean_id(data.get(name)) if name in TEXT_FIELDS else as_text(data.get(name))
            for name in FIELDS}
    info["bill_of_lading"] = clean_bl(info["bill_of_lading"])
    assign_vat_numbers(info, data.get("vat_numbers"))

    progress(4, _("Step 5/7: Checking missing or doubtful fields (second search)"))
    # Second search: ask again, only for that field, if it is missing or doesn't look right
    for field, (hints, ok) in SECOND_SEARCH.items():
        if ok(info[field], info):
            continue
        try:
            value = as_text(ask(pages, second_search_prompt(field, hints, info)).get(field))
            if field in TEXT_FIELDS:
                value = clean_bl(value) if field == "bill_of_lading" else clean_id(value)
            if ok(value, info) or not info[field]:
                info[field] = value
        except Exception as e:
            print(f"   {field} search error:", e)
        print(f"   {field} (2nd search): {info[field] or 'not found'}")

    progress(5, _("Step 6/7: Filling known VAT numbers and calculating VAT"))
    # Fill an empty VAT number from the Company's tax_id
    known_trn = load_known_trn()
    for name_col, trn_col in (("account", "sell_trn"), ("bill_name", "bill_TRN")):
        if not info[trn_col] and normalize(info[name_col]) in known_trn:
            info[trn_col] = known_trn[normalize(info[name_col])]

    items = data.get("items", [])
    vat, how = get_vat(data, items)                  # printed VAT, or calculated from the VAT %
    if how not in ("printed", "no VAT"):
        print(f"   VAT not printed -> calculated {vat:,.2f} ({how})")

    progress(6, _("Step 7/7: Mapping lines to accounts"))
    rows = []
    for i in items:
        mapping_row = account_for(i)
        if not mapping_row:
            print(f"   ⚠ no account for line: {i.get('description')}")
        rows.append({**info, "description": i.get("description", ""), **account_columns(mapping_row),
                     "value": num(i.get("value"))})
    if vat:
        rows.append({**info, "description": "الضريبة", **account_columns(vat_row()),
                     "value": vat})
    progress(7, _("Done"))
    return rows