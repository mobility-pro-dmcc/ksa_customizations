frappe.ui.form.on("Purchase Receipt", {
    refresh(frm) {
        if (frm.doc.docstatus !== 1) return;

        if (!frm.doc.is_return) {
            frm.add_custom_button(
                __("Landed Cost Voucher (Estimated)"),
                () => {
                    frappe.call({
                        method: "ksa_customizations.api.create_estimated_landed_cost_voucher",
                        args: { purchase_receipt: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Calculating estimated landed cost..."),
                        callback(r) {
                            if (!r.exc && r.message) {
                                frappe.set_route("Form", "Landed Cost Voucher", r.message);
                            }
                        },
                    });
                },
                __("Create")
            );
        }

        frm.add_custom_button(__("Landed Cost Voucher (Actual)"), () => {
            frappe.confirm(
                __("This removes the existing Landed Cost Vouchers of this receipt and creates a new one. Continue?"),
                () => {
                    frappe.call({
                        method: "ksa_customizations.api.create_actual_landed_cost_voucher",
                        args: { purchase_receipt: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Creating Landed Cost Voucher..."),
                        callback(r) {
                            if (!r.exc && r.message) {
                                frappe.set_route("Form", "Landed Cost Voucher", r.message);
                            }
                        },
                    });
                }
            );
        }, __("Create"));
        cur_frm.remove_custom_button("Landed Cost Voucher", __("Create"))
    },
});
