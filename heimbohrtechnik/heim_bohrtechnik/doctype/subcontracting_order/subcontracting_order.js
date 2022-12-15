// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subcontracting Order', {
    refresh: function(frm) {
        // filters
        cur_frm.fields_dict['drilling_team'].get_query = function(doc) {
             return {
                 filters: {
                     "drilling_team_type": "Verlängerungsteam"
                 }
             }
        }
    
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
        if (frm.doc.project) {
            find_object(frm, frm.doc.project);
        }
    },
    to_date: function(frm) {
        if (frm.doc.from_date > frm.doc.to_date) {
            cur_frm.set_value("from_date", frm.doc.to_date);
        }
    },
    from_date: function(frm) {
        if (frm.doc.from_date > frm.doc.to_date) {
            cur_frm.set_value("to_date", frm.doc.from_date);
        }
    }
});

function find_object(frm, project) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Project",
            'name': project
        },
        'callback': function(response) {
            var project = response.message;
            cur_frm.set_value("object", project.object);
            autocomplete_object(frm);
        }
    });
}

function autocomplete_object(frm) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Object",
            'name': frm.doc.object || frm.doc.project
        },
        'callback': function(response) {
            var object = response.message;
            cur_frm.set_value("object_name", object.object_name);
            cur_frm.set_value("object_street", object.object_street);
            cur_frm.set_value("object_location", object.object_location);
            if (!frm.doc.object) {
                cur_frm.set_value("object", object.name);
            }
        }
    });
}
