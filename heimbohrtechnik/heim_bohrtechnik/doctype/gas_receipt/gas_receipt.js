// Copyright (c) 2023-2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gas Receipt', {
    refresh: function(frm) {
        if (frm.doc.__islocal) {
            // set today as default date
            cur_frm.set_value('date', frappe.datetime.get_today());
            // check if current user has a truck
            frappe.call({
                'method': 'frappe.client.get_list',
                'args': {
                    'doctype': 'Truck',
                    'filters': [
                        ['user', '=', frappe.session.user]
                    ],
                    'fields': ['name'],
                },
                'callback': function(response) {
                    if (response.message.length > 0) {
                        cur_frm.set_value('truck', response.message[0].name);
                    }
                }
            });
        }
    }
});
