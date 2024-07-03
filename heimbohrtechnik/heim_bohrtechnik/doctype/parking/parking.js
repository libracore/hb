// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Parking', {
    refresh: function(frm) {

    },
    pincode: function(frm) {
        if (frm.doc.pincode) {
            get_city_from_pincode(frm.doc.pincode, 'city', 'canton');
            
        }
        set_location(frm);
    },
    city: function(frm) {
        set_location(frm);
    }
});

function set_location(frm) {
    cur_frm.set_value('location', (frm.doc.pincode || "") + " " + (frm.doc.city || ""));
}
