import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Appraisal": [
            {
                "fieldname": "fill_from_goal_template",
                "label": "Fill from Goal Template",
                "fieldtype": "Check",
                "insert_after": "rate_goals_manually",
                "default": "1"
            }
        ],
        "Designation": [
            {
                "fieldname": "goal_template",
                "label": "Goal Template",
                "fieldtype": "Link",
                "options": "Goal Template",
                "insert_after": "appraisal_template"
            }
        ],
        "Appraisee": [
            {
                "fieldname": "goal_template",
                "label": "Goal Template",
                "fieldtype": "Link",
                "options": "Goal Template",
                "insert_after": "designation",
                "in_list_view": 1
            }
        ]
    }

    create_custom_fields(custom_fields, ignore_validate=True)
    # add custom property to appraisal_kra child table to make reqd is zero in property setter
    frappe.get_doc({
        "doctype": "Property Setter",
        "doctype_or_field": "DocField",
        "doc_type": "Appraisal",
        "field_name": "appraisal_template",
        "property": "mandatory_depends_on",
        "property_type": "Code",
        "value": ""
    }).insert(ignore_permissions=True)
    frappe.clear_cache()