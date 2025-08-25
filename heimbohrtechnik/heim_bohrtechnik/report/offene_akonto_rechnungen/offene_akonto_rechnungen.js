// Copyright (c) 2022-2025, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Offene Akonto-Rechnungen"] = {
    "filters": [
        {
            "fieldname":"sales_order",
            "label": __("Sales Order"),
            "fieldtype": "Link",
            "options": "Sales Order"
        }
    ],
    "onload": (report) => {
        report.page.add_inner_button( __("Abgrenzung erstellen"), function() {
            create_accrual_booking();
        });
    }
};

function create_accrual_booking() {
    let accrual_amount = 0;
    let invoices = [];
    let today = frappe.datetime.get_today();
    for (let i = 0; i < (frappe.query_report.data || []).length; i++) {
        if (frappe.query_report.data[i].expected_end_date < today) {
            accrual_amount += frappe.query_report.data[i].amount;
            invoices.push(frappe.query_report.data[i]);
        }
    }
    let currency = "CHF";
    if (frappe.query_report.data.length > 0) {
        frappe.query_report.data[0].currency;
    }
    let d = new frappe.ui.Dialog({
        'title': __("Abgrenzung erstellen"),
        'fields': [
            {
                'fieldname': 'accrual_date',
                'fieldtype': 'Date',
                'label': __("Accrual Date"),
                'default': frappe.datetime.get_today(),
                'onchange': function() {
                    console.log("onchange " + d.get_value('accrual_date'));
                    d.set_value("resolution_date", frappe.datetime.add_days(d.get_value('accrual_date'), 1));
                }
            },
            {
                'fieldname': 'resolution_date',
                'fieldtype': 'Date',
                'label': __("Resolution Date"),
                'default': frappe.datetime.add_days(frappe.datetime.get_today(), 1)
            },
            {
                'fieldname': 'accrual_account',
                'fieldtype': 'Link',
                'options': 'Account',
                'label': __("Accrual Account"),
                'default': "1280 - Angefangene Arbeiten - HBAG"
            },
            {
                'fieldname': 'revenue_account',
                'fieldtype': 'Link',
                'options': 'Account',
                'label': __("Revenue Account"),
                'default': "3000 - Erlös Bohrungen - HBAG"
            },
            {
                'fieldname': 'amount',
                'fieldtype': 'Currency',
                'options': 'currency',
                'label': __("Amount"),
                'read_only': 1,
                'default': accrual_amount
            },
            {
                'fieldname': 'currency',
                'fieldtype': 'Link',
                'options': 'Currency',
                'label': __("Currency"),
                'hidden': 1,
                'default': currency
            }
        ],
        'primary_action': function() {
            d.hide();
            let values = d.get_values();
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.report.offene_akonto_rechnungen.offene_akonto_rechnungen.create_accrual',
                'args': {
                    'accrual_date': values.accrual_date,
                    'resolution_date': values.resolution_date,
                    'accrual_account': values.accrual_account,
                    'revenue_account': values.revenue_account,
                    'amount': values.amount,
                    'currency': values.currency,
                    'invoices': invoices
                },
                'callback': function(response) {
                    frappe.show_alert( __("Erstellt") + " " + response.message );
                }
            });
        },
        'primary_action_label': __("OK")
    });
    d.show();
}
