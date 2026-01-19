import frappe
from frappe import _

@frappe.whitelist()
def trigger_reconciliation_for_queued_docs():
    if not frappe.db.get_single_value("Accounts Settings", "auto_reconcile_payments"):
    	frappe.msgprint(
    		_("Auto Reconciliation of Payments has been disabled. Enable it through {0}").format(
    			get_link_to_form("Accounts Settings", "Accounts Settings")
    		)
    	)    
    	return
        
    all_queued = frappe.db.get_all(
    	"Process Payment Reconciliation",
    	filters={"docstatus": 1, "status": "Queued"},
    	order_by="creation desc",
    	as_list=1,
    )
    
    docs_to_trigger = []
    unique_filters = set()
    queue_size = 5
    
    fields = ["company", "party_type", "party", "receivable_payable_account"]