import frappe
import mobility_customizations as mc

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
@mc.wrap_script()
def create_quarterly_appraisals():
    def get_hr_emails():
        """Helper function to get emails of all active users with the 'HR User' role."""
        hr_roles = frappe.get_all("Has Role", filters={"role": "HR User"}, fields=["parent"])
        user_names = [role.parent for role in hr_roles]
        
        if not user_names:
            return []
    
        users = frappe.get_all(
            "User", 
            filters={"name": ("in", user_names), "enabled": 1}, 
            fields=["email"]
        )
        return [user.email for user in users if user.email]
    """Scheduled function to generate quarterly appraisal cycles and employee appraisals."""
    current_date = frappe.utils.getdate(frappe.utils.today())
    year = current_date.year
    month = current_date.month

    if month in (1, 2, 3):
        quarter = 1
        start_date = f"{year}-01-01"
        end_date = f"{year}-03-31"
    elif month in (4, 5, 6):
        quarter = 2
        start_date = f"{year}-04-01"
        end_date = f"{year}-06-30"
    elif month in (7, 8, 9):
        quarter = 3
        start_date = f"{year}-07-01"
        end_date = f"{year}-09-30"
    else:
        quarter = 4
        start_date = f"{year}-10-01"
        end_date = f"{year}-12-31"

    cycle_name = f"{year} Q{quarter}"
    hr_emails = get_hr_emails()

    existing_cycle = frappe.db.exists("Appraisal Cycle", {
        "start_date": start_date,
        "end_date": end_date
    })

    if existing_cycle:
        return

    try:
        default_company = frappe.db.get_default('Company')
        
        cycle = frappe.get_doc({
            "doctype": "Appraisal Cycle",
            "cycle_name": cycle_name,
            "start_date": start_date,
            "end_date": end_date,
            "company": default_company
        })
        cycle.flags.ignore_permissions = True
        cycle.insert()
        cycle.set_employees()
        cycle.save()
        cycle.create_appraisals()
        submit_appraisals(cycle.name)
    except Exception as e:
        frappe.log_error(message =f"Error creating Appraisal Cycle {cycle_name}: {str(e)}", title ="Appraisal Scheduler")
        if hr_emails:
            frappe.sendmail(
                recipients=hr_emails,
                subject=f"Error: Appraisal Cycle Creation Failed - {cycle_name}",
                message=str(e)
            )
def submit_appraisals(cycle_name):
    """Submits all appraisals associated with the given appraisal cycle."""
    appraisals = frappe.get_all("Appraisal", filters={"appraisal_cycle": cycle_name, "docstatus": 0}, fields=["name"])
    for appraisal in appraisals:
        try:
            appraisal_doc = frappe.get_doc("Appraisal", appraisal.name)
            appraisal_doc.submit()
        except Exception as e:
            frappe.log_error(message=f"Error submitting Appraisal {appraisal.name}: {str(e)}", title="Appraisal Submission Error")