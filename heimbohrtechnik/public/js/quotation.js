// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quotation', {
    object: function(frm) {
        get_object_address(frm);
        get_object_description(frm);
    },
    before_save: function(frm) {
        set_conditional_net_total(frm);
        recalculate_markups_discounts(frm);
    },
    button_plattmachen: function(frm) {
        plattmachen(frm);
    },
    refresh: function(frm) {
        if (frm.doc.object) {
            show_pincode_information(frm.doc.object);
        }
    }
});

frappe.ui.form.on('Discount Position', {
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});

function plattmachen(frm) {
    frappe.prompt([
            {
                'fieldname': 'target', 
                'fieldtype': 'Currency', 
                'label': 'Endbetrag brutto plattmachen auf', 
                'reqd': 1,
                'default': (frm.doc.rounded_total || frm.doc.grand_total)
            }  
        ],
        function(values){
            var factor = values.target / (frm.doc.rounded_total || frm.doc.grand_total);
            console.log("f= " + factor);
            var difference = frm.doc.net_total - (factor * frm.doc.net_total);
            console.log("d= " + difference);
            add_discount_amount("Spezialrabatt", difference);
            recalculate_markups_discounts(frm);
        },
        'Plattmachen',
        'OK'
    )
}

function add_discount_amount(text, amount) {
    var child = cur_frm.add_child('discount_positions');
    frappe.model.set_value(child.doctype, child.name, 'description', text);
    frappe.model.set_value(child.doctype, child.name, 'amount', amount);
    cur_frm.refresh_field('discount_positions');
}
