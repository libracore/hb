// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subcontracting Order Finish', {
    refresh: function(frm) {

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
