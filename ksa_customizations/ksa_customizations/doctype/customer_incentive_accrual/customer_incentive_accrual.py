# Copyright (c) 2026, Mobility Pro DMCC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomerIncentiveAccrual(Document):
	def on_submit(self):
		self.create_journal_entry()

	def get_incentive_amounts(self):
		return frappe.db.sql(f"""
			SELECT 
				cg.branch AS branch,
				SUM(child.amount) AS total_amount
			FROM 
				`tabCustomer Incentive Accrual Detail` child
			INNER JOIN 
				`tabCustomer` c ON child.customer = c.name
			INNER JOIN 
				`tabCustomer Group` cg ON c.customer_group = cg.name
			WHERE 
				child.parenttype = 'Customer Incentive Accrual'
				AND child.parent = '{self.name}'
			GROUP BY 
				cg.branch
		""", as_dict=True)
	
	def create_journal_entry(self):
		incentive_amounts = self.get_incentive_amounts()
		accounts = []
		sum_total_amount = sum(amount['total_amount'] for amount in incentive_amounts)
		accounts.append({
			'account': self.accrual_expense_account,
			'credit_in_account_currency': max(sum_total_amount, 0),
			'debit_in_account_currency': -min(sum_total_amount, 0),
		})
		for amount in incentive_amounts:
			accounts.append({
				'account': self.expense_account,
				'branch': amount['branch'],
				'debit_in_account_currency': amount['total_amount'] if amount['total_amount'] > 0 else 0,
				'credit_in_account_currency': -amount['total_amount'] if amount['total_amount'] < 0 else 0,
			})
		journal_entry = frappe.get_doc({
			'doctype': 'Journal Entry',
			# 'company': self.company,
			'posting_date': self.posting_date,
			'accounts': accounts,
			'custom_customer_incentive_accrual': self.name,
			'user_remark': self.remarks,
			'remark': self.remarks,
		}).insert(ignore_permissions=True)
		journal_entry.submit()