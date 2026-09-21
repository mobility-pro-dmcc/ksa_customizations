# Copyright (c) 2026, Mobility Pro DMCC and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder.functions import Sum
from pypika import Case, Criterion
from frappe.model.document import Document
from frappe.utils import today
from frappe import _
class PriceVarianceDiscount(Document):
	def before_submit(self):
		invoices = self.get_invoices_details()
		processed_invoices = []
		for invoice, invoice_details in invoices.items():
			if invoice_details:
				processed_invoices.append(invoice)
				self.attach_differences(invoice_details)
				self.make_return_invoice(invoice, invoice_details)
		if processed_invoices:
			frappe.msgprint(_("variance discounts are made for invoices {0}").format(" - ".join(processed_invoices)))
		else:
			frappe.msgprint(_("variance discounts discarded as listed item are not included in any invoice"))
	def make_return_invoice(self, invoice, invoice_details):
		customer, company = frappe.db.get_value("Sales Invoice", invoice, ["customer", "company"])
		return_invoice = frappe.get_doc({
			"doctype": "Sales Invoice",
			"is_return": 1,
			"posting_date": today(),
			"customer": customer,
			"company": company,
			"items": invoice_details,
			"return_against": invoice,     
			"custom_return_reason": self.reason,
			"custom_note_reason": self.reason,
			"income_account": self.income_account
		})
		return_invoice.insert(ignore_permissions=True)
		return_invoice.set_missing_values()
		return_invoice.calculate_taxes_and_totals()
		return_invoice.save()
		return return_invoice.name

	def attach_differences(self, invoice_details):
		items_prices = {item.item_code: item.diff for item in self.items}
		for item in invoice_details:
			item.rate = items_prices.get(item.item_code)
			item.qty = -item.qty
			item.sales_invoice_item = item.get("name") 
			item.income_account = self.income_account
			item.pop("name", None)
			item.pop("parent", None)
	@frappe.whitelist()
	def get_invoices_details(self):
		if not self.items or not self.sales_invoices:
			return {}

		items_list = [item.item_code for item in self.items]
		invoices_list = [item.sales_invoice for item in self.sales_invoices]
		
		si_item = frappe.qb.DocType("Sales Invoice Item")
		si = frappe.qb.DocType("Sales Invoice")
		
		item_conditions = []
		for entry in self.items:
			item_code = entry.get("item_code")
			prod_year = entry.get("production_year")
			cond = (si_item.item_code == item_code) & (si_item.production_year == prod_year)
			item_conditions.append(cond)

		combined_items_filter = Criterion.any(item_conditions)

		original_row_name = Case().when(si.is_return == 1, si_item.sales_invoice_item).else_(si_item.name)
		
		original_invoice_name = Case().when(si.is_return == 1, si.credit_adjustment_against).else_(si.name)

		query = (
			frappe.qb.from_(si_item)
			.inner_join(si).on(si_item.parent == si.name)
			.select(
				si_item.item_code,
				original_row_name.as_("name"),
				original_invoice_name.as_("parent"),
				si_item.production_year,
				si.customer,
				Sum(si_item.qty).as_("qty")
			)
			.where(
				(si.docstatus != 2) &
				(si_item.item_code.isin(items_list)) &
				(
					(si.name.isin(invoices_list)) |
					(si.credit_adjustment_against.isin(invoices_list))
				) &
				combined_items_filter
			)
			.groupby(
				original_row_name,
				original_invoice_name,
				si_item.item_code,
				si_item.production_year,
				si.customer
			)
			.having(
				Sum(si_item.qty) > 0
			)
		)
		
		details = query.run(as_dict=True)
		result = {invoice: [] for invoice in invoices_list}
		for row in details:
			if row.parent in result:
				result[row.parent].append(row)
				
		return result

