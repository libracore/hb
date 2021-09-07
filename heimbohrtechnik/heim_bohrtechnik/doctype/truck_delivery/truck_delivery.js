// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Truck Delivery', {
    refresh: function(frm) {
        if (!frm.doc.date) {
            // fetch current timestamp if empty
            cur_frm.set_value("date", new Date());
        }
        if ((frm.doc.docstatus === 0) && (frm.doc.truck_scale)) {
            frm.add_custom_button( __("Full Weight"), function() {
                get_weight(frm, 'full_weight')
            }).addClass("btn-primary");
            frm.add_custom_button( __("Empty Weight"), function() {
                get_weight(frm, 'empty_weight')
            }).addClass("btn-primary");
        }
    },
    full_weight: function(frm) {
        update_net_weight(frm);
    },
    empty_weight: function(frm) {
        update_net_weight(frm);
    }
});

function get_weight(frm, target) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.truck_scale.truck_scale.get_weight',
        'args': {
            'truck_scale': frm.doc.truck_scale
        },
        'callback': function(r) {
            if (typeof r.message !== 'undefined') {
                cur_frm.set_value(target, r.message);
            } else {
                console.log("Invalid response");
            }
        }
    });
}

function update_net_weight(frm) {
    var full_weight = frm.doc.full_weight || 0;
    var empty_weight = frm.doc.empty_weight || 0;
    var net_weight = full_weight - empty_weight;
    cur_frm.set_value('net_weight', net_weight);
}
