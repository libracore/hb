// Copyright (c) 2021-2026, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delivery Note', {
    'object': function(frm) {
        get_object_address(frm);
    }, 
    'before_save': function(frm) {
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
    },
    'refresh': function(frm) {
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
        
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button( __("Verfügbare Lager holen") , function() {
                get_available_warehouses(frm);
            });
        }
        
        // remove obsolete menu items
        setTimeout(function() {
            $("a[data-label='" + encodeURI(__("Packing Slip")) + "']").parent().remove();
            $("a[data-label='" + encodeURI(__("Installation Note")) + "']").parent().remove();
            $("a[data-label='" + encodeURI(__("Sales Return")) + "']").parent().remove();
            $("a[data-label='" + encodeURI(__("Delivery Trip")) + "']").parent().remove();
            $("a[data-label='" + encodeURI(__("Subscription")) + "']").parent().remove();
        }, 1000);
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

function get_available_warehouses(frm) {
    for (let i = 0; i < frm.doc.items.length; i++) {
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.utils.get_available_warehouse',
            'args': {
                'item_code': frm.doc.items[i].item_code,
                'company': frm.doc.company
            },
            'callback': function(response) {
                if (response.message) {
                    frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, 'warehouse', response.message);
                }
            }
        });
    }
}
