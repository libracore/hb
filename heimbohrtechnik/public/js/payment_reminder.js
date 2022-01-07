// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Reminder', {
    refresh: function(frm) {
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
    },
    before_save: function(frm) {       
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
    }
});
