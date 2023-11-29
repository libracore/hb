// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Road Block Material Order', {
    refresh: function(frm) {
        // from object: new bohranzeige: link project
        if ((frm.doc.object) && (!frm.doc.project)) {
            cur_frm.set_value("project", frm.doc.object);
        }
        
        if ((frm.doc.__islocal) && (frm.doc.project)) {
            fetch_content(frm);
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

function fetch_content(frm) {
    frappe.call({
        'method': "frappe.client.get_list",
        'args': {
            'doctype': "Construction Site Description",
            'filters': {
                'project': frm.doc.project
            },
            'fields': ['name', 'road_block_remarks', 'road_block_meters']
        },
        'callback': function(response) {
            var details = response.message;
            
            if (details.length > 0) {
                var child = cur_frm.add_child('items');
                var description = details[0].road_block_remarks;
                if (details[0].road_block_meters) {
                    description += " (" + details[0].road_block_meters + ")";
                }
                frappe.model.set_value(child.doctype, child.name, 'qty', 1);
                frappe.model.set_value(child.doctype, child.name, 'description', description);
                cur_frm.refresh_field('items');
            }
        }
    });
}
