import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
    custom_fields = {
        "Journal Entry Account": [
            {
                "fieldname": "landed_cost_category",
                "label": "Landed Cost Category",
                "fieldtype": "Link",
                "options": "Landed Cost Expense Category Mapper",
                "insert_after": "expense_account",
                "in_list_view": 1,
            }
        ]
    }
    create_custom_fields(custom_fields, update=True)

    add_select_option("Journal Entry Account", "reference_type", "Purchase Receipt")
    add_select_option("Journal Entry", "voucher_type", "Landed Cost Entry")


def add_select_option(doctype, fieldname, option):
    existing = frappe.db.get_value(
        "Property Setter",
        {"doc_type": doctype, "field_name": fieldname, "property": "options"},
        ["name", "value"],
        as_dict=True,
    )

    if existing:
        options = (existing.value or "").split("\n")
    else:
        frappe.clear_cache(doctype=doctype)
        options = (frappe.get_meta(doctype).get_field(fieldname).options or "").split("\n")

    if option in options:
        return

    options.append(option)
    value = "\n".join(options)

    if existing:
        frappe.db.set_value("Property Setter", existing.name, "value", value)
    else:
        make_property_setter(doctype, fieldname, "options", value, "Text")

    frappe.clear_cache(doctype=doctype)
