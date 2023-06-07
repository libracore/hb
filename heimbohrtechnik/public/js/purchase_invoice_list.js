// Copyright (c) 2022-2023, libracore and contributors
// For license information, please see license.txt

frappe.listview_settings['Purchase Invoice'] = {
    onload: function(listview) {
        listview.page.add_menu_item(__("Quick Entry"), function() {
            quick_entry();
        });
    }
};

function quick_entry() {
    var d = new frappe.ui.Dialog({
        'title': __('Quick Entry'),
        'fields': [
            {
                'fieldname': 'company', 
                'fieldtype': 'Link', 
                'label': __('Company'), 
                'reqd': 1, 
                'options': 'Company',
                'default': frappe.defaults.get_user_default("Company"),
                'onchange': function() {
                    frappe.call({
                        'method': "frappe.client.get",
                        'args': {
                            'doctype': "Company",
                            'name': d.fields_dict.company.value
                        },
                        'callback': function(response) {
                            var company = response.message;
                            d.set_value("cost_center", company.cost_center)
                        }
                    });
                }
            },
            {
                'fieldname': 'supplier', 
                'fieldtype': 'Link', 
                'label': __('Supplier'), 
                'options': 'Supplier',
                'reqd': 1,
                'onchange': function() {
                    frappe.call({
                        'method': "frappe.client.get",
                        'args': {
                            'doctype': "Supplier",
                            'name': d.fields_dict.supplier.value
                        },
                        'callback': function(response) {
                            var supplier = response.message;
                            d.set_value("supplier_name", supplier.supplier_name)
                        }
                    });
                }
            },
            {
                'fieldname': 'supplier_name', 
                'fieldtype': 'Data', 
                'label': __('Supplier name'), 
                'read_only': 1
            },
            {
                'fieldname': 'date', 
                'fieldtype': 'Date', 
                'label': __('Posting Date'), 
                'reqd': 1, 
                'default': frappe.datetime.get_today()
            },
            {
                'fieldname': 'project', 
                'fieldtype': 'Link', 
                'label': __('Project'), 
                'options': 'Project'
            },
            {
                'fieldname': 'bill_no', 
                'fieldtype': 'Data', 
                'label': __('Bill No'), 
                'reqd': 1
            },
            {
                'fieldname': 'item', 
                'fieldtype': 'Link', 
                'label': __('Item'), 
                'reqd': 1, 
                'options': 'Item',
                'get_query': function() { return { filters: {'is_purchase_item': 1 } } }
            },
            {
                'fieldname': 'amount', 
                'fieldtype': 'Currency', 
                'label': __('Amount'), 
                'reqd': 1
            },
            {
                'fieldname': 'cost_center', 
                'fieldtype': 'Link', 
                'label': __('Cost Center'), 
                'reqd': 1, 
                'options': 'Cost Center',
                'get_query': function() { return { filters: {'company': d.fields_dict.company.value } } }
            },
            {
                'fieldname': 'taxes_and_charges', 
                'fieldtype': 'Link', 
                'label': __('Taxes and Charges Template'), 
                'reqd': 1, 
                'options': 'Purchase Taxes and Charges Template'
            },
            {
                'fieldname': 'remarks', 
                'fieldtype': 'Data', 
                'label': __('Remarks')
            }
        ],
        'primary_action': function() {
            d.hide();
            var values = d.get_values();
            frappe.call({
                    'method': "heimbohrtechnik.heim_bohrtechnik.utils.quick_entry_purchase_invoice",
                    'args':{
                        'company': values.company,
                        'supplier': values.supplier,
                        'date': values.date,
                        'project': values.project,
                        'bill_no': values.bill_no,
                        'item': values.item,
                        'amount': values.amount,
                        'cost_center': values.cost_center,
                        'taxes_and_charges': values.taxes_and_charges,
                        'remarks': values.remarks
                    },
                    'callback': function(r)
                    {
                        frappe.set_route("Form", "Purchase Invoice", r.message);
                    }
            });
        },
        'primary_action_label': __('Create')
    });
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Company",
            'name': frappe.defaults.get_user_default("Company")
        },
        'callback': function(response) {
            var company = response.message;
            d.set_value("cost_center", company.cost_center)
        }
    });
    d.show();
}
