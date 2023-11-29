// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Follow Up Note', {
    refresh: function(frm) {
        if (frm.doc.__islocal) {
            cur_frm.set_value("date", new Date());
        }
    }
});
