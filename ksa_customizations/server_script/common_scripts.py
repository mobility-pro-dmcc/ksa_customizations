import frappe

def update_contact_person(doc, method):
    contact = frappe.db.get_all('Dynamic Link', {'parenttype':'Contact', 'link_doctype':'Customer', 'link_name':doc.customer}, ['parent'][0], pluck='parent')
    doc.contact_person = contact[0] if contact else None
    doc.contact_display = contact[0] if contact else None
    doc.contact_email = frappe.db.get_value('Contact', contact, 'email_id') or None