// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Heim Settings', {
    refresh: function(frm) {
        set_abo_reminder_property(frm.doc.send_abo_reminder);
    },
    send_abo_reminder: function(frm) {
        set_abo_reminder_property(frm.doc.send_abo_reminder);
    }
});

function set_abo_reminder_property(reminder) {
    if (reminder) {
        cur_frm.set_df_property('abo_reminder_to', 'reqd', 1);
    } else {
        cur_frm.set_df_property('abo_reminder_to', 'reqd', 0);
    }
}
