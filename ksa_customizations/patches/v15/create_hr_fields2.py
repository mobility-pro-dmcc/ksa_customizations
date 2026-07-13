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
            },
            {
                "fieldname": "custom_functional_manager",
                "label": "Functional Manager",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "reports_to"
            }
        ],
    }

    create_custom_fields(custom_fields, ignore_validate=True)