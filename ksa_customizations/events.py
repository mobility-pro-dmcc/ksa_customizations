import frappe

def repost_item_valuation_for_zero_qty_stock_entries():
    # This function identifies stock entries where the total actual quantity is zero but there is a non-zero stock value difference, which can lead to incorrect item valuation. It then creates and submits Repost Item Valuation documents for those entries to correct the valuation.
    sles = frappe.db.sql(
        """
        SELECT item_code, posting_date, voucher_no,
            MAX(CASE WHEN actual_qty < 0 THEN warehouse END) AS warehouse
        FROM `tabStock Ledger Entry`
        WHERE is_cancelled = 0 AND voucher_type = 'Stock Entry'
            AND posting_date > (SELECT value FROM tabSingles WHERE doctype = 'Stock Settings' AND field = 'stock_frozen_upto')
        GROUP BY item_code, posting_date, voucher_no
        HAVING SUM(actual_qty) = 0 AND ABS(SUM(stock_value_difference)) > 0.009
        UNION ALL
        SELECT item_code, posting_date, voucher_no,
            MAX(CASE WHEN actual_qty > 0 THEN warehouse END) AS warehouse
        FROM `tabStock Ledger Entry`
        WHERE is_cancelled = 0 AND voucher_type = 'Stock Entry'
            AND posting_date > (SELECT value FROM tabSingles WHERE doctype = 'Stock Settings' AND field = 'stock_frozen_upto')
        GROUP BY item_code, posting_date, voucher_no
        HAVING SUM(actual_qty) = 0 AND ABS(SUM(stock_value_difference)) > 0.009
        """,
        as_dict=True)
    for sle in sles:
        riv = frappe.get_doc({
            'doctype':'Repost Item Valuation',
            'item_code': sle.item_code,
            'warehouse': sle.warehouse,
            'based_on': 'Item and Warehouse',
            'posting_date': sle.posting_date,
            'posting_time': '00:00:00',
        })
        riv.insert()
        riv.submit()
    frappe.db.commit()

def repost_incorrect_sles():
    stock_closing_date = frappe.db.get_single_value('Stock Settings', 'stock_frozen_upto')
    company = frappe.db.get_default('Company')

    voucher_set = set()

    for diff_filter in ['Qty', 'Value', 'Valuation']:
        result = frappe.call(
            "frappe.desk.query_report.run",
            report_name="Stock Ledger Variance",
            filters={"company": company, "difference_in": diff_filter},
            ignore_prepared_report=True
        )

        for i in result.get("result", []):
            if i.posting_date > stock_closing_date and (
                abs(i.difference_in_qty) > 0
                or abs(i.diff_value_diff) > 0.0009
                or abs(i.valuation_diff) > 0.0009
            ):
                voucher = (i.voucher_type, i.voucher_no)
                if voucher not in voucher_set:
                    voucher_set.add(voucher)
                    repost_entry = frappe.get_doc({
                        'doctype': 'Repost Item Valuation',
                        'based_on': 'Transaction',
                        'posting_date': i.posting_date,
                        'posting_time': i.posting_time,
                        'voucher_type': i.voucher_type,
                        'voucher_no': i.voucher_no
                    })
                    repost_entry.insert()
                    repost_entry.submit()
                    frappe.db.commit()