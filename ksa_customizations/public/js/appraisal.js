frappe.ui.form.on('Appraisal', {
    refresh: function(frm) {
        frm.remove_custom_button(__("View Goals"));
        frm.add_custom_button(__("View Goals"), function() {
			frappe.route_options = {
				company: frm.doc.company,
				employee: frm.doc.employee,
				appraisal_cycle: frm.doc.appraisal_cycle,
			};
			frappe.set_route("Report", "Goal");
        });
    }
})