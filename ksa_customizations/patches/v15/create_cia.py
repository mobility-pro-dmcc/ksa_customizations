from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Journal Entry": [
            {
                "fieldname": "custom_customer_incentive_accrual",
                "label": "Customer Incentive Accrual",
                "fieldtype": "Link",
                "options": "Customer Incentive Accrual",
                "insert_after": "user_remark",
                "reqd": 1,
                "read_only": 1,
                "no_copy": 1,
                "allow_in_quick_entry": 0,
                "allow_on_submit": 0,
                "bold": 0,
                "collapsible": 0,
                "columns": 0,
                "hidden": 0,
                "hide_border": 0,
                "hide_days": 0,
                "hide_seconds": 0,
                "ignore_user_permissions": 0,
                "ignore_xss_filter": 0,
                "in_global_search": 0,
                "in_list_view": 0,
                "in_preview": 0,
                "in_standard_filter": 0,
                "is_virtual": 0,
                "non_negative": 0,
                "permlevel": 0,
                "print_hide": 0,
                "print_hide_if_no_value": 0,
                "report_hide": 0,
                "search_index": 0,
                "show_dashboard": 0,
                "sort_options": 0,
                "translatable": 0,
                "unique": 0
            }
        ]
    }

    # Arguments: custom_fields dict, ignore_validate=False, update=True
    create_custom_fields(custom_fields, update=True)