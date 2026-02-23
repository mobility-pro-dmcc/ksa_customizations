// Copyright (c) 2026, Mobility Pro DMCC and contributors
// For license information, please see license.txt

frappe.ui.form.on("Marketing Credit Note", {
    refresh(frm) {
        render_commission_table(frm);
    }
});

function render_commission_table(frm) {
    let data = JSON.parse(frm.doc.commision_json) || [];

    if (!data.length) {
        frm.fields_dict.commision_table.$wrapper.html("<p>No data</p>");
        return;
    }

    let html = `
        <table class="table table-bordered table-sm">
            <thead>
                <tr>
                    <th>Item</th>
                    <th>Production Year</th>
                    <th class="text-right">Net Amount</th>
                    <th class="text-right">Commission</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.forEach(row => {
        html += `
            <tr>
                <td>${row.item_code || ""}</td>
                <td>${row.production_year || ""}</td>
                <td class="text-right">${format_currency(row.net_amount)}</td>
                <td class="text-right">${format_currency(row.commission_amount)}</td>
            </tr>
        `;
    });

    html += "</tbody></table>";

    frm.fields_dict.commision_table.$wrapper.html(html);
}
