// Copyright (c) 2026, Mobility Pro DMCC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tire Claim Reconciliation", {
	onload(frm) {
		frm.set_query("tire_claims", () => {
			return {
				filters: {
					selected: 0,
					docstatus: ["!=", 2],
				},
			};
		});
	},
});
