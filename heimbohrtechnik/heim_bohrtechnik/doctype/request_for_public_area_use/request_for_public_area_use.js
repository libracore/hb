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
            for (var a = 0; a < object.addresses.length; a++) {
                if (object.addresses[a].address_type === "Eigentümer") {
                    if (object.addresses[a].is_simple) {
                        cur_frm.set_value("address_name", object.addresses[a].simple_name);
                        var address_parts = object.addresses[a].simple_address.split(", ");
                        cur_frm.set_value("address_street", address_parts[0]);
                        if (address_parts.length > 1) {
                            cur_frm.set_value("address_location", address_parts[1]);
                        }
                    } else {
                        var address_parts = object.addresses[a].address_display.split("<br>");
                        cur_frm.set_value("address_name", object.addresses[a].party_name);
                        if (address_parts.length > 2) {
                            cur_frm.set_value("address_street", address_parts[0]);
                            cur_frm.set_value("address_location", address_parts[1]);
                        }
                    }
                }
            }
        }
    });
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "Project",
            "name": obj
        },
        "callback": function(response) {
            var project = response.message;
            cur_frm.set_value("from_date", project.expected_start_date);
            cur_frm.set_value("to_date", project.expected_end_date);
        }
    });
}
