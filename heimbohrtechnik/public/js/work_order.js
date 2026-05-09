// Copyright (c) 2026, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Order', {
    'refresh': function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button( __("Verfügbare Lager holen") , function() {
                get_available_warehouses(frm);
            });
        }
    }
});

function get_available_warehouses(frm) {
    for (let i = 0; i < frm.doc.required_items.length; i++) {
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.utils.get_available_warehouse',
            'args': {
                'item_code': frm.doc.required_items[i].item_code,
                'company': frm.doc.company
            },
            'callback': function(response) {
                if (response.message) {
                    frappe.model.set_value(frm.doc.required_items[i].doctype, frm.doc.required_items[i].name, 'source_warehouse', response.message);
                }
            }
        });
    }
}
