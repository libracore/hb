// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

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
    },
    refresh: function(frm) {
        if (frm.doc.object) {
            show_pincode_information(frm.doc.object);
        }
        
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
        
        // get tax id
        if ((frm.doc.party_name) && (!frm.doc.tax_id) && (frm.doc.docstatus === 0)) {
            get_tax_id(frm);
        }
        
        // navigate to environment
        if (frm.doc.object) {
            frm.add_custom_button("Umgebung", function() {
                window.open("/desk#object-overview?object=" + frm.doc.object, "_blank");
            });
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
        }
    });
}
