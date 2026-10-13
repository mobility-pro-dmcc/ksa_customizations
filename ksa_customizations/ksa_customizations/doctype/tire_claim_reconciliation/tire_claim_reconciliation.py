# Copyright (c) 2026, Mobility Pro DMCC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today


class TireClaimReconciliation(Document):
	def validate(self):
		self.validate_items()

	def validate_items(self):
		if not self.items:
			frappe.throw(_("Please add at least one item."))

		seen = set()
		for row in self.items:
			key = (row.item_code, row.production_year)
			if key in seen:
				frappe.throw(
					_("Row #{0}: Item {1} with production year {2} is duplicated.").format(
						row.idx, row.item_code, row.production_year
					)
				)
			seen.add(key)

	def on_submit(self):
		return_invoice = self.make_return_invoice()
		frappe.msgprint(
			_("Return Invoice {0} has been created.").format(
				frappe.utils.get_link_to_form("Sales Invoice", return_invoice)
			),
			alert=True,
		)

	def make_return_invoice(self):
		company = frappe.db.get_value("Sales Invoice", self.sales_invoice, "company")
		claims = [d.tire_claim for d in self.tire_claims if d.tire_claim]
		remarks = "{0}\nInvoice: {1}".format(self.reason, self.sales_invoice)
		if claims:
			remarks += "\nTire Claims: {0}".format(", ".join(claims))

		return_invoice = frappe.new_doc("Sales Invoice")
		return_invoice.update(
			{
				"is_return": 1,
				"posting_date": today(),
				"customer": self.customer,
				"company": company,
				"return_against": self.sales_invoice,
				"credit_adjustment_against": self.sales_invoice,
				# Sales Invoice.tire_claim is a single link: keep the first, the rest are in remarks
				"tire_claim": claims[0] if claims else None,
				"custom_return_reason": self.reason,
				"custom_note_reason": self.reason,
				"taxes_and_charges": self.tax,
				"income_account": self.income_account,
				"remarks": remarks,
			}
		)
		return_invoice.set("custom_return_against_additional_references", [{"sales_invoice": self.sales_invoice}])

		original_rows = {
			(d.item_code, d.production_year): d.name
			for d in frappe.get_all(
				"Sales Invoice Item",
				filters={"parent": self.sales_invoice},
				fields=["name", "item_code", "production_year"],
				order_by="idx desc",
			)
		}

		for row in self.items:
			return_invoice.append(
				"items",
				{
					"item_code": row.item_code,
					"production_year": row.production_year,
					"qty": -abs(row.qty),
					"rate": row.rate,
					"income_account": self.income_account,
					"sales_invoice_item": original_rows.get((row.item_code, row.production_year)),
				},
			)

		return_invoice.set_missing_values()
		return_invoice.calculate_taxes_and_totals()
		return_invoice.insert(ignore_permissions=True)
		return return_invoice.name
