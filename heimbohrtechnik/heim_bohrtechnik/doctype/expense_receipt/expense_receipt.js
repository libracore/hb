// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt

// filter for accounts
cur_frm.fields_dict['expense_account'].get_query = function(doc) {
     return {
         filters: {
             "company": frappe.defaults.get_user_default("company") || frappe.defaults.get_global_default("company")
         }
     }
}
cur_frm.fields_dict['vat_account'].get_query = function(doc) {
     return {
         filters: {
             "company": frappe.defaults.get_user_default("company") || frappe.defaults.get_global_default("company")
         }
     }
}
    
frappe.ui.form.on('Expense Receipt', {
    refresh: function(frm) {
        if (frm.doc.__islocal) {
            cur_frm.set_value("journal_entry", null);
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
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    'doctype': "Heim Settings",
                    'name': "Heim Settings"
                },
                'callback': function(response) {
                    var settings = response.message;
                    
                    cur_frm.set_value("expense_account", settings.default_expense_account);
                    cur_frm.set_value("vat_account", settings.vat_account);
                }
            });
        }
    }
});
