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