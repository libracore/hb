// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Request for Public Area Use', {
    object: function(frm) {
        if (frm.doc.object) {
            fetch_object_details(frm.doc.object);
        }
    }
});

function fetch_object_details(obj) {
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "Object",
            "name": obj
        },
        "callback": function(response) {
            var object = response.message;
            cur_frm.set_value("object_name", object.object_name);
            cur_frm.set_value("object_street", object.object_street);
            cur_frm.set_value("object_location", object.object_location);
        }
    });
}
