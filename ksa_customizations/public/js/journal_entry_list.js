// Extends the standard Journal Entry list view (does not replace ERPNext's settings)
frappe.listview_settings["Journal Entry"] = frappe.listview_settings["Journal Entry"] || {};

const je_list_settings = frappe.listview_settings["Journal Entry"];
const original_onload = je_list_settings.onload;

je_list_settings.onload = function (listview) {
    if (original_onload) original_onload.call(this, listview);

    listview.page.add_inner_button(__("Upload Landed Cost Invoice"), () => {
        show_landed_cost_upload_dialog(listview);
    });
};

function show_landed_cost_upload_dialog(listview) {
    const dialog = new frappe.ui.Dialog({
        title: __("Upload Landed Cost Invoice"),
        fields: [
            {
                fieldname: "file",
                fieldtype: "Attach",
                label: __("File"),
                reqd: 1,
                options: { restrictions: { allowed_file_types: [".pdf"] } },
            },
            {
                fieldname: "against_account",
                fieldtype: "Link",
                label: __("Against Account"),
                options: "Account",
                reqd: 1,
            },
            {
                fieldname: "purchase_receipt",
                fieldtype: "Link",
                label: __("Purchase Receipt"),
                options: "Purchase Receipt",
                reqd: 1,
            },
        ],
        primary_action_label: __("Upload"),
        primary_action(values) {
            // The server reports each step into the cache; poll it so the progress bar always shows
            const progress_id = frappe.utils.get_random(12);
            const title = __("Reading PDF");
            const poll = setInterval(() => {
                frappe.call({
                    method: "ksa_customizations.api.get_upload_progress",
                    args: { progress_id },
                    no_spinner: true,
                    callback(r) {
                        const p = r.message;
                        if (p && p.message) frappe.show_progress(title, p.percent, 100, p.message, true);
                    },
                });
            }, 1000);
            frappe.show_progress(title, 1, 100, __("Uploading file..."), true);

            frappe.call({
                method: "ksa_customizations.api.upload_landed_cost_file",
                args: {
                    file_url: values.file,
                    against_account: values.against_account,
                    purchase_receipt: values.purchase_receipt,
                    progress_id,
                },
                callback(r) {
                    clearInterval(poll);
                    frappe.hide_progress();
                    if (!r.exc && r.message) {
                        dialog.hide();
                        show_landed_cost_entries_dialog(r.message);
                    }
                },
                error() {
                    clearInterval(poll);
                    frappe.hide_progress();
                },
            });
        },
    });
    dialog.show();
}

// Status of the invoice's buyer compared with the Purchase Receipt's Company (from api.check_buyer)
function buyer_check_html(check) {
    if (!check) return "";
    const esc = (value) => frappe.utils.escape_html(value || "");
    const STATUS = {
        match: ["green", __("Match")],
        mismatch: ["red", __("Mismatch")],
        missing: ["orange", __("Not Found")],
    };
    // One line per check: status, then invoice value vs company value (shown in full only when they differ)
    const line = (label, status, invoice_value, company_value, note = "") => {
        const [color, text] = STATUS[status];
        const detail = status === "match"
            ? esc(invoice_value)
            : `${esc(invoice_value) || "-"} <span class="text-muted">≠ ${__("Company")}:</span> ${esc(company_value) || "-"}`;
        return `<div class="ellipsis"><span class="indicator ${color}"></span>
            <b>${label}:</b> ${text}${note} — ${detail}</div>`;
    };
    const name_note = check.name_status === "mismatch" ? ` (${check.name_score}%)` : "";
    const any_bad = check.name_status === "mismatch" || check.vat_status === "mismatch";
    const all_ok = check.name_status === "match" && check.vat_status === "match";
    const border = all_ok ? "var(--green-500)" : any_bad ? "var(--red-500)" : "var(--orange-500)";

    return `<div style="font-size: var(--text-sm); padding: 6px 10px; margin-bottom: var(--margin-sm);
                border-inline-start: 3px solid ${border}; background: var(--subtle-fg); border-radius: var(--border-radius);">
        ${line(__("Buyer Name"), check.name_status, check.buyer_name, check.company_name, name_note)}
        ${line(__("Buyer VAT ID"), check.vat_status, check.buyer_vat_id, check.company_vat_id)}
    </div>`;
}

function show_landed_cost_entries_dialog(result) {
    // Like the Journal Entry accounts table: debit lines, then one credit line (against account) at the end.
    const debit_rows = result.rows.map((row) => ({
        account: row.account || row.expense_account,
        account_ar: row.account_ar,
        description: row.description,
        debit: flt(row.value),
        credit: 0,
    }));
    const credit_row = () => ({
        account: result.against_account,
        account_ar: "",
        description: "",
        debit: 0,
        credit: 0,
        is_against: 1,
    });

    const dialog = new frappe.ui.Dialog({
        title: __("Landed Cost Entries"),
        size: "extra-large",
        fields: [
            {
                fieldname: "buyer_check",
                fieldtype: "HTML",
                options: buyer_check_html(result.buyer_check),
            },
            {
                fieldname: "accounts",
                fieldtype: "Table",
                label: __("Accounting Entries"),
                in_place_edit: true,
                data: [...debit_rows, credit_row()].map((row, i) => ({ idx: i + 1, ...row })),
                get_data: () => dialog.fields_dict.accounts.df.data,
                fields: [
                    { fieldname: "account", fieldtype: "Link", options: "Account", label: __("Account"), in_list_view: 1, columns: 2, reqd: 1 },
                    { fieldname: "account_ar", fieldtype: "Data", label: __("Category (AR)"), in_list_view: 1, columns: 2 },
                    { fieldname: "description", fieldtype: "Small Text", label: __("Description"), in_list_view: 1, columns: 2 },
                    { fieldname: "debit", fieldtype: "Currency", label: __("Debit"), in_list_view: 1, columns: 2 },
                    { fieldname: "credit", fieldtype: "Currency", label: __("Credit"), in_list_view: 1, columns: 2, read_only: 1 },
                    { fieldname: "is_against", fieldtype: "Check", label: __("Against"), hidden: 1 },
                ],
            },
        ],
        primary_action_label: __("Next"),
        primary_action() {
            const accounts = dialog.fields_dict.accounts.df.data.map((row) => ({
                account: row.account,
                account_ar: row.account_ar,
                debit: flt(row.debit),
                credit: flt(row.credit),
            }));
            frappe.call({
                method: "ksa_customizations.api.create_landed_cost_journal_entry",
                args: {
                    purchase_receipt: result.purchase_receipt,
                    accounts,
                    file_url: result.file_url,
                },
                freeze: true,
                freeze_message: __("Creating Journal Entry..."),
                callback(r) {
                    if (r.exc || !r.message) return;
                    dialog.hide();
                    let message = __("Operation completed. Journal Entry {0} was created as a draft.", [
                        frappe.utils.get_form_link("Journal Entry", r.message.name, true),
                    ]);
                    const warnings = [];
                    if (!r.message.vendor) {
                        // No Vendor with this VAT number: party_name / party_tax_id were left empty
                        warnings.push(
                            r.message.seller_tax_id
                                ? __("No Vendor matches the seller's VAT number {0}. Please set the Party Name manually.", [
                                    `<b>${frappe.utils.escape_html(r.message.seller_tax_id)}</b>`,
                                ])
                                : __("The seller's VAT number was not found in the invoice. Please set the Party Name manually.")
                        );
                    } else if (!r.message.vendor_name_matches) {
                        // Vendor found by VAT number, but its name differs from the seller name on the invoice
                        warnings.push(__("Vendor {0} was matched by VAT number {1}, but its name does not closely match the seller name on the invoice {2} (similarity {3}%). Please check the Party Name.", [
                            `<b>${frappe.utils.escape_html(r.message.vendor_name)}</b>`,
                            `<b>${frappe.utils.escape_html(r.message.seller_tax_id)}</b>`,
                            `<b>${frappe.utils.escape_html(r.message.seller_name)}</b>`,
                            r.message.vendor_name_score,
                        ]));
                    }
                    if (!r.message.bill_no) {
                        warnings.push(__("The invoice number was not found in the invoice. Please set the Bill No manually."));
                    }
                    if (!r.message.bill_date) {
                        warnings.push(__("The invoice date was not found in the invoice. Please set the Bill Date manually and check the Posting Date (set to today)."));
                    }
                    if (warnings.length) {
                        message += "<br><br>" + warnings.map((w) => `<b>${__("Warning")}:</b> ${w}`).join("<br>");
                    }
                    const indicator = warnings.length ? "orange" : "green";
                    frappe.msgprint({ title: __("Operation completed"), indicator, message });
                    cur_list && cur_list.refresh();
                },
            });
        },
    });

    // Keep the credit line last, with debit 0 and credit = sum of all debits (on edit, add or remove).
    let against_account = result.against_account;
    const recalc = () => {
        const field = dialog.fields_dict.accounts;
        const data = field.df.data || [];
        const against = data.find((row) => row.is_against);
        const lines = data.filter((row) => !row.is_against);
        if (against) against_account = against.account || against_account;

        const total = flt(lines.reduce((sum, row) => sum + flt(row.debit), 0), 2);
        const credit = against || { ...credit_row(), account: against_account };
        const credit_changed = !against || flt(credit.credit) !== total || flt(credit.debit) !== 0;
        credit.debit = 0;
        credit.credit = total;

        const ordered = [...lines, credit];
        const reordered = ordered.length !== data.length || ordered.some((row, i) => data[i] !== row);
        ordered.forEach((row, i) => (row.idx = i + 1));
        field.df.data = ordered;
        // rebuild the grid only when needed, so typing in a cell is not interrupted
        if (reordered || credit_changed) {
            field.grid.df.data = ordered;
            field.grid.refresh();
        }
    };
    dialog.fields_dict.accounts.$wrapper.on("change click keyup", () => setTimeout(recalc, 200));

    // Column widths (share of the space after the checkbox column)
    const widths = { account: 50, account_ar: 15, description: 15, debit: 10, credit: 10 };
    $(`<style>${Object.entries(widths)
        .map(([fieldname, width]) =>
            `.landed-cost-dialog .grid-static-col[data-fieldname="${fieldname}"]
                { flex: ${width} 1 0% !important; max-width: none !important; }`)
        .join("\n")}</style>`).appendTo(dialog.$wrapper.addClass("landed-cost-dialog"));

    dialog.show();
    recalc();
}
