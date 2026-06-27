// Copyright (c) 2026, Mobility Pro DMCC and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Goal Template", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Goal Template KRA', {
    kra: function(frm) {
        let options = frm.doc.kra.map(k => k.kra);
        frm.fields_dict["goals"].grid.update_docfield_property("kra_group", "options", options);
    }
});

frappe.ui.form.on('Goal Template', {
    validate: function(frm) {
        let kraSum = frm.doc.kra.reduce((sum, item) => sum + (item.weight || 0), 0);
        if (kraSum !== 100) {
            frappe.throw(__('Total weightage of all KRAs must equal 100%. Currently it is {0}%.', [kraSum]));
        }
    }
})