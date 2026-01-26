import frappe
import mobility_customizations as mc
from ksa_customizations.server_script.common_scripts import update_contact_person

def _update_sales_order_billing_from_invoice(doc, is_cancel=False):
    """Update Sales Order Item.billed_qty and maybe close/reopen SO.

    Returns:
        str | None: final Sales Order status (on cancel), or None on submit.
    """
    if doc.is_return or doc.update_stock or doc.is_opening == "Yes":
        return None

    # qty sign: + on submit, - on cancel
    sign = -1 if is_cancel else 1

    # Collect total qty per Sales Order Item (in case of repeated so_detail)
    so_item_qty_map = {}
    for row in doc.items:
        if not row.so_detail:
            continue
        so_item_qty_map.setdefault(row.so_detail, 0)
        so_item_qty_map[row.so_detail] += sign * (row.qty or 0)

    if not so_item_qty_map:
        return None

    item_names = list(so_item_qty_map.keys())

    # Fetch existing billed_qty once for all related SO Items
    so_items = frappe.get_all(
        "Sales Order Item",
        filters={"name": ["in", item_names]},
        fields=["name", "billed_qty", "parent"],
    )

    if not so_items:
        return None

    # All these items belong to the same Sales Order in standard flows
    so_name = so_items[0].parent

    # Update billed_qty for each affected Sales Order Item
    for item in so_items:
        delta = so_item_qty_map.get(item.name, 0) or 0
        if not delta:
            continue

        current_billed = item.billed_qty or 0
        new_billed = current_billed + delta
        if new_billed < 0:
            new_billed = 0

        frappe.db.set_value(
            "Sales Order Item",
            item.name,
            "billed_qty",
            new_billed,
            update_modified=False,
        )

    # Recalculate full billing
    all_items = frappe.get_all(
        "Sales Order Item",
        filters={"parent": so_name},
        fields=["qty", "billed_qty"],
    )

    fully_billed = True
    for row in all_items:
        qty = row.qty or 0
        billed = row.billed_qty or 0
        if billed < qty:
            fully_billed = False
            break

    # Read current SO data
    so_row = frappe.db.get_value(
        "Sales Order",
        so_name,
        ["per_billed", "status"],
        as_dict=True,
    ) or {"per_billed": 0, "status": None}

    per_billed = so_row.per_billed or 0
    current_status = so_row.status

    # On submit: close when fully billed
    if not is_cancel:
        if fully_billed and per_billed < 100:
            from erpnext.selling.doctype.sales_order.sales_order import update_status
            update_status(
                status="Closed",
                name=so_name,
            )
        return None

    # On cancel: if no longer fully billed and SO is Closed, reopen
    new_status = current_status
    if not fully_billed and current_status == "Closed":
        # you can change this to "To Deliver and Bill" or "To Bill" depending on your flow
        new_status = "To Bill"
        frappe.db.set_value(
            "Sales Order",
            so_name,
            "status",
            new_status,
            update_modified=False,
        )

    # Return final SO status on cancel
    return new_status

def _update_dn_billing_from_invoice(doc, is_cancel=False):
    """Update Delivery Note Item.billed_qty and DN billing fields.

    Returns:
        str | None: final DN.billing_status on cancel, or None on submit.
    """
    if doc.is_return or doc.update_stock or doc.is_opening == "Yes":
        return None

    sign = -1 if is_cancel else 1

    # Map DN Item name → total invoiced qty (with sign)
    dn_item_qty_map = {}
    for row in doc.items:
        if not row.dn_detail:
            continue
        dn_item_qty_map.setdefault(row.dn_detail, 0)
        dn_item_qty_map[row.dn_detail] += sign * (row.qty or 0)

    if not dn_item_qty_map:
        return None

    dn_item_names = list(dn_item_qty_map.keys())

    # Fetch DN Items once
    dn_items = frappe.get_all(
        "Delivery Note Item",
        filters={"name": ["in", dn_item_names]},
        fields=["name", "billed_qty", "qty", "parent"],
    )

    if not dn_items:
        return None

    dn_name = dn_items[0].parent

    # Update billed_qty on Delivery Note Items
    for item in dn_items:
        delta = dn_item_qty_map.get(item.name, 0) or 0
        if not delta:
            continue

        current_billed = item.billed_qty or 0
        new_billed = current_billed + delta
        if new_billed < 0:
            new_billed = 0

        frappe.db.set_value(
            "Delivery Note Item",
            item.name,
            "billed_qty",
            new_billed,
            update_modified=False,
        )

    # Recalculate totals for that Delivery Note
    totals = frappe.db.sql(
        """
        SELECT
            COALESCE(SUM(billed_qty), 0) AS total_billed_qty,
            COALESCE(SUM(qty), 0)        AS total_delivered_qty
        FROM `tabDelivery Note Item`
        WHERE parent = %s
        """,
        dn_name,
        as_dict=True,
    )[0]

    total_billed_qty = totals.total_billed_qty
    total_delivered_qty = totals.total_delivered_qty

    if total_delivered_qty == 0 or total_billed_qty == 0:
        custom_per_billed = 0
        billing_status = "Not Billed"
    elif 0 < total_billed_qty < total_delivered_qty:
        custom_per_billed = (total_billed_qty / total_delivered_qty) * 100
        billing_status = "Partly Billed"
    else:
        custom_per_billed = 100
        billing_status = "Fully Billed"

    frappe.db.set_value(
        "Delivery Note",
        dn_name,
        {
            "custom_per_billed": custom_per_billed,
            "billing_status": billing_status,
        },
        update_modified=False,
    )

    # Sales Order closing logic stays same on submit; on cancel we just return statuses
    so = doc.items[0].sales_order if doc.items and getattr(doc.items[0], "sales_order", None) else None
    if not is_cancel and so:
        so_status = frappe.db.get_value(
            "Sales Order",
            so,
            ["billing_status", "delivery_status"],
            as_dict=True,
        )
        if so_status:
            if so_status.billing_status == "Partly Billed" and so_status.delivery_status == "Fully Delivered":
                frappe.db.set_value(
                    "Sales Order",
                    so,
                    "status",
                    "Closed",
                    update_modified=False,
                )

    # On cancel: return final DN billing_status
    if is_cancel:
        return billing_status

    return None

@mc.wrap_script()
def after_submit_sales_invoice_so(doc, method):
    _update_sales_order_billing_from_invoice(doc, is_cancel=False)

@mc.wrap_script()
def on_cancel_sales_invoice_so(doc, method):
    return _update_sales_order_billing_from_invoice(doc, is_cancel=True)

@mc.wrap_script()
def after_submit_sales_invoice_dn(doc, method):
    # called on_submit
    _update_dn_billing_from_invoice(doc, is_cancel=False)

@mc.wrap_script()
def on_cancel_sales_invoice_dn(doc, method):
    # called on_cancel – returns final DN.billing_status
    return _update_dn_billing_from_invoice(doc, is_cancel=True)

@mc.wrap_script()
def update_contact(doc, method):
    update_contact_person(doc, method)

def on_cancel(doc, method):
    on_cancel_sales_invoice_so(doc, method)
    on_cancel_sales_invoice_dn(doc, method)

def on_submit(doc, method):
    after_submit_sales_invoice_so(doc, method)
    after_submit_sales_invoice_dn(doc, method)

def validate(doc, method):
    update_contact(doc, method)