// Copyright (c) 2026, Mobility Pro DMCC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payment Transfer Request", {
    refresh(frm) {

        if (frm.doc.owner !== frappe.session.user) {
            frm.disable_form();
        }

        frm.call("get_cash_accounts_for_user").then((r) => {
            let accounts = r.message || [];

            if (accounts.length) {
                frm.set_value("paid_from", accounts[0]);
            }
            
            frm.set_query("paid_from", function () {
                return {
                    filters: {
                        name: ["in", accounts]
                    }
                };
            });
        });
    }
});
