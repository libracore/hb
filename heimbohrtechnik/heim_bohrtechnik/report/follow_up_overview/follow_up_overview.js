// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Follow-Up Overview"] = {
    "filters": [
        {
            "fieldname":"volume_from",
            "label": __("Volumen von"),
            "fieldtype": "Int",
            "default": 500000
        },
        {
            "fieldname":"volume_to",
            "label": __("Volumen bis"),
            "fieldtype": "Int"
        },
        {
            "fieldname":"from_date",
            "label": __("Von Datum"),
            "fieldtype": "Date"
        },
        {
            "fieldname":"to_date",
            "label": __("Bis Datum"),
            "fieldtype": "Date"
        }
    ],
    "onload": (report) => {
        // attach a handler that stores the clicked row
        if (!locals.click_handler) {
            locals.click_handler = true;
            
            cur_page.container.addEventListener("click", function(event) {
                locals.current_row = event.target.parentElement.getAttribute("data-row-index");
                if (locals.current_row) {
                    locals.current_quotation = frappe.query_report.data[locals.current_row].quotation;
                }
            });
        }
        
        // attach note button
        report.page.add_inner_button( __("Follow Up Note"), function() {
            if (locals.current_quotation) {
                frappe.prompt([
                        {
                            'fieldname': 'quotation', 
                            'fieldtype': 'Link', 
                            'label': __('Quotation'), 
                            'options': 'Quotation',
                            'default': locals.current_quotation,
                            'reqd': 1,
                            'read_only': 1
                        },
                        {
                            'fieldname': 'note', 
                            'fieldtype': 'Small Text', 
                            'label': __('Note'), 
                            'reqd': 1
                        }  
                    ],
                    function(values){
                        // insert into DB
                        frappe.db.insert({
                            "doctype": "Follow Up Note",
                            "quotation": values.quotation,
                            "notes": values.note
                        }).then(function(doc) {
                            frappe.query_report.refresh();
                        });
                    },
                    __('New Follow Up Note'),
                    __('Add')
                );
            } else {
                frappe.msgprint(__("Bitte eine Zeile anwählen"), __("Information") );
            }
        });
        
        report.page.add_inner_button( __("Assign to"), function() {
            if (locals.current_quotation) {
                const assign_to = new frappe.ui.form.AssignToDialog({
                    'obj': cur_page,
                    'method': 'frappe.desk.form.assign_to.add',
                    'doctype': "Quotation",
                    'docname': locals.current_quotation,
                    'callback': function (r) {
                        frappe.query_report.refresh();
                    } 
                });
                
                assign_to.dialog.show();
            } else {
                frappe.msgprint(__("Bitte eine Zeile anwählen"), __("Information") );
            }
        });
        
    }
};
