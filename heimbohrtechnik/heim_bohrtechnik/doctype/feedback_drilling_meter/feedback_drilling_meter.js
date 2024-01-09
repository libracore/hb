// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Feedback Drilling Meter', {
    before_save: function(frm) {
        console.log("hoi");
        autocomplete_day_and_week(frm);
    }
});

function autocomplete_day_and_week(frm) {
    console.log("hoi");
}
