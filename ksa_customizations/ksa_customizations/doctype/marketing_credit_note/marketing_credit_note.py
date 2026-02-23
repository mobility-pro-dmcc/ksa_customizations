# Copyright (c) 2026, Mobility Pro DMCC
# License: see license.txt

import frappe
import json
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum
from decimal import Decimal, ROUND_DOWN


class MarketingCreditNote(Document):

    def validate(self):
        self.calculate_commission()

    def on_submit(self):
        self.create_return_invoice()

    @staticmethod
    def distribute_amount(total, values):
        if not values or total == 0:
            return [0.0] * len(values)

        total = Decimal(str(total))
        values = [Decimal(str(v)) for v in values]

        total_values = sum(values)
        if total_values == 0:
            return [0.0] * len(values)

        raw = [(v / total_values) * total for v in values]

        truncated = [
            v.quantize(Decimal("0.01"), rounding=ROUND_DOWN) for v in raw
        ]

        diff = total - sum(truncated)

        remainders = sorted(
            [(i, raw[i] - truncated[i]) for i in range(len(raw))],
            key=lambda x: x[1],
            reverse=True,
        )

        for i in range(int(diff * 100)):
            truncated[remainders[i][0]] += Decimal("0.01")

        return [float(v) for v in truncated]

    def calculate_commission(self):

        SalesInvoiceItem = DocType("Sales Invoice Item")
        SalesInvoice = DocType("Sales Invoice")
        Item = DocType("Item")
        Company = DocType("Company")

        net_expr = (
            SalesInvoiceItem.amount
            - SalesInvoiceItem.discount_amount_custom
        )

        accounts = (
            frappe.qb.from_(Company)
            .select(Company.default_income_account)
            .union(
                frappe.qb.from_(Company)
                .select(Company.default_sales_return_account)
            )
        )

        query = (
            frappe.qb.from_(SalesInvoiceItem)
            .inner_join(SalesInvoice)
            .on(SalesInvoiceItem.parent == SalesInvoice.name)
            .inner_join(Item)
            .on(SalesInvoiceItem.item_code == Item.name)
            .select(
                SalesInvoiceItem.item_code,
                SalesInvoiceItem.production_year,
                Sum(net_expr).as_("net_amount"),
            )
            .where(
                (SalesInvoiceItem.docstatus == 1)
                & (SalesInvoice.docstatus == 1)
                & (SalesInvoiceItem.income_account.isin(accounts))
                & (
                    SalesInvoice.posting_date.between(
                        self.from_date, self.to_date
                    )
                )
                & (SalesInvoice.customer == self.customer)
                & (Item.brand == self.brand)
            )
            .groupby(
                SalesInvoiceItem.item_code,
                SalesInvoiceItem.production_year,
            )
            .having(Sum(net_expr) > 0)
        )

        data = query.run(as_dict=True)

        if not data:
            self.commision_json = []
            return

        net_amounts = [d["net_amount"] for d in data]

        distributed = self.distribute_amount(
            self.commision, net_amounts
        )

        for i, row in enumerate(data):
            row["commission_amount"] = distributed[i]

        self.commision_json = json.dumps(data)
        
    def create_return_invoice(self):
        if not self.commision_json:
            return

        data = json.loads(self.commision_json)

        invoices = self.get_return_invoices()

        if not invoices:
            return

        return_si = frappe.new_doc("Sales Invoice")
        return_si.customer = self.customer
        return_si.is_return = 1
        return_si.income_account = self.income_account
        return_si.extend("custom_return_against_additional_references", invoices)
        return_si.custom_return_reason = self.reason
        return_si.taxes_and_charges = self.taxes_and_charges_template
        return_si.flags.ignore_mandatory = True

        for row in data:
            if not row.get("commission_amount"):
                continue

            return_si.append(
                "items",
                {
                    "item_code": row["item_code"],
                    "qty": -1,
                    "rate": row["commission_amount"],
                    "production_year": row["production_year"],
                    "income_account": self.income_account,
                },
            )
        
        if self.taxes_and_charges_template:
            taxes = frappe.get_all(
                "Sales Taxes and Charges",
                filters={"parent": self.taxes_and_charges_template},
                fields="*",
                order_by="idx",
            )

            for tax in taxes:
                tax.pop("name", None)
                tax.pop("parent", None)
                tax.pop("parenttype", None)
                tax.pop("parentfield", None)

                return_si.append("taxes", tax)
        return_si.set_missing_values()
        return_si.calculate_taxes_and_totals()  
        return_si.insert()

    def get_return_invoices(self):
        SalesInvoiceItem = DocType("Sales Invoice Item")
        SalesInvoice = DocType("Sales Invoice")
        Item = DocType("Item")

        query = (
            frappe.qb.from_(SalesInvoiceItem)
            .inner_join(SalesInvoice)
            .on(SalesInvoiceItem.parent == SalesInvoice.name)
            .inner_join(Item)
            .on(SalesInvoiceItem.item_code == Item.name)
            .select(
                SalesInvoice.name.as_("sales_invoice")
            )
            .where(
                (SalesInvoiceItem.docstatus == 1)
                & (SalesInvoice.docstatus == 1)
                & (SalesInvoice.is_return == 0)
                & (SalesInvoice.is_debit_note == 0)
                & (
                    SalesInvoice.posting_date.between(
                        self.from_date, self.to_date
                    )
                )
                & (SalesInvoice.customer == self.customer)
                & (Item.brand == self.brand)
            ).groupby(SalesInvoice.name)
        )

        return query.run(as_dict=True)