import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

class Migration():
    def __init__(self):
        self.create_custom_fields()
        frappe.db.commit()

    def create_custom_fields(self):
        print("Executing before_migrate.py for ksa_customizations")

        if not frappe.db.exists(
            "Custom Field",
            {"dt": "Contact", "fieldname": "is_sales_person"}
        ):
            create_custom_field(
                "Contact",
                {
                    "label": "Is Sales Person",
                    "fieldname": "is_sales_person",
                    "fieldtype": "Check",
                    "insert_after": "sync_with_google_contacts"
                }
            )
            print("Custom Field 'is_sales_person' created in Contact")
        else:
            print("Custom Field 'is_sales_person' already exists in Contact")

        # Sales Person
        if not frappe.db.exists(
            "Custom Field",
            {"dt": "Contact", "fieldname": "sales_person"}
        ):
            create_custom_field(
                "Contact",
                {
                    "label": "Sales Person",
                    "fieldname": "sales_person",
                    "fieldtype": "Link",
                    "options": "Sales Person",
                    "insert_after": "is_sales_person",
                    "depends_on": "eval:doc.is_sales_person",
                    "mandatory_depends_on": "eval:doc.is_sales_person"
                }
            )
            print("Custom Field 'sales_person' created in Contact")
        else:
            print("Custom Field 'sales_person' already exists in Contact")