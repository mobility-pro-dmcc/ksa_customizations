import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Employee": [
            {
                "fieldname": "goal_template",
                "label": "Goal Template",
                "fieldtype": "Link",
                "options": "Goal Template",
                "insert_after": "grade"
            }
        ],
    }

    create_custom_fields(custom_fields, ignore_validate=True)