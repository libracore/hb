// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quotation', {
    object: function(frm) {
        get_object_address(frm);
    }
});

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
