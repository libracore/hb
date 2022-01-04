// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
{% include 'erpnext/selling/sales_common.js' %};

frappe.provide("erpnext.accounts");

erpnext.accounts.SalesInvoiceController = erpnext.selling.SellingController.extend({   
    without_items: function(doc) {
        if (doc.without_items === 1) {
            this.remove_items(doc);
        }
    },
    no_item_net_amount: function(doc) {
        if (doc.without_items === 1) {
            this.remove_items(doc);
        }
    },
    object: function(doc) {
        get_object_address(cur_frm);
        get_project_description(cur_frm);
    },
    refresh: function(doc) {
        // fetch sales invoice object text if new document and has object
        if ((cur_frm.doc.__islocal) && (cur_frm.doc.object)) {
            get_project_description(cur_frm);
        }
    },
    before_save: function(doc) {
        set_conditional_net_total(cur_frm);
        recalculate_markups_discounts(cur_frm);
    },
    setup: function(doc) {
        this.setup_posting_date_time_check();
        this._super(doc);
    },
    onload: function() {
        var me = this;
        this._super();

        if(!this.frm.doc.__islocal && !this.frm.doc.customer && this.frm.doc.debit_to) {
            // show debit_to in print format
            this.frm.set_df_property("debit_to", "print_hide", 0);
        }

        erpnext.queries.setup_queries(this.frm, "Warehouse", function() {
            return erpnext.queries.warehouse(me.frm.doc);
        });

        if(this.frm.doc.__islocal && this.frm.doc.is_pos) {
            //Load pos profile data on the invoice if the default value of Is POS is 1

            me.frm.script_manager.trigger("is_pos");
            me.frm.refresh_fields();
        }
    },

    refresh: function(doc, dt, dn) {
        const me = this;
        this._super();
        if(cur_frm.msgbox && cur_frm.msgbox.$wrapper.is(":visible")) {
            // hide new msgbox
            cur_frm.msgbox.hide();
        }

        this.frm.toggle_reqd("due_date", !this.frm.doc.is_return);

        // this.show_general_ledger();
    },


    on_submit: function(doc, dt, dn) {
        var me = this;

        if (frappe.get_route()[0] != 'Form') {
            return
        }

        $.each(doc["items"], function(i, row) {
            if(row.delivery_note) frappe.model.clear_doc("Delivery Note", row.delivery_note)
        })
    },

    sales_order_btn: function() {
        var me = this;
        this.$sales_order_btn = this.frm.add_custom_button(__('Sales Order'),
            function() {
                erpnext.utils.map_current_doc({
                    method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
                    source_doctype: "Sales Order",
                    target: me.frm,
                    setters: {
                        customer: me.frm.doc.customer || undefined,
                    },
                    get_query_filters: {
                        docstatus: 1,
                        status: ["not in", ["Closed", "On Hold"]],
                        per_billed: ["<", 99.99],
                        company: me.frm.doc.company
                    }
                })
            }, __("Get items from"));
    },

    delivery_note_btn: function() {
        var me = this;
        this.$delivery_note_btn = this.frm.add_custom_button(__('Delivery Note'),
            function() {
                erpnext.utils.map_current_doc({
                    method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
                    source_doctype: "Delivery Note",
                    target: me.frm,
                    date_field: "posting_date",
                    setters: {
                        customer: me.frm.doc.customer || undefined
                    },
                    get_query: function() {
                        var filters = {
                            docstatus: 1,
                            company: me.frm.doc.company,
                            is_return: 0
                        };
                        if(me.frm.doc.customer) filters["customer"] = me.frm.doc.customer;
                        return {
                            query: "erpnext.controllers.queries.get_delivery_notes_to_be_billed",
                            filters: filters
                        };
                    }
                });
            }, __("Get items from"));
    },

    tc_name: function() {
        this.get_terms();
    },
    customer: function() {
        if (this.frm.doc.is_pos){
            var pos_profile = this.frm.doc.pos_profile;
        }
        var me = this;
        if(this.frm.updating_party_details) return;
        erpnext.utils.get_party_details(this.frm,
            "erpnext.accounts.party.get_party_details", {
                posting_date: this.frm.doc.posting_date,
                party: this.frm.doc.customer,
                party_type: "Customer",
                account: this.frm.doc.debit_to,
                price_list: this.frm.doc.selling_price_list,
                pos_profile: pos_profile
            }, function() {
                me.apply_pricing_rule();
            });

        if(this.frm.doc.customer) {
            frappe.call({
                "method": "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_loyalty_programs",
                "args": {
                    "customer": this.frm.doc.customer
                },
                callback: function(r) {
                    if(r.message && r.message.length) {
                        select_loyalty_program(me.frm, r.message);
                    }
                }
            });
        }
    },

    debit_to: function() {
        var me = this;
        if(this.frm.doc.debit_to) {
            me.frm.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Account",
                    fieldname: "account_currency",
                    filters: { name: me.frm.doc.debit_to },
                },
                callback: function(r, rt) {
                    if(r.message) {
                        me.frm.set_value("party_account_currency", r.message.account_currency);
                        me.set_dynamic_labels();
                    }
                }
            });
        }
    },

    allocated_amount: function() {
        this.calculate_total_advance();
        this.frm.refresh_fields();
    },

    write_off_outstanding_amount_automatically: function() {
        if(cint(this.frm.doc.write_off_outstanding_amount_automatically)) {
            frappe.model.round_floats_in(this.frm.doc, ["grand_total", "paid_amount"]);
            // this will make outstanding amount 0
            this.frm.set_value("write_off_amount",
                flt(this.frm.doc.grand_total - this.frm.doc.paid_amount - this.frm.doc.total_advance, precision("write_off_amount"))
            );
            this.frm.toggle_enable("write_off_amount", false);

        } else {
            this.frm.toggle_enable("write_off_amount", true);
        }

        this.calculate_outstanding_amount(false);
        this.frm.refresh_fields();
    },

    write_off_amount: function() {
        this.set_in_company_currency(this.frm.doc, ["write_off_amount"]);
        this.write_off_outstanding_amount_automatically();
    },

    items_add: function(doc, cdt, cdn) {
        var row = frappe.get_doc(cdt, cdn);
        this.frm.script_manager.copy_from_first_row("items", row, ["income_account", "cost_center"]);
    },

    set_dynamic_labels: function() {
        this._super();
    },

    items_on_form_rendered: function() {
        erpnext.setup_serial_no();
    },

    packed_items_on_form_rendered: function(doc, grid_row) {
        erpnext.setup_serial_no();
    },

    make_sales_return: function() {
        frappe.model.open_mapped_doc({
            method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
            frm: cur_frm
        })
    },

    asset: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if(row.asset) {
            frappe.call({
                method: erpnext.assets.doctype.asset.depreciation.get_disposal_account_and_cost_center,
                args: {
                    "company": frm.doc.company
                },
                callback: function(r, rt) {
                    frappe.model.set_value(cdt, cdn, "income_account", r.message[0]);
                    frappe.model.set_value(cdt, cdn, "cost_center", r.message[1]);
                }
            })
        }
    },

    amount: function(){
        this.write_off_outstanding_amount_automatically()
    },

    change_amount: function(){
        if(this.frm.doc.paid_amount > this.frm.doc.grand_total){
            this.calculate_write_off_amount();
        }else {
            this.frm.set_value("change_amount", 0.0);
            this.frm.set_value("base_change_amount", 0.0);
        }

        this.frm.refresh_fields();
    },
    
        remove_items: function(doc) {
        // clear all items
        cur_frm.clear_table("items");
        cur_frm.refresh_fields();
        // add net item
        frappe.call({
            'method': 'get_akonto_item',
            'doc': doc,
            'callback': function(response) {
                var child = cur_frm.add_child('items');
                frappe.model.set_value(child.doctype, child.name, 'item_code', response.message);
                frappe.model.set_value(child.doctype, child.name, 'qty', 1);
                setTimeout(function (amount) {
                    frappe.model.set_value(child.doctype, child.name, 'rate', doc.no_item_net_amount);
                    cur_frm.refresh_field('items');
                }, 1000);
                
            }
        });
    }
});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.accounts.SalesInvoiceController({frm: cur_frm}));

cur_frm.cscript.update_stock = function(doc, dt, dn) {
    cur_frm.cscript.hide_fields(doc, dt, dn);
    this.frm.fields_dict.items.grid.toggle_reqd("item_code", doc.update_stock? true: false)
}

cur_frm.cscript['Make Delivery Note'] = function() {
    frappe.model.open_mapped_doc({
        method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_delivery_note",
        frm: cur_frm
    })
}

// project name
//--------------------------
cur_frm.fields_dict['project'].get_query = function(doc, cdt, cdn) {
    return{
        query: "erpnext.controllers.queries.get_project_name",
        filters: {'customer': doc.customer}
    }
}

// Income Account in Details Table
// --------------------------------
cur_frm.set_query("income_account", "items", function(doc) {
    return{
        query: "erpnext.controllers.queries.get_income_account",
        filters: {'company': doc.company}
    }
});

// Cost Center in Details Table
// -----------------------------
cur_frm.fields_dict["items"].grid.get_field("cost_center").get_query = function(doc) {
    return {
        filters: {
            'company': doc.company,
            "is_group": 0
        }
    }
}

cur_frm.cscript.income_account = function(doc, cdt, cdn) {
    erpnext.utils.copy_value_in_all_rows(doc, cdt, cdn, "items", "income_account");
}

cur_frm.cscript.expense_account = function(doc, cdt, cdn) {
    erpnext.utils.copy_value_in_all_rows(doc, cdt, cdn, "items", "expense_account");
}

cur_frm.cscript.cost_center = function(doc, cdt, cdn) {
    erpnext.utils.copy_value_in_all_rows(doc, cdt, cdn, "items", "cost_center");
}

cur_frm.set_query("debit_to", function(doc) {
    // filter on Account
    if (doc.customer) {
        return {
            filters: {
                'account_type': 'Receivable',
                'is_group': 0,
                'company': doc.company
            }
        }
    } else {
        return {
            filters: {
                'report_type': 'Balance Sheet',
                'is_group': 0,
                'company': doc.company
            }
        }
    }
});

cur_frm.set_query("asset", "items", function(doc, cdt, cdn) {
    var d = locals[cdt][cdn];
    return {
        filters: [
            ["Asset", "item_code", "=", d.item_code],
            ["Asset", "docstatus", "=", 1],
            ["Asset", "status", "in", ["Submitted", "Partially Depreciated", "Fully Depreciated"]],
            ["Asset", "company", "=", doc.company]
        ]
    }
});

frappe.ui.form.on('Akonto Invoice', {
    setup: function(frm){
        frm.add_fetch('customer', 'tax_id', 'tax_id');
        frm.add_fetch('payment_term', 'invoice_portion', 'invoice_portion');
        frm.add_fetch('payment_term', 'description', 'description');

        frm.set_query("account_for_change_amount", function() {
            return {
                filters: {
                    account_type: ['in', ["Cash", "Bank"]]
                }
            };
        });

        frm.set_query("cost_center", function() {
            return {
                filters: {
                    company: frm.doc.company,
                    is_group: 0
                }
            };
        });

        // expense account
        frm.fields_dict.items.grid.get_field('expense_account').get_query = function(doc) {
            if (erpnext.is_perpetual_inventory_enabled(doc.company)) {
                return {
                    filters: {
                        'report_type': 'Profit and Loss',
                        'company': doc.company,
                        "is_group": 0
                    }
                }
            }
        }

        frm.fields_dict.items.grid.get_field('deferred_revenue_account').get_query = function(doc) {
            return {
                filters: {
                    'root_type': 'Liability',
                    'company': doc.company,
                    "is_group": 0
                }
            }
        }

        frm.set_query('company_address', function(doc) {
            if(!doc.company) {
                frappe.throw(__('Please set Company'));
            }

            return {
                query: 'frappe.contacts.doctype.address.address.address_query',
                filters: {
                    link_doctype: 'Company',
                    link_name: doc.company
                }
            };
        });

    },
    // When multiple companies are set up. in case company name is changed set default company address
    company:function(frm){
        if (frm.doc.company)
        {
            frappe.call({
                method:"frappe.contacts.doctype.address.address.get_default_address",
                args:{ doctype:'Company',name:frm.doc.company},
                callback: function(r){
                    if (r.message){
                        frm.set_value("company_address",r.message)
                    }
                    else {
                        frm.set_value("company_address","")
                    }
                }
            })
        }
    },

    project: function(frm){
        frm.call({
            method: "add_timesheet_data",
            doc: frm.doc,
            callback: function(r, rt) {
                refresh_field(['timesheets'])
            }
        })
    },

    refresh: function(frm) {
        if (frappe.boot.active_domains.includes("Healthcare")){
            frm.set_df_property("patient", "hidden", 0);
            frm.set_df_property("patient_name", "hidden", 0);
            frm.set_df_property("ref_practitioner", "hidden", 0);
            if (cint(frm.doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !frm.doc.is_return) {
                frm.add_custom_button(__('Healthcare Services'), function() {
                    get_healthcare_services_to_invoice(frm);
                },"Get items from");
                frm.add_custom_button(__('Prescriptions'), function() {
                    get_drugs_to_invoice(frm);
                },"Get items from");
            }
        }
        else{
            frm.set_df_property("patient", "hidden", 1);
            frm.set_df_property("patient_name", "hidden", 1);
            frm.set_df_property("ref_practitioner", "hidden", 1);
        }
    },

    create_invoice_discounting: function(frm) {
        frappe.model.open_mapped_doc({
            method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.create_invoice_discounting",
            frm: frm
        });
    }
})

var calculate_total_billing_amount =  function(frm) {
    var doc = frm.doc;

    doc.total_billing_amount = 0.0

    refresh_field('total_billing_amount')
}

var get_checked_values= function($results) {
    return $results.find('.list-item-container').map(function() {
        let checked_values = {};
        if ($(this).find('.list-row-check:checkbox:checked').length > 0 ) {
            checked_values['dn'] = $(this).attr('data-dn');
            checked_values['dt'] = $(this).attr('data-dt');
            checked_values['item'] = $(this).attr('data-item');
            if($(this).attr('data-rate') != 'undefined'){
                checked_values['rate'] = $(this).attr('data-rate');
            }
            else{
                checked_values['rate'] = false;
            }
            if($(this).attr('data-income-account') != 'undefined'){
                checked_values['income_account'] = $(this).attr('data-income-account');
            }
            else{
                checked_values['income_account'] = false;
            }
            if($(this).attr('data-qty') != 'undefined'){
                checked_values['qty'] = $(this).attr('data-qty');
            }
            else{
                checked_values['qty'] = false;
            }
            if($(this).attr('data-description') != 'undefined'){
                checked_values['description'] = $(this).attr('data-description');
            }
            else{
                checked_values['description'] = false;
            }
            return checked_values;
        }
    }).get();
};
