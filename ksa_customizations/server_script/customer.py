import frappe
import mobility_customizations as mc

@mc.wrap_script()
def update_sales_person_link(doc):
    # get previous version of the document
    old_doc = doc.get_doc_before_save()

    # if this is a new doc or sales_person did not change → do nothing
    if not old_doc or old_doc.sales_person == doc.sales_person:
        return

    # if new sales_person is empty, stop
    if not doc.sales_person:
        return

    # 1. delete ONLY the Dynamic Link rows for this customer
    frappe.db.delete(
        "Dynamic Link",
        {
            "link_doctype": "Customer",
            "link_name": doc.name
        }
    )

    # 2. find the new contact by sales_person
    contact_name = frappe.db.get_value(
        "Contact",
        {"sales_person": doc.sales_person},
        "name"
    )

    if not contact_name:
        frappe.throw(f"No Contact found for Sales Person: {doc.sales_person}")

    # 3. insert new Dynamic Link row
    frappe.get_doc({
        "doctype": "Dynamic Link",
        "parenttype": "Contact",
        "parentfield": "links",
        "parent": contact_name,
        "link_doctype": "Customer",
        "link_name": doc.name,
        "link_title": doc.customer_name
    }).insert(ignore_permissions=True)

    frappe.db.commit()


def on_update(doc, method):
    update_sales_person_link(doc)