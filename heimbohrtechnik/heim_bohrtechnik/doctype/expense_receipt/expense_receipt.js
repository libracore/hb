// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Expense Receipt', {
    refresh: function(frm) {
        if (frm.doc.__islocal) {
            cur_frm.set_value("date", new Date());
            frappe.call({
                'method': "frappe.client.get_list",
                'args': {
                    'doctype': "Employee",
                    'filters': {
                        'user_id': frappe.session.user
                    },
                    'fields': ['name']
                },
                'callback': function(response) {
                    var employee = response.message;
                    
                    if (employee.length > 0) {
                        cur_frm.set_value("employee", employee[0].name);
                    }
                }
            });
        }
    }
});
