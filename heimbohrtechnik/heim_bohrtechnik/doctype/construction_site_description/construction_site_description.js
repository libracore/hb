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
        
        if (!frm.doc.__islocal) {
            frm.add_custom_button( __("Object") , function() {
                frappe.set_route("Form", "Object", frm.doc.object);
            }).addClass("btn-primary");
            
            frm.add_custom_button( __("Project") , function() {
                frappe.set_route("Form", "Project", frm.doc.project);
            }).addClass("btn-primary");
        
            frm.add_custom_button( __("Verlängerung") , function() {
                show_subcontracting_wizard(frm);
            }).addClass("btn-primary");
        }
    },
    before_save: function(frm) {
        if (!frm.doc.object_name) {
            autocomplete_object(frm);
        }
    },
    project: function(frm) {
        // from project: link object
        if ((!frm.doc.object) && (frm.doc.project) && (!locals.ignore_object_update)) {
            locals.ignore_object_update = true;
            cur_frm.set_value("object", frm.doc.project);
            autocomplete_object(frm);
        }
    },
    object: function(frm) {
        // GUI change of object link
        if ((frm.doc.object) && (!locals.ignore_object_update)) {
            locals.ignore_object_update = true;
            cur_frm.set_value("project", frm.doc.object);
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

function show_subcontracting_wizard(frm) {
    // prepare subcontracting wizard
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description.get_subcontracting_order_map',
        'args': {
            'project': frm.doc.project
        },
        'freeze': true,
        'freeze_message': __("Verlängerungsaufträge laden..."),
        'callback': function(response) {
            locals.subcontracting_wizard_fields = response.message;
            console.log(response.message);
            
            let wizard = new frappe.ui.Dialog({
                'fields': locals.subcontracting_wizard_fields,
                'primary_action': function() {
                    wizard.hide();
                    // trigger updates of subcontracting orders
                    frappe.call({
                        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description.save_subcontracting_wizard',
                        'args': {
                            'project': frm.doc.project,
                            'fields': locals.subcontracting_wizard_fields,
                            'values': wizard.get_values()
                        },
                        'freeze': true,
                        'freeze_message': __("Aufträge aktualisieren...")
                    });
                },
                'primary_action_label': __("OK"),
                'title': __("Verlängerungs-Assistent")
            });
            wizard.show();
            
            setTimeout(function () {
                var modals = document.getElementsByClassName("modal-dialog");
                if (modals.length > 0) {
                    modals[modals.length - 1].style.width = "1000px";
                }
            }, 300);
            
        }
    });
}
