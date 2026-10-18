# Copyright (c) 2026, Mobility Pro DMCC and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KSACustomizationSettings(Document):
	def get_ai_info(self):
		return {
			"model": self.used_model,
			"api_key": self.get_password("api_key")
		}
