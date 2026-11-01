frappe.ui.form.on('Appraisal', {
    refresh: function(frm) {
        frm.remove_custom_button(__("View Goals"));
        frm.add_custom_button(__("View Goals"), function() {
			const filters = {
				company: frm.doc.company,
				employee: frm.doc.employee,
				appraisal_cycle: frm.doc.appraisal_cycle,
                is_group: 0
			};
			frappe.route_options = Object.assign({}, filters);
			frappe.set_route("List", "Goal", "Report", "Goal").then(() => {
				// A saved Report view ignores route_options once it has been loaded,
				// so re-apply the filters to replace the previous appraisal's values
				if (!cur_list || cur_list.doctype !== "Goal") return;
				const filter_area = cur_list.filter_area;
				const fields_dict = cur_list.page.fields_dict;
				const non_standard_filters = [];
				Object.entries(filters).forEach(([fieldname, value]) => {
					if (fields_dict[fieldname]) {
						fields_dict[fieldname].set_value(value);
					} else {
						filter_area.remove(fieldname);
						non_standard_filters.push(["Goal", fieldname, "=", value]);
					}
				});
				filter_area.add(non_standard_filters);
			});
        });

        frm.remove_custom_button(__("Reset Goals and KRAs"));
        if (!frm.is_new() && frm.doc.docstatus === 0 && frappe.user.has_role("HR Manager")) {
            frm.add_custom_button(__("Reset Goals and KRAs"), function() {
                frappe.confirm(
                    __("This will delete all Goals of {0} for Appraisal Cycle {1} and rebuild the KRAs and Goals from the Goal Template. Any progress recorded on the existing Goals will be lost. Do you want to continue?",
                        [frm.doc.employee_name.bold(), frm.doc.appraisal_cycle.bold()]),
                    function() {
                        frm.call({
                            doc: frm.doc,
                            method: "reset_goals_and_kras",
                            freeze: true,
                            freeze_message: __("Resetting Goals and KRAs..."),
                        }).then(() => {
                            frm.reload_doc();
                            frappe.show_alert({ message: __("Goals and KRAs have been reset"), indicator: "green" });
                        });
                    }
                );
            });
        }
    }
})
