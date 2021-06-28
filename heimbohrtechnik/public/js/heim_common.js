// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
// Common functions

function get_object_address(frm) {
    if (frm.doc.object) {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Object",
                'name': frm.doc.object
            },
            'callback': function(response) {
                var object = response.message;

                if (object) {
                    cur_frm.set_value('object_address_display', object.object_street + "<br>" + object.object_location);
                } 
            }
        });
    }
}

function get_object_description(frm) {
    if (frm.doc.object) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.utils.get_object_description",
            'args': {
                'object_name': frm.doc.object
            },
            'callback': function(response) {
                var html = response.message;

                if (html) {
                    cur_frm.set_value('object_description', html);
                } 
            }
        });
    }
}

function update_additional_discount(frm) {
    if (frm.doc.discount_positions) {
        var additional_discount = 0;
        for (var i = 0; i < frm.doc.discount_positions.length; i++) {
            additional_discount += frm.doc.discount_positions[i].discount;
        }
        if (frm.doc.total !== 0 ) {
            cur_frm.set_value("additional_discount_percentage", (100 * additional_discount) / frm.doc.total);
        } else {
            cur_frm.set_value("discount_amount", additional_discount);
        }
    }
}

function get_required_activities(frm, dt, dn) {
    var v = locals[dt][dn];
    if (v.supplier) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.filters.get_required_activities",
            'args': {
                'supplier': v.supplier,
                'activity': v.activity
            },
            'callback': function(response) {
                var activities = response.message;
                for (var i = 0; i < activities.length; i++) {
                    for (var r = 0; r < frm.doc.checklist.length; r++) {
                        if (frm.doc.checklist[r].activity === activities[i]) {
                            frappe.model.set_value(frm.doc.checklist[r].doctype, frm.doc.checklist[r].name, 
                                'supplier', v.supplier);
                            frappe.model.set_value(frm.doc.checklist[r].doctype, frm.doc.checklist[r].name, 
                                'supplier_name', v.supplier_name);
                        }
                    }
                }
                
                cur_frm.refresh_field('addresses');
            }
        });
    } else {
        frappe.model.set_value(v.doctype, v.name, "supplier_name", null);
    }
}

function prepare_checklist_and_permits(frm) {
    if ((!frm.doc.permits) || (frm.doc.permits.length === 0)) {
        // no permits, load standards
        frappe.call({
            "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_standard_permits",
            "callback": function(response) {
                var standard_permits = response.message;
                for (var i = 0; i < standard_permits.length; i++) {
                    var child = cur_frm.add_child('permits');
                    frappe.model.set_value(child.doctype, child.name, 'permit', standard_permits[i]);
                }
                cur_frm.refresh_field('permits');
            }
        });
    }
    if ((!frm.doc.checklist) || (frm.doc.checklist.length === 0)) {
        // no checklist positions, load standards
        frappe.call({
            "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_standard_activities",
            "callback": function(response) {
                var standard_activities = response.message;
                for (var i = 0; i < standard_activities.length; i++) {
                    var child = cur_frm.add_child('checklist');
                    frappe.model.set_value(child.doctype, child.name, 'activity', standard_activities[i]);
                }
                cur_frm.refresh_field('checklist');
            }
        });
    }
}
