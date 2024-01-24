// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt

// filter for accounts
cur_frm.fields_dict['expense_account'].get_query = function(doc) {
     return {
         filters: {
             "company": cur_frm.doc.company || frappe.defaults.get_user_default("company") || frappe.defaults.get_global_default("company")
         }
     }
}
cur_frm.fields_dict['vat_account'].get_query = function(doc) {
     return {
         filters: {
             "company": cur_frm.doc.company || frappe.defaults.get_user_default("company") || frappe.defaults.get_global_default("company")
         }
     }
}
cur_frm.fields_dict['tax_template'].get_query = function(doc) {
     return {
         filters: {
             "company": cur_frm.doc.company || frappe.defaults.get_user_default("company") || frappe.defaults.get_global_default("company")
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
        
        if (!frm.doc.company) {
            cur_frm.set_value("company", frappe.defaults.get_user_default("company") || frappe.defaults.get_global_default("company"));
        }
    },
    tax_template: function(frm) {
        if (frm.doc.tax_template) {
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    'doctype': "Purchase Taxes and Charges Template",
                    'name': frm.doc.tax_template
                },
                'callback': function(response) {
                    var tax_template = response.message;
                    
                    if (tax_template.taxes.length > 0) {
                        var net_amount = 100 * frm.doc.amount / (100 + tax_template.taxes[0].rate);
                        cur_frm.set_value("vst", frm.doc.amount - net_amount);
                        cur_frm.set_value("vat_account", tax_template.taxes[0].account_head);
                    }
                }
            });
        }
    }
});
