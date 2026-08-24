import mobility_customizations as mc
import frappe
from frappe import _

@mc.wrap_script()
def validate_is_excel_uploaded(doc, method):
    old_doc = doc.get_doc_before_save()
    if old_doc and old_doc.is_excel_uploaded:
        frappe.throw(_("You cannot edit this document as it is modified by the system"))
@mc.wrap_script()
def set_goal_target_amount(doc, method):
    if doc.expected_target_amount:
        actual_target_amount = doc.actual_target_amount or 0
        doc.progress = actual_target_amount / doc.expected_target_amount * 100

def before_save(doc, method):
    set_goal_target_amount(doc, method)
    validate_is_excel_uploaded(doc, method)