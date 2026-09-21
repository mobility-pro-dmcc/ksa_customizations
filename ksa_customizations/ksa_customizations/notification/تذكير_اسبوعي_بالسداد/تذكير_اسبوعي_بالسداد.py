import frappe
from frappe.utils import today, add_days


def get_context(context):
	overdue_limit = add_days(today(), -7)
	def get_customer_outstanding_amount(customer):
		return frappe.db.get_value(
			"Sales Invoice", 
			{
				"customer": customer,
				"docstatus": 1,
				"outstanding_amount": [">", 0],
				"due_date": ["<=",overdue_limit],
			},
			"sum(outstanding_amount)"
		) or 0

	def get_outstanding_invoices(customer):
		sinv = frappe.qb.DocType("Sales Invoice")
		cust = frappe.qb.DocType("Customer")

		query = (
			frappe.qb.from_(sinv)
			.inner_join(cust).on(sinv.customer == cust.name)
			.select(sinv.name)
			.where(
				(sinv.docstatus == 1) &
				(sinv.outstanding_amount > 2000) &
				(sinv.is_return == 0) &
				(sinv.is_debit_note == 0) &
				(sinv.due_date < overdue_limit) &
				(cust.send_whatsapp_notifications == 1)
			)
		)

		return query.run(pluck=True) or " "
	doc = context["doc"]
	context["outstanding_amount"] = get_customer_outstanding_amount(doc.name)
	context["outstanding_invoices"] = (" • ".join(get_outstanding_invoices(doc.name))).encode()

	return context