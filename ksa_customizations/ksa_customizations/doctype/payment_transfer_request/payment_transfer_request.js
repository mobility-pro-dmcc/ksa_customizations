// Copyright (c) 2026, Mobility Pro DMCC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Transfer Request', {
	refresh(frm) {
	    if(frm.doc.owner != frappe.session.user) {frm.disable_form()}

	    frappe.db.get_value("Contact", {user: frappe.session.user}, "is_sales_person", function(res){
          	if(res.is_sales_person){
        		frappe.db.get_list("Account", {filters:{custom_assigned_person: frappe.session.user, account_type:"Cash"}, pluck: "name"})
                .then(function(r){
                  	if(r.length){
                        frm.set_value("paid_from", r[0]);
                        frm.set_query("paid_from", function(){
                            return {
                                filters:{
                                    name: ["in", r]
                                }
                            };
                        });
                    }
                });
            }
        });
	}
});