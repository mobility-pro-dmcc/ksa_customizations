# Copyright (c) 2026, Mobility Pro DMCC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PaymentTransferRequest(Document):
	def on_update(self):
		self.check_notification()
	
	def before_cancel(self):
		self.cancel_payment()

	def on_trash(self):
		self.delete_payment_entry()
	
	def before_submit(self):
		self.create_payment_entry()

	def cancel_payment(self):
		payment_name = frappe.db.get_value("Payment Entry", {"custom_payment_transfer_request": self.name})
		if payment_name:
			payment = frappe.get_doc("Payment Entry", payment_name)
			payment.flags.is_system_cancel = True
			payment.flags.ignore_permissions = True
			payment.flags.ignore_links = True
			payment.cancel()
	
	def create_payment_entry(self):
		payment_dict = {
			"payment_type": "Internal Transfer",
			"posting_date": self.posting_date,
			"company": self.company,
			"paid_from": self.paid_from,
			"paid_to": self.paid_to,
			"source_exchange_rate": 1,
			"paid_amount": self.paid_amount,
			"target_exchange_rate": 1,
			"received_amount": self.paid_amount,
			"reference_no": self.name,
			"reference_date": self.posting_date,
			"custom_payment_transfer_request": self.name,
			"doctype": "Payment Entry"
		}
		if self.custom_remarks:
			payment_dict["custom_remarks"] = self.custom_remarks
			payment_dict["remarks"] = self.remarks
		payment_entry = frappe.get_doc(payment_dict)
		payment_entry.insert(ignore_permissions=True)
		payment_entry.submit()

	def delete_payment_entry(self):
		payment_name = frappe.db.get_value("Payment Entry", {"custom_payment_transfer_request": self.name})
		if payment_name:
			frappe.delete_doc(
				"Payment Entry",
				payment_name,
				force=1,
				ignore_permissions=True,
				ignore_missing=True,
			)
		
	def check_notification(self):
		old_doc = self.get_doc_before_save()

		if not old_doc or old_doc.workflow_state != self.workflow_state:
			notif = frappe.get_doc("Notification", "Payment Transfer Request")
			notif.send(self)