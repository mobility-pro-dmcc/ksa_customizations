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
                "insert_after": "grade",
            },
            {
                "fieldname": "custom_functional_manager",
                "label": "Functional Manager",
                "fieldtype": "Link",
                "options": "User",
                "insert_after": "reports_to",
            },
            {
                "fieldname": "reports_to_email",
                "label": "Direct Manager Email",
                "fieldtype": "Data",
                "insert_after": "reports_to",
                "fetch_from": "reports_to.user_id",
            },
            {
                "fieldname": "follows_kpis",
                "label": "Follows KPIs",
                "fieldtype": "Check",
                "insert_after": "employee_name",
            },
            {
                "fieldname": "employee_name_ar",
                "label": "Full Name in Arabic",
                "fieldtype": "Data",
                "insert_after": "employee_name",
            },
        ],
        "Appraisal": [
            {
                "fieldname": "fill_from_goal_template",
                "label": "Fill from Goal Template",
                "fieldtype": "Check",
                "insert_after": "rate_goals_manually",
                "default": "1",
            },
            {
                "fieldname": "employee_email",
                "label": "Employee Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.user_id",
            },
            {
                "fieldname": "direct_manager_email",
                "label": "Direct Manager Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.reports_to_email",
            },
            {
                "fieldname": "functional_manager_email",
                "label": "Functional Manager Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.custom_functional_manager",
            },
            {
                "fieldname": "start_date",
                "label": "Start Date",
                "fieldtype": "Date",
                "insert_after": "appraisal_cycle",
                "fetch_from": "appraisal_cycle.start_date",
            },
            {
                "fieldname": "end_date",
                "label": "End Date",
                "fieldtype": "Date",
                "insert_after": "appraisal_cycle",
                "fetch_from": "appraisal_cycle.end_date",
            },
        ],
        "Designation": [
            {
                "fieldname": "goal_template",
                "label": "Goal Template",
                "fieldtype": "Link",
                "options": "Goal Template",
                "insert_after": "appraisal_template",
            }
        ],
        "Appraisee": [
            {
                "fieldname": "goal_template",
                "label": "Goal Template",
                "fieldtype": "Link",
                "options": "Goal Template",
                "insert_after": "designation",
                "in_list_view": 1,
            }
        ],
        "Goal": [
            {
                "fieldname": "employee_email",
                "label": "Employee Email",
                "fieldtype": "Data",
                "insert_after": "employee",
                "fetch_from": "employee.user_id",
            },
            {
                "fieldname": "actual_target_amount",
                "label": "Actual Target Amount",
                "fieldtype": "Float",
                "insert_after": "employee",
                "in_list_view": 1,
            },
            {
                "fieldname": "expected_target_amount",
                "label": "Expected Target Amount",
                "fieldtype": "Float",
                "insert_after": "actual_target_amount",
                "read_only": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "is_excel_uploaded",
                "label": "Is Excel Uploaded",
                "fieldtype": "Check",
                "read_only": 1,
            },
            {
                "fieldname": "goal_name_ar",
                "label": "Goal Name in Arabic",
                "fieldtype": "Data",
                "insert_after": "goal_name",
            },
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
                "insert_after": "unlink_payment_on_cancellation_of_employee_advance",
            },
            {
                "fieldname": "appraisal_cycle_duration",
                "label": "Appraisal Cycle Duration (in days)",
                "fieldtype": "Int",
                "default": "90",
                "insert_after": "appraisal_cycle_section",
            },
            {
                "fieldname": "appraisal_cycle_creation_dates",
                "label": "Appraisal Cycle Creation Dates",
                "fieldtype": "Table",
                "options": "Appraisal Cycle Creation Dates",
                "insert_after": "appraisal_cycle_duration",
            },
        ],
    }

    if not frappe.db.exists("Role", "COO"):
        frappe.get_doc({"doctype": "Role", "role_name": "COO"}).insert(
            ignore_permissions=True
        )

    create_custom_fields(custom_fields, ignore_validate=True)

    # Appraisal KRA table must not be mandatory when filling from a goal template
    if not frappe.db.exists(
        "Property Setter",
        {
            "doc_type": "Appraisal",
            "field_name": "appraisal_template",
            "property": "mandatory_depends_on",
        },
    ):
        frappe.get_doc(
            {
                "doctype": "Property Setter",
                "doctype_or_field": "DocField",
                "doc_type": "Appraisal",
                "field_name": "appraisal_template",
                "property": "mandatory_depends_on",
                "property_type": "Code",
                "value": "",
            }
        ).insert(ignore_permissions=True)

    frappe.clear_cache()
