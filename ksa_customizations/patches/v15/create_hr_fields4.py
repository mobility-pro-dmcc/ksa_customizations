import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Goal": [
            {
                "fieldname": "actual_target_amount",
                "label": "Actual Target Amount",
                "fieldtype": "Float",
                "insert_after": "employee",
                "in_list_view": 1
            },
            {
                "fieldname": "expected_target_amount",
                "label": "Expected Target Amount",
                "fieldtype": "Float",
                "insert_after": "actual_target_amount",
                "read_only": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "is_excel_uploaded",
                "label": "Is Excel Uploaded",
                "fieldtype": "Check",
                "read_only": 1
            },
            {
                "fieldname": "goal_name_ar",
                "label": "Goal Name in Arabic",
                "fieldtype": "Data",
                "insert_after": "goal_name"
            }
        ],
        "KRA": [
            {
                "fieldname": "kra_name_ar",
                "label": "KRA Name in Arabic",
                "fieldtype": "Data",
                "reqd": 1,
            }
        ],
        "HR Settings": [
            {
                "fieldtype": "Section Break",
                "fieldname": "appraisal_cycle_section",
                "label": "Appraisal Cycle Settings",
                "insert_after": "unlink_payment_on_cancellation_of_employee_advance"
            },
            {
                "fieldname": "appraisal_cycle_duration",
                "label": "Appraisal Cycle Duration (in days)",
                "fieldtype": "Int",
                "default": 90,
                "insert_after": "appraisal_cycle_section"
            },
            {
                "fieldname": "appraisal_cycle_creation_dates",
                "label": "Appraisal Cycle Creation Dates",
                "fieldtype": "Table",
                "options": "Appraisal Cycle Creation Dates",
                "insert_after": "appraisal_cycle_duration",
            }   
        ]
    }
    create_custom_fields(custom_fields, ignore_validate=True)