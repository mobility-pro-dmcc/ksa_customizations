import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    doctype = "Sales Order"
    fieldname = "custom_per_billed"

    if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
        print(f"[PATCH] {doctype}.{fieldname} already exists – skipping")
        return

    custom_fields = {
        doctype: [
            {
                "fieldname": fieldname,
                "label": "% Qty Billed",
                "fieldtype": "Float",
                "insert_after": "per_billed",
                "read_only": 1,
                "precision": 2
            }
        ]
    }

    create_custom_fields(custom_fields)
    print(f"[PATCH] {doctype}.{fieldname} created")
