// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Abo', {
	refresh: function(frm) {
        set_next_reminder_property(frm.doc.set_reminder_manually);
	},
    set_reminder_manually: function(frm) {
        set_next_reminder_property(frm.doc.set_reminder_manually);
    },
    disabled: function(frm) {
        set_end_date(frm.doc.disabled);
    },
    before_save: function(frm) {
        if (frm.doc.__islocal) {
            set_next_reminder(frm);
        }
    },
    interval: function(frm) {
        set_next_reminder(frm);
    }
});

function set_next_reminder_property(set_reminder_manually) {
    if (set_reminder_manually) {
        cur_frm.set_df_property('next_reminder', 'read_only', 0);
    } else {
        cur_frm.set_df_property('next_reminder', 'read_only', 1);
    }
}

function set_end_date(disabled) {
    if (disabled) {
        cur_frm.set_value('end_date', frappe.datetime.nowdate());
    } else {
        cur_frm.set_value('end_date', null);
    }
}

function set_next_reminder(frm) {
    if (!frm.doc.set_reminder_manually) {
        //set initial date
        let initial_date = frm.doc.last_reminder || frm.doc.start_date
        //set years to add
        let years = 0
        if (frm.doc.interval == "Yearly") {
            years = 1;
        } else if (frm.doc.interval == "Biannual") {
            years = 2;
        }
        //set next date
        let next_reminder = frappe.datetime.add_months(initial_date, years * 12);
        cur_frm.set_value("next_reminder", next_reminder);
    }
}
