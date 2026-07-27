import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Employee": [
            {
                "fieldname": "reports_to_email",
                "label": "Direct Manager Email",
                "fieldtype": "Data",
                "insert_after": "reports_to",
                "fetch_from": "reports_to.user_id"
            }
        ],
        "Appraisal": [
            {
                "fieldname": "employee_email",
                "label": "Employee Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.user_id"
            },
            {
                "fieldname": "direct_manager_email",
                "label": "Direct Manager Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.reports_to_email"
            },
            {
                "fieldname": "functional_manager_email",
                "label": "Functional Manager Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.custom_functional_manager"
            },
            {
                "fieldname": "start_date",
                "label": "Start Date",
                "fieldtype": "Date",
                "insert_after": "appraisal_cycle",
                "fetch_from": "appraisal_cycle.start_date"
            },
            {
                "fieldname": "end_date",
                "label": "End Date",
                "fieldtype": "Date",
                "insert_after": "appraisal_cycle",
                "fetch_from": "appraisal_cycle.end_date"
            }
        ],
        "Goal": [
            {
                "fieldname": "employee_email",
                "label": "Employee Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.user_id"
            }
        ]
    }

    if not frappe.db.exists("Role", "COO"):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": "COO"
        }).insert(ignore_permissions=True)
        print("Role COO created successfully.")
        # frappe.db.commit()

    create_custom_fields(custom_fields, ignore_validate=True)