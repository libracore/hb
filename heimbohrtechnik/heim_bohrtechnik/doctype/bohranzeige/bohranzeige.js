// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bohranzeige', {
    refresh: function(frm) {
        // from object: new bohranzeige: link project
        if ((frm.doc.object) && (!frm.doc.project)) {
            cur_frm.set_value("project", frm.doc.object);
        }
    },
    before_save: function(frm) {
        if (!frm.doc.object_name) {
            autocomplete_object(frm);
        }
    },
    project: function(frm) {
        autocomplete_object(frm);
    }
});

function autocomplete_object(frm) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Object",
            'name': frm.doc.object
        },
        'async': false,
        'callback': function(response) {
            var object = response.message;
            cur_frm.set_value("object_name", object.object_name);
            
            for (var i = 0; i < object.addresses.length; i++) {
                if (object.addresses[i].address_type === "Eigentümer") {
                    cur_frm.set_value("bewilligungsinhaber", 
                        (object.addresses[i].address_display || "")
                            .replaceAll("<br>", " - ").replaceAll("\n", " - "));
                }
            }
        }
    });
}
