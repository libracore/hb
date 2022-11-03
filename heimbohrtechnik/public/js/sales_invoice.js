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
        
        // check duplicate discount
        if (frm.doc.docstatus === 0) {
            check_duplicate_discounts(frm);
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

function check_duplicate_discounts(frm) {
    var sales_order = null;
    for (var i = 0; i < frm.doc.items.length; i++) {
        if (frm.doc.items[i].sales_order) {
            sales_order = frm.doc.items[i].sales_order;
            break;
        }
    }
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_invoiced_markup_discounts",
        "args": {
            "sales_order": sales_order
        },
        "async": false,
        "callback": function(response) {
            var positions = response.message;
            console.log(positions);
            // check markups
            for (var m = frm.doc.markup_positions.length - 1; m >= 0; m--) {
                for (var i = 0; i < response.message.length; i++) {
                    if ((frm.doc.markup_positions[m].description === response.message[i].description)
                        && (response.message[i].parent !== frm.doc.name)) {
                        // already in another invoice - remove
                        cur_frm.get_field("markup_positions").grid.grid_rows[m].remove();
                        frappe.show_alert(__("Doppelten Zuschlag {0} entfernt").replace("{0}", frm.doc.markup_positions[m].description))
                        break;
                    }
                }
            }
            for (var m = frm.doc.discount_positions.length - 1; m >= 0; m--) {
                for (var i = 0; i < response.message.length; i++) {
                    if ((frm.doc.discount_positions[m].description === response.message[i].description)
                        && (response.message[i].parent !== frm.doc.name)) {
                        // already in another invoice - remove
                        cur_frm.get_field("discount_positions").grid.grid_rows[m].remove();
                        frappe.show_alert(__("Doppelten Abzug {0} entfernt").replace("{0}", frm.doc.discount_positions[m].description))
                        break;
                    }
                }
            }
            cur_frm.refresh_fields(["markup_positions", "discount_positions"]);
        }
    });
}
