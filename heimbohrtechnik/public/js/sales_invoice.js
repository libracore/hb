// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
    object: function(frm) {
        get_object_address(frm);
        get_project_description(frm);
    },
    refresh: function(frm) {
        // fetch sales invoice object text if new document and has object
        if ((frm.doc.__islocal) && (frm.doc.object)) {
            get_project_description(frm);
        }
        
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
    },
    before_save: function(frm) {
        set_conditional_net_total(frm);
        recalculate_markups_discounts(frm);
        
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
        
        // check and apply accrual
        check_warranty(frm);
    },
    after_cancel: function(frm) {
        // if this is a MudEX invoice to HB, cancel related invoice
        if ((frm.doc.company.includes("MudEX")) && (frm.doc.customer === "K-00010")) {
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.utils.cancel_mudex_invoice',
                'args': {
                    'reference': frm.doc.name
                },
                'callback': function(r) {
                    if (r.message) {
                        frappe.show_alert(r.message + " wurde auch storniert");
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Discount Position', {
    discount: function(frm, dt, dn) {
        update_additional_discount(frm);
    },
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});

frappe.ui.form.on('Markup Position', {
    discount: function(frm, dt, dn) {
        update_additional_discount(frm);
    },
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});
