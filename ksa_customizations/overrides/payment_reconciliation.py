import frappe
from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import (
    PaymentReconciliation,
)
from frappe.utils import flt
import mobility_customizations as mc


class CustomPaymentReconciliation(PaymentReconciliation):
    @mc.wrap_script()
    def get_payment_details(self, row, dr_or_cr):
        payment_details = super().get_payment_details(row, dr_or_cr)
        payment_datails["precision"] = 2
        return payment_details
