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
        'callback': function(response) {
            var object = response.message;
            cur_frm.set_value("object_name", object.object_name);
            cur_frm.set_value("object_street", object.object_street);
            cur_frm.set_value("object_location", object.object_location);
            cur_frm.set_value("parcel", object.parcel);
            
            for (var i = 0; i < object.addresses.length; i++) {
                if (object.addresses[i].address_type === "Eigentümer") {
                    if (object.addresses[i].is_simple === 1) {
                        cur_frm.set_value("bewilligungsinhaber", 
                            (object.addresses[i].simple_name || "") + ", " 
                                + (object.addresses[i].simple_address || ""));
                    } else {
                        cur_frm.set_value("bewilligungsinhaber", 
                            (object.addresses[i].address_display || "")
                                .replaceAll("<br>", " - ").replaceAll("\n", " - "));
                    }
                }
            }
            
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    'doctype': "Project",
                    'name': frm.doc.object
                },
                'callback': function(response) {
                    var project = response.message;
                                        
                    for (var i = 0; i < project.permits.length; i++) {
                        if (project.permits[i].permit.includes("Bohrbewilligung")) {
                            cur_frm.set_value("bewilligung", 
                                (project.permits[i].permit_number || ""));
                            cur_frm.set_value("bewilligungsdatum", 
                                (project.permits[i].permit_date));
                        }
                    }
                }
            });
        }
    });
}
