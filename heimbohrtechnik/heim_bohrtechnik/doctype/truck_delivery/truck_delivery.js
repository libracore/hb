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
        // make sure there is an object row
        if ((!frm.doc.objects) || (frm.doc.objects.length < 1)) {
            var child = cur_frm.add_child('objects');
            cur_frm.refresh_field('objects');
        }
    },
    full_weight: function(frm) {
        update_net_weight(frm);
    },
    empty_weight: function(frm) {
        update_net_weight(frm);
    },
    truck: function(frm) {
        if ((frm.doc.truck) && ((!frm.doc.empty_weight) || (frm.doc.empty_weight === 0))) { 
            fetch_truck_net_weight(frm); 
        }
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
                cur_frm.set_value(target, r.message.weight);
                // add trace
                var child = cur_frm.add_child('trace');
                frappe.model.set_value(child.doctype, child.name, 'date', get_now());
                frappe.model.set_value(child.doctype, child.name, 'scale', frm.doc.truck_scale);
                frappe.model.set_value(child.doctype, child.name, 'weight', r.message.weight);
                frappe.model.set_value(child.doctype, child.name, 'process_id', r.message.process_id);
                cur_frm.refresh_field('trace');
                cur_frm.save();
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

function fetch_truck_net_weight(frm) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Truck",
            'name': frm.doc.truck
        },
        'callback': function(response) {
            var truck = response.message;

            if ((truck) && (truck.net_weight)) {
                cur_frm.set_value('empty_weight', truck.net_weight);
            } 
        }
    });
}
