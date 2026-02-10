import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Account": [
            {
                "fieldname": "custom_assigned_person",
                "label": "Assigned Person",
                "fieldtype": "Link",
                "insert_after": "account_currency",
                "options": "User"   
            }
        ],
        "Payment Entry": [
            {
                "fieldname": "custom_payment_transfer_request",
                "label": "Payment Transfer Request",
                "fieldtype": "Link",
                "insert_after": "reference_no",
                "options": "Payment Transfer Request",
                "read_only": 1
            }
        ]
    }
    for doctype, fields in custom_fields.items():
        for field in fields:
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
                print(f"[PATCH] {doctype}.{field['fieldname']} already exists – skipping")
            else:
                create_custom_fields({doctype: [field]})
                print(f"[PATCH] {doctype}.{field['fieldname']} created")

    print("[PATCH] Custom fields for Payment Transfer Request added")
