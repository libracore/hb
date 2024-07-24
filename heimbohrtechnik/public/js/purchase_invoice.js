// Copyright (c) 2021-2024, libracore AG and contributors
// For license information, please see license.txt

cur_frm.dashboard.add_transactions([
    {
        'label': 'Expenses',
        'items': ['Expense Receipt', 'Gas Receipt']
    }
]); 
        
frappe.ui.form.on('Purchase Invoice', {
    refresh: function(frm) {
        if ((!frm.doc.__islocal) && (frm.doc.docstatus < 2)) {
            frm.add_custom_button(__("Spesen anhängen"), function() {
                find_payment_methods();
            });
            
            find_attached_expenses(frm);
        }
        if (frm.doc.docstatus === 0) {
            cur_frm.set_value("quick_remarks", frm.doc.remarks);
        }
    },
    before_save: function(frm) {
        if (frm.doc.object) {
            set_project(frm);
        }
    },
    before_cancel: function(frm) {
        unlink_expenses(frm);
    },
    quick_remarks: function(frm) {
        cur_frm.set_value("remarks", frm.doc.quick_remarks);
    }
});

function set_project(frm) {
    // check if there is a project for this object and set it
    frappe.call({
        'method': 'frappe.client.get_list',
        'args': {
            'doctype': 'Project',
            'filters': [
                ['name', '=', frm.doc.object]
            ],
            'fields': ['name'],
        },
        'async': false,
        'callback': function(response) {
            if ((response.message) && (response.message.length > 0)) {
                var project = response.message[0]['name'];
                for (var i = 0; i < frm.doc.items.length; i++) {
                    frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, 'project', project);
                }
            }
        }
    });
}

function find_attached_expenses(frm) {
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.doctype.expense_receipt.expense_receipt.get_allocated_expenses",
        "args": {
            "purchase_invoice": frm.doc.name
        },
        "callback": function(response) {
            var allocated_expenses = response.message;
            var allocated_amount = 0;
            for (var i = 0; i < allocated_expenses.length; i++) {
                allocated_amount += allocated_expenses[i].amount;
            }
            if (allocated_amount > 0) {
                setTimeout(function (allocated_expenses, allocated_amount) {
                    cur_frm.dashboard.add_comment( 
                        "Es sind " + allocated_expenses.length + 
                        " Spesenbelege zu CHF " + allocated_amount.toFixed(2) + 
                        " angehängt", 'blue', true
                    );
                }, 500, allocated_expenses, allocated_amount);
            }
        }
    });
}

function find_payment_methods() {
    // select payment method
    frappe.call({
        'method': 'frappe.client.get_list',
        'args': {
            'doctype': 'Mode of Payment',
            'filters': [
                ['enabled', '=', 1]
            ],
            'fields': ['name'],
        },
        'callback': function(response) {
            console.log("select payment");
            if ((response.message) && (response.message.length > 0)) {
                var payment_methods = []
                for (var i = 0; i < response.message.length; i++) {
                    payment_methods.push(response.message[i].name);
                }
                frappe.prompt([
                        {
                            'fieldname': 'payment_method', 
                            'fieldtype': 'Select', 
                            'options': payment_methods.join("\n"), 
                            'label': 'Kartenkonto', 
                            'reqd': 1
                        }  
                    ],
                    function(values){
                        select_expenses(values.payment_method);
                    },
                    'Kreditkarte wählen',
                    'OK'
                );
            }
        }
    });
}
    
function select_expenses(payment_method) {
    // get available expenses
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.doctype.expense_receipt.expense_receipt.get_unallocated_expenses",
        "args": {
            "payment_method": payment_method
        },
        "callback": function(response) {
            var unallocated_expenses = response.message;
            if (unallocated_expenses.length > 0) {
                // show dialog
                const fields = [{
                    'label': 'Expenses',
                    'fieldtype': 'Table',
                    'fieldname': 'expenses',
                    'description': "Einträge aus der Liste entfernen, die nicht angehängt werden sollen.",
                    'fields': [{
                        'fieldtype': 'Read Only',
                        'fieldname': 'name',
                        'label': __('Expense'),
                        'in_list_view': 1
                    }, {
                        'fieldtype': 'Read Only',
                        'fieldname': 'date',
                        'label': __('Date'),
                        'in_list_view': 1
                    }, {
                        'fieldtype': 'Read Only',
                        'fieldname': 'amount',
                        'label': __('Amount'),
                        'in_list_view': 1
                    }, {
                        'fieldtype': 'Read Only',
                        'fieldname': 'currency',
                        'label': __('Currency'),
                        'in_list_view': 1
                    }],
                    'data': unallocated_expenses,
                    'get_data': () => {
                        return unallocated_expenses;
                    }
                }];
                var d = new frappe.ui.Dialog({
                    'fields': fields,
                    'primary_action': function(){
                        d.hide();
                        attach_expense_receipts(d.get_values().expenses);
                    },
                    'primary_action_label': __('Anhängen')
                });
                d.show();
            } 
        }
    });
}

function attach_expense_receipts(expenses) {
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.doctype.expense_receipt.expense_receipt.attach_expenses",
        'args': {
            'expenses': expenses,
            'purchase_invoice': cur_frm.doc.name
        },
        'callback': function(response) {
            cur_frm.reload_doc();
        }
    });
}

function unlink_expenses(frm) {
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.doctype.expense_receipt.expense_receipt.unattach_expenses",
        'args': {
            'purchase_invoice': cur_frm.doc.name
        },
        'async': false
    });
}
