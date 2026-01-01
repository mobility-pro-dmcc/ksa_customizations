import frappe
import time
import ksa_customizations as kc 
from erpnext.accounts.doctype.payment_entry.payment_entry import get_outstanding_reference_documents
from ksa_customizations.api import trigger_reconciliation_for_queued_docs

@kc.wrap_script()
def auto_reconcile_after_payment_entry_submit(doc):
    """ Script: Auto-Reconciliation After Payment Entry Submission """
    time.sleep(15)
    if doc.party_type == 'Customer' and not doc.references and not doc.get("payment_log"):
        company = doc.company
        account = doc.paid_from
        customer = doc.party
        args = {'party_type':'Customer', 'party':customer, 'party_account':account}
        outstanding_documents = get_outstanding_reference_documents(args, True)
        flag = False
        if outstanding_documents:
            total = 0
            for i in outstanding_documents:
                if i.outstanding_amount > 0:
                    flag = True
                    break
        if flag:
            unallocated_amount = frappe.db.get_value("Payment Entry", [["party", "=", customer], ["unallocated_amount", ">", 0], ["docstatus", "=", 1]], "sum(unallocated_amount)") or 0
            credit_amount = frappe.db.get_value("Journal Entry Account", [["party", "=", customer], ["credit", ">", 0], ["reference_name", "=", None], ["docstatus", "=", 1]], "sum(credit)") or 0
            cn_amount = frappe.db.get_value("Sales Invoice", [["customer", "=", customer], ["outstanding_amount", "<", 0], ["is_return", "=", 1], ["docstatus", "=", 1]], "sum(outstanding_amount)") or 0
            if unallocated_amount or credit_amount or cn_amount:
                reconciliation = frappe.get_doc({
                    "doctype": "Process Payment Reconciliation",
                    "party_type": "Customer",
                    "party" : customer,
                    "company": company,
                    "receivable_payable_account": account,
                    "default_advance_account": account
                })
                reconciliation.insert(ignore_permissions=True)
                reconciliation.submit()
                trigger_reconciliation_for_queued_docs()
    frappe.db.commit()

def on_submit(doc, method=None):
    frappe.enqueue(auto_reconcile_after_payment_entry_submit, doc=doc)