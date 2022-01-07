// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Note', {
    object: function(frm) {
        get_object_address(frm);
    }, 
    before_save: function(frm) {
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
    },
    refrehs: function(frm) {
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
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
