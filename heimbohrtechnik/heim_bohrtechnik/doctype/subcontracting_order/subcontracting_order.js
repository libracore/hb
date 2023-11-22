// Copyright (c) 2022-2023, libracore AG and contributors
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
        
        // create pdf with plans
        frm.add_custom_button(__("PDF mit Werkleitungen"), function() {
            create_full_pdf(frm);
        });
        
        // load template
        frm.add_custom_button(__("Vorlage"), function() {
            from_template(frm);
        });
        
        // pull items
        frm.add_custom_button(__("Artikel holen"), function() {
            pull_items(frm);
        });
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

function create_full_pdf(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.create_subcontracting_order_pdf',
        'args': {'subcontracting_order': frm.doc.name},
        'callback': function(response) {
            cur_frm.reload_doc();
        },
        'freeze': true,
        'freeze_message': __("PDF mit Werkplänen erstellen, bitte warten...")
    });
}

function from_template(frm) {
    // find all templates
    frappe.call({
        'method': "frappe.client.get_list",
        'args': {
            'doctype': "Subcontracting Order Template"
        },
        'callback': function(response) {
            // dialog to select template
            var templates = response.message;
            var options = [];
            for (var i = 0; i < templates.length; i++) {
                options.push(templates[i].name);
            }
            var d = new frappe.ui.Dialog({
                'fields': [
                    {'fieldname': 'template', 'fieldtype': 'Select', 'label': __("Vorlage"), "options": options.join("\n")}
                ],
                'primary_action': function(){
                    d.hide();
                    // load template
                    frappe.call({
                        'method': 'frappe.client.get',
                        'args': {
                            'doctype': "Subcontracting Order Template",
                            'name': d.get_values().template
                        },
                        'callback': function(response) {
                            // apply template
                            var template = response.message;
                            if (template.drilling_team) { cur_frm.set_value("drilling_team", template.drilling_team); }
                            if (template.order_description) { cur_frm.set_value("order_description", template.order_description); }
                            if (template.prio) { cur_frm.set_value("prio", template.prio); }
                            if (template.remarks) { cur_frm.set_value("remarks", template.remarks); }
                            for (var i = 0; i < template.items.length; i++) {
                                var child = cur_frm.add_child('items');
                                frappe.model.set_value(child.doctype, child.name, 'qty', template.items[i].qty);
                                frappe.model.set_value(child.doctype, child.name, 'description', template.items[i].description);
                            }
                            cur_frm.refresh_field('items');
                        }
                    });
                },
                'primary_action_label': __('Vorlage anwenden'),
                'title': __("Vorlage")
            });
            d.show();
        }
    });
}

function pull_items(frm) {
    frappe.call({
        'method': 'get_bkps',
        'doc': frm.doc,
        'callback': function(response) {
            var bkps = response.message;
            // show dialog to select bkp
            if (bkps.length > 0) {
                frappe.prompt([
                        {
                            'fieldname': 'bkp', 
                            'fieldtype': 'Select', 
                            'label': 'BKP', 
                            'options': bkps.join("\n"), 
                            'reqd': 1,
                            'default': "06"
                        }  
                    ],
                    function(values){
                        // fetch items and insert
                        frappe.call({
                            'method': 'get_bkp_items',
                            'doc': frm.doc,
                            'args': {
                                'bkp': values.bkp
                            },
                            'callback': function(response) {
                                var items = response.message;
                                for (var i = 0; i < items.length; i++) {
                                    var child = cur_frm.add_child('sales_order_items');
                                    frappe.model.set_value(child.doctype, child.name, 'item_code', items[i].item_code);
                                    frappe.model.set_value(child.doctype, child.name, 'item_name', items[i].item_name);
                                    frappe.model.set_value(child.doctype, child.name, 'qty', items[i].qty);
                                    frappe.model.set_value(child.doctype, child.name, 'rate', items[i].base_rate);
                                    frappe.model.set_value(child.doctype, child.name, 'amount', items[i].base_amount);
                                    frappe.model.set_value(child.doctype, child.name, 'subcontracting_amount', items[i].base_amount * ((100 - cur_frm.doc.margin) / 100));
                                }
                                cur_frm.refresh_fields("sales_order_items");
                            }
                        });
                    },
                    __('Position aus AB importieren'),
                    __('Importieren')
                );
            }
        }
    });
}
