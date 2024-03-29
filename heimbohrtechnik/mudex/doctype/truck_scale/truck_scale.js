// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Truck Scale', {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Weight"), function() {
                get_weight(frm);
            });
        }
    }
});

function get_weight(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.mudex.doctype.truck_scale.truck_scale.get_weight',
        'args': {
            'truck_scale': frm.doc.name
        },
        'callback': function(r) {
            if (typeof r.message !== 'undefined') {
                var html = __('Weight') + " " + r.message.weight + " kg";
                cur_frm.set_df_property('weight_html', 'options', html);
            } else {
                console.log("Invalid response");
            }
        }
    });
}
