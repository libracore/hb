// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Order', {
    object: function(frm) {
        get_object_address(frm);
        get_object_description(frm);
    },
    before_save: function(frm) {
        set_conditional_net_total(frm);
        recalculate_markups_discounts(frm);
    },
    refresh: function(frm) {
        if (frm.doc.object) {
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    'doctype': "Object",
                    'name': frm.doc.object
                },
                'callback': function(response) {
                    var object = response.message;
                    // button to create truck link
                    frm.add_custom_button("<i class='fa fa-truck'></i> Link", function() {
                        create_delivery_link(object.name, object.object_key, true);
                    }, "MudEX");
                    // button to create truck QR code
                    frm.add_custom_button("<i class='fa fa-truck'></i> QR-Code", function() {
                        create_delivery_link(object.name, object.object_key, false);
                    }, "MudEX");
                }
            });
            // check if mud can be invoiced
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.truck_delivery.truck_delivery.has_invoiceable_mud',
                'args': {'object': frm.doc.object},
                'callback': function(response) {
                    if (response.message) {
                        frm.add_custom_button( __("Abrechnen"), function() {
                            create_mud_invoice(frm.doc.object);
                        }, "MudEX");
                    }
                }
            });
        }
    }
});

frappe.ui.form.on('Discount Position', {
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});
