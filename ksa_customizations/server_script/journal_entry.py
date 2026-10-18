import frappe
from frappe import _


def validate(doc, method=None):
    validate_landed_cost_entry(doc)


def validate_landed_cost_entry(doc):
    """Landed Cost Entry lines must reference a Purchase Receipt; Asset lines (other than Bank / Cash) also need a landed cost category."""
    if doc.voucher_type != "Landed Cost Entry":
        return

    for row in doc.accounts:
        if row.reference_type != "Purchase Receipt" or not row.reference_name:
            frappe.throw(
                _("Row #{0}: Reference Type must be Purchase Receipt and Reference Name is mandatory for a Landed Cost Entry").format(row.idx)
            )

        if row.get("landed_cost_category"):
            continue

        root_type, account_type = frappe.get_cached_value("Account", row.account, ["root_type", "account_type"])
        if root_type == "Asset" and account_type not in ("Bank", "Cash"):
            frappe.throw(
                _("Row #{0}: Landed Cost Category is mandatory for Asset account {1}").format(row.idx, frappe.bold(row.account))
            )
