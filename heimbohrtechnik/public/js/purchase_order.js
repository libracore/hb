// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Order', {
    object: function(frm) {
        get_object_address(frm);
    },
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Umbuchen"), function() {
                reassign(frm);
            });
        }
    },
    on_submit: function(frm) {
        // create and attach PDF
        frappe.call({
            'method': 'erpnextswiss.erpnextswiss.attach_pdf.attach_pdf',
            'args': {
                'doctype': frm.doc.doctype,
                'docname': frm.doc.name,
                'print_format': "Bestellung"
            },
            'callback': function(response) {
                cur_frm.reload_doc();
            }
        });
        
        if (frm.doc.lagervorrat) {
            // create purchase receipt and close order and receipt
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.utils.po_from_stock',
                'args': {
                    'purchase_order': frm.doc.name
                },
                'callback': function(response) {
                    cur_frm.reload_doc();
                }
            });
        }
    }
});

function reassign(frm) {
    // fetch parking space
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Heim Settings",
            'name': "Heim Settings"
        },
        'callback': function(response) {
            var settings = response.message;
            // find old project
            var old_project = null;
            for (var i = 0; i < cur_frm.doc.items.length; i++) {
                if (cur_frm.doc.items[i].project) {
                    old_project = cur_frm.doc.items[i].project;
                    break;
                }
            }
            // show a dialog to prompt
            frappe.prompt(
                [
                    {'fieldname': 'old_project', 'fieldtype': 'Link', 'label': __('From'), 'options': 'Project', 'default': old_project, 'hidden': true},
                    {'fieldname': 'parking', 'fieldtype': 'Link', 'label': __('Sondenparkplatz'), 'options': 'Project', 'default': settings.sondenparkplatz, 'hidden': true},
                    {'fieldname': 'move', 'fieldtype': 'Check', 'label': __('Auf ein anderes Projekt (statt dem Sondenparkplatz)'), 'default': 0},
                    {'fieldname': 'project', 'fieldtype': 'Link', 'label': __('Project'), 'options': 'Project', 'depends_on': 'move'}
                ],
                function(values){
                    var to_project = settings.sondenparkplatz;      // default: move to parking
                    if ((values.move === 1) && (values.project)) {
                        // move to project
                        to_project = values.project;
                    }
                    frappe.call({
                        'method': "heimbohrtechnik.heim_bohrtechnik.utils.reassign_project",
                        'args': {
                            'purchase_order': frm.doc.name,
                            'old_project': old_project,
                            'new_project': to_project
                        },
                        'callback': function(response) {
                            cur_frm.reload_doc();
                        }
                    });
                },
                __('Auf ein anderes Projekt umbuchen'),
                'OK'
            );
        }
    })
}
