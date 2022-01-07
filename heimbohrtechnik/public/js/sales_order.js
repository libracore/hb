// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

// extend dashboard
cur_frm.dashboard.add_transactions([
    {
        'label': 'Fulfillment',
        'items': ['Akonto Invoice']
    }
]);
        
frappe.ui.form.on('Sales Order', {
    object: function(frm) {
        get_object_address(frm);
        get_object_description(frm);
    },
    before_save: function(frm) {
        set_conditional_net_total(frm);
        recalculate_markups_discounts(frm);
        
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
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
                'method': 'heimbohrtechnik.mudex.doctype.truck_delivery.truck_delivery.has_invoiceable_mud',
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
        if (frm.doc.docstatus === 1) {
            // add create akonto function
            frm.add_custom_button(__("Akonto Invoice"),  function() { 
                create_akonto(frm);
            }, __("Create"));
            // remove obsolete menu items
            setTimeout(function() {
                $("a[data-label='" + encodeURI(__("Pick List")) + "']").parent().remove();
                $("a[data-label='" + encodeURI(__("Work Order")) + "']").parent().remove();
                $("a[data-label='" + encodeURI(__("Material Request")) + "']").parent().remove();
                $("a[data-label='" + encodeURI(__("Request for Raw Materials")) + "']").parent().remove();
                $("a[data-label='" + encodeURI(__("Purchase Order")) + "']").parent().remove();
                $("a[data-label='" + encodeURI(__("Project")) + "']").parent().remove();
                $("a[data-label='" + encodeURI(__("Subscription")) + "']").parent().remove();
                $("a[data-label='" + encodeURI(__("Payment Request")) + "']").parent().remove();
            }, 1000);
        }
        
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

function create_akonto(frm) {
    frappe.model.open_mapped_doc({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.create_akonto',
        'frm': frm
    });
}

