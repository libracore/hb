// Copyright (c) 2021-2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Construction Site Description', {
    onload: function(frm) {
        // filter for tractor suppliers
        cur_frm.fields_dict['tractor'].get_query = function(doc) {
             return {
                'query': 'heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability',
                'filters': {
                    'capability': "Traktor"
                }
            }
        } 
    },
    refresh: function(frm) {
        // from object: link project
        if ((frm.doc.object) && (!frm.doc.project)) {
            cur_frm.set_value("project", frm.doc.object);
        }
        
        frm.add_custom_button( __("Object") , function() {
            frappe.set_route("Form", "Object", frm.doc.object);
        }).addClass("btn-primary");
        
        frm.add_custom_button( __("Project") , function() {
            frappe.set_route("Form", "Project", frm.doc.project);
        }).addClass("btn-primary");
    },
    before_save: function(frm) {
        if (!frm.doc.object_name) {
            autocomplete_object(frm);
        }
    },
    project: function(frm) {
        // from project: link object
        if ((!frm.doc.object) && (frm.doc.project)) {
            cur_frm.set_value("object", frm.doc.project);
            autocomplete_object(frm);
        }
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
        }
    });
}
