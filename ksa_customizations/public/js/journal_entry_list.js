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

// Accounts table like the Journal Entry one: debit lines, then one credit line (against account) at the end.
// The credit is always the sum of the debits (on edit, add or remove).
function entries_table_field(fieldname, label, debit_rows, against_row) {
    return {
        fieldname,
        fieldtype: "Table",
        label,
        in_place_edit: true,
        data: [...debit_rows, { ...against_row, debit: 0, credit: 0, is_against: 1 }].map((row, i) => ({
            idx: i + 1,
            ...row,
        })),
        fields: [
            { fieldname: "account", fieldtype: "Link", options: "Account", label: __("Account"), in_list_view: 1, columns: 2, reqd: 1 },
            { fieldname: "account_ar", fieldtype: "Link", options: "Landed Cost Expense Category", label: __("Category (AR)"), in_list_view: 1, columns: 2 },
            { fieldname: "description", fieldtype: "Small Text", label: __("Description"), in_list_view: 1, columns: 2 },
            { fieldname: "debit", fieldtype: "Currency", label: __("Debit"), in_list_view: 1, columns: 2 },
            { fieldname: "credit", fieldtype: "Currency", label: __("Credit"), in_list_view: 1, columns: 2, read_only: 1 },
            { fieldname: "is_against", fieldtype: "Check", label: __("Against"), hidden: 1 },
        ],
    };
}

// Keep the credit line of the table last, with debit 0 and credit = sum of all debits.
function setup_entries_table(dialog, fieldname, against_row) {
    const field = dialog.fields_dict[fieldname];
    field.df.get_data = () => field.df.data;
    let against_account = against_row.account;

    const recalc = () => {
        const data = field.df.data || [];
        const against = data.find((row) => row.is_against);
        const lines = data.filter((row) => !row.is_against);
        if (against) against_account = against.account || against_account;

        const total = flt(lines.reduce((sum, row) => sum + flt(row.debit), 0), 2);
        const credit = against || { ...against_row, account: against_account, debit: 0, credit: 0, is_against: 1 };
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
    field.$wrapper.on("change click keyup", () => setTimeout(recalc, 200));
    return recalc;
}

function table_accounts(dialog, fieldname) {
    return dialog.fields_dict[fieldname].df.data.map((row) => ({
        account: row.account,
        account_ar: row.account_ar,
        debit: flt(row.debit),
        credit: flt(row.credit),
    }));
}

// Column widths (share of the space after the checkbox column)
function set_entries_column_widths(dialog) {
    const widths = { account: 50, account_ar: 15, description: 15, debit: 10, credit: 10 };
    $(`<style>${Object.entries(widths)
        .map(([fieldname, width]) =>
            `.landed-cost-dialog .grid-static-col[data-fieldname="${fieldname}"]
                { flex: ${width} 1 0% !important; max-width: none !important; }`)
        .join("\n")}</style>`).appendTo(dialog.$wrapper.addClass("landed-cost-dialog"));
}

// Warnings about the created journal entry (from create_landed_cost_journal_entry)
function journal_entry_warnings(m) {
    const warnings = [];
    if (!m.vendor) {
        // No Vendor with this VAT number: party_name / party_tax_id were left empty
        warnings.push(
            m.seller_tax_id
                ? __("No Vendor matches the seller's VAT number {0}. Please set the Party Name manually.", [
                    `<b>${frappe.utils.escape_html(m.seller_tax_id)}</b>`,
                ])
                : __("The seller's VAT number was not found in the invoice. Please set the Party Name manually.")
        );
    } else if (!m.vendor_name_matches) {
        // Vendor found by VAT number, but its name differs from the seller name on the invoice
        warnings.push(__("Vendor {0} was matched by VAT number {1}, but its name does not closely match the seller name on the invoice {2} (similarity {3}%). Please check the Party Name.", [
            `<b>${frappe.utils.escape_html(m.vendor_name)}</b>`,
            `<b>${frappe.utils.escape_html(m.seller_tax_id)}</b>`,
            `<b>${frappe.utils.escape_html(m.seller_name)}</b>`,
            m.vendor_name_score,
        ]));
    }
    if (!m.bill_no) {
        warnings.push(__("The invoice number was not found in the invoice. Please set the Bill No manually."));
    }
    if (!m.bill_date) {
        warnings.push(__("The invoice date was not found in the invoice. Please set the Bill Date manually and check the Posting Date (set to today)."));
    }
    return warnings;
}

function warnings_html(warnings) {
    return warnings.map((w) => `<b>${__("Warning")}:</b> ${w}`).join("<br>");
}

// Create the journal entries of the given tables one by one ({dialog, fieldname, index, label}),
// then show one message with all of them. Returns true only if all of them were created.
// A table already created (table.entry) is skipped, so retrying after an error does not duplicate it.
async function create_landed_cost_entries(result, tables) {
    const created = [];
    let failed = false;
    frappe.dom.freeze(__("Creating Journal Entries..."));
    try {
        for (const table of tables.filter((t) => !t.entry)) {
            const r = await frappe.call({
                method: "ksa_customizations.api.create_landed_cost_journal_entry",
                args: {
                    purchase_receipt: result.purchase_receipt,
                    accounts: table_accounts(table.dialog, table.fieldname),
                    file_url: result.file_url,
                    ...(table.index === null ? {} : { attachment_index: table.index }),
                },
            });
            if (!r || r.exc || !r.message) {
                failed = true;
                break;
            }
            table.entry = r.message;
            created.push({ table, entry: r.message });
        }
    } catch (e) {
        failed = true;
    } finally {
        frappe.dom.unfreeze();
    }
    if (!created.length) return !failed;

    cur_list && cur_list.refresh();
    const lines = created.map(({ table, entry }) => {
        const warnings = journal_entry_warnings(entry);
        return `<div style="margin-bottom: var(--margin-sm);">
            ${table.label}: ${frappe.utils.get_form_link("Journal Entry", entry.name, true)}
            ${warnings.length ? "<br>" + warnings_html(warnings) : ""}
        </div>`;
    });
    if (failed) {
        lines.push(`<div class="text-danger">${__("The remaining entries were not created because of an error. Fix it and click Create again; the entries above will not be created twice.")}</div>`);
    }
    const any_warning = failed || created.some(({ entry }) => journal_entry_warnings(entry).length);
    frappe.msgprint({
        title: __("Operation completed"),
        indicator: any_warning ? "orange" : "green",
        message: __("Journal Entries created as drafts:") + "<br><br>" + lines.join(""),
    });
    return !failed;
}

// First preview: the main invoice. If the PDF has other invoices with VAT, Next opens the second preview;
// otherwise it creates the journal entry directly.
function show_landed_cost_entries_dialog(result) {
    const esc = (value) => frappe.utils.escape_html(value || "");
    const returned_vats = result.returned_vats || [];
    const against_row = { account: result.against_account, account_ar: "", description: "" };
    let vat_dialog = null;

    const dialog = new frappe.ui.Dialog({
        title: __("Landed Cost Entries"),
        size: "extra-large",
        fields: [
            { fieldname: "buyer_check", fieldtype: "HTML", options: buyer_check_html(result.buyer_check) },
            entries_table_field(
                "accounts",
                __("Accounting Entries"),
                result.rows.map((row) => ({
                    account: row.account || row.expense_account,
                    account_ar: row.account_ar,
                    description: row.description,
                    debit: flt(row.value),
                    credit: 0,
                })),
                against_row
            ),
        ],
        primary_action_label: returned_vats.length ? __("Next") : __("Create Journal Entry"),
        async primary_action() {
            if (returned_vats.length) {
                dialog.hide();
                vat_dialog = vat_dialog || make_returned_vats_dialog(result, main_table, dialog);
                vat_dialog.show();
                return;
            }
            if (await create_landed_cost_entries(result, [main_table])) dialog.hide();
        },
    });
    const main_table = { dialog, fieldname: "accounts", index: null,
        label: __("Main Invoice {0}", [esc(result.invoice_no)]) };

    const recalc = setup_entries_table(dialog, "accounts", against_row);
    set_entries_column_widths(dialog);
    dialog.show();
    recalc();
}

// Second preview: one table per other invoice in the PDF that charges VAT (the Tax account debited against
// the invoice's account), each with a checkbox. Creates the main entry and the checked VAT entries.
function make_returned_vats_dialog(result, main_table, main_dialog) {
    const esc = (value) => frappe.utils.escape_html(value || "");
    const vat_account = result.vat_account || {};
    const returned_vats = result.returned_vats;
    const tables = [];
    const total_vat = returned_vats.reduce((sum, vat) => sum + flt(vat.vat), 0);

    const fields = [{
        fieldname: "found_vats",
        fieldtype: "HTML",
        options: `<div style="padding: 8px 12px; margin-bottom: var(--margin-sm); background: var(--subtle-fg);
                border-inline-start: 3px solid var(--blue-500); border-radius: var(--border-radius);">
            ${__("We found {0} other invoice(s) with VAT in this PDF (total VAT {1}).", [
                `<b>${returned_vats.length}</b>`, `<b>${format_currency(total_vat)}</b>`,
            ])}<br>
            ${__("Check the ones you want to create a Journal Entry for. The main invoice entry will be created too.")}
        </div>`,
    }];
    if (!vat_account.account) {
        fields.push({
            fieldname: "vat_account_missing",
            fieldtype: "HTML",
            options: `<div class="text-danger" style="margin-bottom: var(--margin-sm);">
                ${__("No Landed Cost Expense Category with Category (EN) = Tax has an expense account. Please choose the VAT account in each table.")}
            </div>`,
        });
    }

    returned_vats.forEach((vat, i) => {
        const fieldname = `vat_accounts_${i}`;
        const check = `create_vat_${i}`;
        // the invoice's description goes on its own account (the credit line), not on the VAT account
        const against_row = { account: vat.account || vat.expense_account, account_ar: vat.account_ar,
            description: vat.description };
        tables.push({ fieldname, check, against_row, index: i,
            label: __("VAT Invoice {0}", [esc(vat.invoice_no) || i + 1]) });

        fields.push(
            { fieldtype: "Section Break", label: __("VAT Invoice {0}", [i + 1]) },
            {
                fieldname: `vat_info_${i}`,
                fieldtype: "HTML",
                options: `<div style="font-size: var(--text-sm); margin-bottom: var(--margin-sm);">
                    <b>${__("Invoice No")}:</b> ${esc(vat.invoice_no) || "-"} &nbsp;
                    <b>${__("Date")}:</b> ${esc(vat.invoice_date) || "-"} &nbsp;
                    <b>${__("Seller")}:</b> ${esc(vat.seller_name) || "-"} &nbsp;
                    <b>${__("VAT")}:</b> ${format_currency(flt(vat.vat))}
                </div>`,
            },
            { fieldname: check, fieldtype: "Check", label: __("Create Journal Entry"), default: 1 },
            entries_table_field(
                fieldname,
                __("Accounting Entries"),
                [{
                    account: vat_account.account,
                    account_ar: vat_account.account_ar,
                    description: "",
                    debit: flt(vat.vat),
                    credit: 0,
                }],
                against_row
            )
        );
    });

    const dialog = new frappe.ui.Dialog({
        title: __("VAT of Other Invoices"),
        size: "extra-large",
        fields,
        primary_action_label: __("Create Journal Entries"),
        async primary_action() {
            const selected = tables.filter((table) => dialog.get_value(table.check));
            if (await create_landed_cost_entries(result, [main_table, ...selected])) dialog.hide();
        },
        secondary_action_label: __("Back"),
        secondary_action() {
            dialog.hide();
            main_dialog.show();
        },
    });
    tables.forEach((table) => (table.dialog = dialog));

    const recalcs = tables.map((table) => setup_entries_table(dialog, table.fieldname, table.against_row));
    set_entries_column_widths(dialog);
    // recalculate once the dialog is visible (the grids render on show)
    dialog.$wrapper.one("shown.bs.modal", () => recalcs.forEach((recalc) => recalc()));
    return dialog;
}
