// Copyright (c) 2021-2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Drilling Request', {
    refresh: function(frm) {
        if (!frm.doc.date) {
            // set today as default date
            cur_frm.set_value("date", frappe.datetime.get_today());
        }
        if (!frm.doc.quotation_until) {
            // set in 3 days as default quotation date
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.holiday_safe_add_days',
                'args': {
                    'source_date': (frm.doc.date || frappe.datetime.get_today()),
                    'days': 3
                },
                'callback': function(response) {
                    cur_frm.set_value("quotation_until", response.message);
                }
            });
            //cur_frm.set_value("quotation_until", frappe.datetime.add_days(frappe.datetime.get_today(), 3));
        }
        
        if (!frm.doc.__islocal) {
            if (!frm.doc.object) {
                // create object
                frm.add_custom_button(__("Object"), function() {
                    create_object(frm);
                }, __("Create"));
            } else {
                // open object
                frm.add_custom_button(__("Object"), function() {
                    frappe.set_route("Form", "Object", frm.doc.object);
                }, __("Öffnen"));
            }
            
            if ((frm.doc.object) && (frm.doc.customer) && (!frm.doc.quotation)) {
                // create a quotation
                frm.add_custom_button(__("Quotation"), function() {
                    create_quotation(frm);
                }, __("Create"));
            }
            
            // open customer
            if (frm.doc.customer) {
                frm.add_custom_button(__("Customer"), function() {
                    frappe.set_route("Form", "Customer", frm.doc.customer);
                }, __("Öffnen"));
            } else {
                cur_frm.dashboard.add_comment(__('Bitte einen Kunden hinterlegen'), 'yellow', true);
            }
            
            // open quotation
            if (frm.doc.quotation) {
                frm.add_custom_button(__("Quotation"), function() {
                    frappe.set_route("Form", "Quotation", frm.doc.quotation);
                }, __("Öffnen"));
            }
            
            
        }
    }
});

function create_object(frm) {
    cur_frm.save().then(function () {
        frappe.call({
            'method': 'create_object',
            'doc': cur_frm.doc,
            'callback': function(response) {
                frappe.set_route("Form", "Object", response.message);
            }
        });
    });
}

function create_quotation(frm) {
    cur_frm.save().then(function () {
        frappe.call({
            'method': 'create_quotation',
            'doc': cur_frm.doc,
            'callback': function(response) {
                frappe.set_route("Form", "Quotation", response.message);
            }
        });
    });
}
