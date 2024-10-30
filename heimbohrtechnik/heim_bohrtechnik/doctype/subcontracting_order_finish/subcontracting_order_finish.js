// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subcontracting Order Finish', {
    refresh: function(frm) {
        frm.add_custom_button( __("Sonden holen"), function() 
            {
                fetch_probes(frm);
            }
        );
    },
    subcontracting_order: function(frm) {
        if (frm.doc.subcontracting_order) {
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    'doctype': "Subcontracting Order",
                    'name': frm.doc.subcontracting_order
                },
                'callback': function(response) {
                    var order = response.message;
                    cur_frm.set_value("team", order.drilling_team);
                    cur_frm.set_value("project", order.project);
                    cur_frm.set_value("object", order.object);
                    cur_frm.set_value("object_name", order.object_name);
                    cur_frm.set_value("object_street", order.object_street);
                    cur_frm.set_value("object_location", order.object_location);
                }
            });
        }
    }
});

function fetch_probes(frm) {
    if (frm.doc.object) {
        frappe.call({
            "method": "frappe.client.get",
            "args": {
                "doctype": "Object",
                "name": frm.doc.object
            },
            "callback": function(response) {
                let obj = response.message;
                let probes = [];
                let id = 1;
                for (let i = 0; i < obj.ews_specification.length; i++) {
                    for (let j = 0; j < obj.ews_specification[i].ews_count; j++) {
                        probes.push({
                            'id': id,
                            'depth': obj.ews_specification[i].ews_depth,
                            'dimension': obj.ews_specification[i].ews_dimension,
                            'pressure_level': obj.ews_specification[i].pressure_level,
                            'probe_type': obj.ews_specification[i].probe_type,
                        });
                        id++;
                    }
                }
                
                add_probes(probes);
            }
        });
    }
}

function add_probes(probes) {
    cur_frm.clear_table("probes");
    for (let i = 0; i < probes.length; i++) {
        let child = cur_frm.add_child('probes');
        frappe.model.set_value(child.doctype, child.name, 'id', probes[i].id);
        frappe.model.set_value(child.doctype, child.name, 'depth', probes[i].depth);
    }
    cur_frm.refresh_field('probes');
}
