// Copyright (c) 2021-2024, libracore AG and contributors
// For license information, please see license.txt

// extend dashboard
try {
    cur_frm.dashboard.add_transactions([
        {
            'label': 'Sales',
            'items': ['Follow Up Note']
        }
    ]);
} catch { /* do nothing for older versions */ }

frappe.ui.form.on('Quotation', {
    object: function(frm) {
        get_object_address(frm);
        get_object_description(frm);
    },
    before_save: function(frm) {
        set_conditional_net_total(frm);
        recalculate_markups_discounts(frm);
        
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
        
        // set follow up date
        cur_frm.set_value("next_follow_up",frappe.datetime.add_days(frm.doc.transaction_date, 14));
    },
    refresh: function(frm) {
        if (frm.doc.object) {
            show_pincode_information(frm.doc.object);
        }
        
        // fresh document
        if (frm.doc.__islocal) {
            // set naming series (for company)
            select_naming_series(frm);
            
            // verify customer if set (on duplicate or revision)
            get_tax_id(frm);

            // set valid till date
            cur_frm.set_value("valid_till",frappe.datetime.add_days(frm.doc.transaction_date, 30));
        }
        
        // get tax id
        if ((frm.doc.party_name) && (!frm.doc.tax_id) && (frm.doc.docstatus === 0)) {
            get_tax_id(frm);
        }
        
        // navigate to environment
        if (frm.doc.object) {
            frm.add_custom_button( __("Umgebung"), function() {
                window.open("/desk#object-overview?object=" + frm.doc.object, "_blank");
            });
        }
        
        // fill address and description if missing
        if (frm.doc.object) {
            if (!frm.doc.object_address_display) {
                get_object_address(frm);
            }
            if (!frm.doc.object_description) {
                get_object_description(frm);
            }
        }
        
        // allow to extend valid until to today (to create sales order on an expired qtn
        if ((frm.doc.docstatus === 1) && (frm.doc.valid_till < frappe.datetime.get_today())) {
            frm.add_custom_button( __("Verlängern"), function() {
                frappe.call({
                    'method': 'heimbohrtechnik.heim_bohrtechnik.utils.extend_quotation_due_date',
                    'args': {
                        'quotation': frm.doc.name
                    },
                    'callback': function(response) {
                        cur_frm.reload_doc();
                    }
                });
            });
        }
        
        // create watermarked pdf
        if (frm.doc.docstatus === 1) {
            let attachments = cur_frm.attachments.get_attachments();
            let has_pdf = false;
            let file_name = frm.doc.name + ".pdf";
            for (let a = 0; a < attachments.length; a++) {
                if (attachments[a].file_name === file_name) {
                    has_pdf = true;
                    break;
                }
            }
            if (has_pdf) {
                frm.add_custom_button( __("Wasserzeichen einfügen"), function() {
                    frappe.call({
                        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.add_watermark',
                        'args': {
                            'file_name': file_name
                        },
                        'callback': function(response) {
                            frappe.show_alert( __("Wasserzeichen eingefügt in") + " " + file_name);
                            cur_frm.reload_doc();
                        }
                    });
                });
            }
        }
    },
    party_name: function(frm) {
        if (frm.doc.party_name) {
            get_tax_id(frm);
        }
    },
    on_submit: function(frm) {
        // create and attach PDF
        frappe.call({
            'method': 'erpnextswiss.erpnextswiss.attach_pdf.attach_pdf',
            'args': {
                'doctype': frm.doc.doctype,
                'docname': frm.doc.name,
                'print_format': "Offerte"
            },
            'callback': function(response) {
                cur_frm.reload_doc();
            }
        });
        // if this came from a request, close it
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.drilling_request.drilling_request.close_request',
            'args': {
                'quotation': frm.doc.name,
            },
            'callback': function(response) {
                frappe.show_alert(__("Angebotsanfrage geschlossen") );
            }
        });
    }
});

frappe.ui.form.on('Discount Position', {
    discount: function(frm, dt, dn) {
        update_additional_discount(frm);
    },
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});

frappe.ui.form.on('Markup Position', {
    discount: function(frm, dt, dn) {
        update_additional_discount(frm);
    },
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});

function add_discount_amount(text, amount) {
    var child = cur_frm.add_child('discount_positions');
    frappe.model.set_value(child.doctype, child.name, 'description', text);
    frappe.model.set_value(child.doctype, child.name, 'amount', amount);
    cur_frm.refresh_field('discount_positions');
}

function get_tax_id(frm) {
    if (frm.doc.party_name) {
        frappe.call({
            "method": "frappe.client.get",
            "args": {
                "doctype": "Customer",
                "name": frm.doc.party_name
            },
            "async": false,
            "callback": function(response) {
                var customer = response.message;
                cur_frm.set_value("tax_id", customer.tax_id);
                if (customer.disabled === 1) {
                    frappe.msgprint( __("Vorsicht, der Kunde {0} ist deaktiviert").replace("{0}", customer.customer_name), __("Validation") );
                }
            }
        });
    }
}
