import frappe
from frappe.utils import today
from erpnext.accounts.utils import get_balance_on

def get_context(context):
	doc = context["doc"]
	context["customer_balance"] = get_balance_on(
		party_type="Customer",
		party= doc.customer,
		company= doc.company
	)
	context["customer_outstanding"] = frappe.db.get_value("Sales Invoice", {"due_date": ["<=", today()], "docstatus": 1, "is_return": 0, "outstanding_amount": [">", 0], "customer": doc.customer}, "sum(outstanding_amount)")
	return context