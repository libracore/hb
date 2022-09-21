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
        'method': "get_autocomplete_data",
        'doc': frm.doc,
        'args': {
            'project': frm.doc.project
        },
        'callback': function(response) {
            cur_frm.set_value("object_name", response.message.object.object_name);
            cur_frm.set_value("object_street", response.message.object.object_street);
            cur_frm.set_value("object_location", response.message.object.object_location);
            cur_frm.set_value("parcel", response.message.object.parcel);
            
            for (var i = 0; i < response.message.object.addresses.length; i++) {
                if (response.message.object.addresses[i].address_type === "Eigentümer") {
                    if (response.message.object.addresses[i].is_simple === 1) {
                        cur_frm.set_value("bewilligungsinhaber", 
                            (response.message.object.addresses[i].simple_name || "") + ", " 
                                + (response.message.object.addresses[i].simple_address || ""));
                    } else {
                        cur_frm.set_value("bewilligungsinhaber", 
                            (response.message.object.addresses[i].address_display || "")
                                .replaceAll("<br>", " - ").replaceAll("\n", " - "));
                    }
                }
            }
                                        
            for (var i = 0; i < response.message.project.permits.length; i++) {
                if (response.message.project.permits[i].permit.includes("Bohrbewilligung kantonal")) {
                    cur_frm.set_value("bewilligung", 
                        (response.message.project.permits[i].permit_number || ""));
                    cur_frm.set_value("bewilligungsdatum", 
                        (response.message.project.permits[i].permit_date));
                }
            }
            
            if (response.message.construction_site_description) {
                if (response.message.construction_site_description.hydrant == 1) {
                    cur_frm.set_value("wasserbezugsort", "Hausanschluss, falls nötig Hydrant");
                } else {
                    cur_frm.set_value("wasserbezugsort", "Hausanschluss");
                }
            }
        }
    });
}
