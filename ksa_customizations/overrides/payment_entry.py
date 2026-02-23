import frappe
from frappe import _
import mobility_customizations as mc
from erpnext.accounts.utils import get_account_currency, get_balance_on
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
from erpnext.accounts.party import (
	complete_contact_details,
	get_default_contact,
	get_party_account,
)


class CustomPaymentEntry(PaymentEntry):
    def custom_get_account_details(self, account, date, cost_center=None):
        frappe.has_permission("Payment Entry", throw=True)

        # to check if the passed account is accessible under reference doctype Payment Entry
        account_list = frappe.get_list("Account", {"name": account}, reference_doctype="Payment Entry", limit=1)

        # There might be some user permissions which will allow account under certain doctypes
        # except for Payment Entry, only in such case we should throw permission error
        if not self.flags.ignore_accounts_permissions and not account_list:
            frappe.throw(_("Account: {0} is not permitted under Payment Entry").format(account))

        account_balance = (
            get_balance_on(account, date, cost_center=cost_center, ignore_account_permission=True)
            if frappe.get_single_value("Accounts Settings", "show_account_balance")
            else 0
        )

        return frappe._dict(
            {
                "account_currency": get_account_currency(account),
                "account_balance": account_balance,
                "account_type": frappe.get_cached_value("Account", account, "account_type"),
            }
        )
    
    @mc.wrap_script()
    def set_missing_values(self):
        if self.payment_type == "Internal Transfer":
            for field in (
                "party",
                "party_balance",
                "total_allocated_amount",
                "base_total_allocated_amount",
                "unallocated_amount",
            ):
                self.set(field, None)
            self.references = []
        else:
            if not self.party_type:
                frappe.throw(_("Party Type is mandatory"))

            if not self.party:
                frappe.throw(_("Party is mandatory"))

            _party_name = "title" if self.party_type == "Shareholder" else self.party_type.lower() + "_name"

            if frappe.db.has_column(self.party_type, _party_name):
                self.party_name = frappe.db.get_value(self.party_type, self.party, _party_name)
            else:
                self.party_name = frappe.db.get_value(self.party_type, self.party, "name")

        if self.party:
            if self.party_type == "Employee":
                self.contact_person = None
            elif not self.contact_person:
                self.contact_person = get_default_contact(self.party_type, self.party)

            complete_contact_details(self)
            if not self.party_balance and frappe.get_single_value("Accounts Settings", "show_party_balance"):
                self.party_balance = get_balance_on(
                    party_type=self.party_type, party=self.party, date=self.posting_date, company=self.company
                )

            if not self.party_account:
                party_account = get_party_account(self.party_type, self.party, self.company)
                self.set(self.party_account_field, party_account)
                self.party_account = party_account

        if self.paid_from and (
            not self.paid_from_account_currency
            or not self.paid_from_account_balance
            or not self.paid_from_account_type
        ):
            acc = self.custom_get_account_details(self.paid_from, self.posting_date, self.cost_center)
            self.paid_from_account_currency = acc.account_currency
            self.paid_from_account_balance = acc.account_balance
            self.paid_from_account_type = acc.account_type

        if self.paid_to and (
            not self.paid_to_account_currency
            or not self.paid_to_account_balance
            or not self.paid_to_account_type
        ):
            acc = self.custom_get_account_details(self.paid_to, self.posting_date, self.cost_center)
            self.paid_to_account_currency = acc.account_currency
            self.paid_to_account_balance = acc.account_balance
            self.paid_to_account_type = acc.account_type

        self.party_account_currency = (
            self.paid_from_account_currency
            if self.payment_type == "Receive"
            else self.paid_to_account_currency
        )



