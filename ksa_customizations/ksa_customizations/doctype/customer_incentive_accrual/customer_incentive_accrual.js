// Copyright (c) 2026, Mobility Pro DMCC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Incentive Accrual", {
	calculate_total_amount(frm) {
		let total = 0;
		(frm.doc.details || []).forEach((row) => {
			total += flt(row.amount);
		});
		frm.set_value("total_amount", total);
	},
});

frappe.ui.form.on("Customer Incentive Accrual Detail", {
	amount(frm) {
		frm.events.calculate_total_amount(frm);
	},
});
