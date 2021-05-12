// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
// Common functions

function get_object_address(frm) {
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "Object",
            "name": frm.doc.object
        },
        "callback": function(response) {
            var object = response.message;

            if (object) {
                cur_frm.set_value('object_address_display', object.object_street + "<br>" + object.object_location);
            } 
        }
    });
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
