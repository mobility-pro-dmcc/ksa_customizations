# Copyright (c) 2026, Mobility Pro DMCC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomerInternalCreditlimitsTool(Document):
	def on_submit(self):
		for l in self.details:
			if l.credit_limit <= 0:
				l.credit_limit = 0.001
			customer_limit_row = frappe.db.get_value('Customer Credit Limit', {'parent': l.customer})
			if customer_limit_row:
				frappe.db.set_value('Customer Credit Limit', {'parent': l.customer}, 'credit_limit', l.credit_limit)
			else:
				frappe.get_doc({
					"doctype":"Customer Credit Limit",
					"parenttype":"Customer",
					"parent": l.customer,
					"parentfield": "credit_limits",
					"company": "Arabian Tires LLC",
					"credit_limit": l.credit_limit,
					"legal_credit_limit": 0
				}).save()