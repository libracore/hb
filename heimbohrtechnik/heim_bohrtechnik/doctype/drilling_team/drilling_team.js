// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Drilling Team', {
    refresh: function(frm) {
        // button to create meterliste link
        frm.add_custom_button("Meterliste", function() {
            create_meter_list_link(frm.doc.name.replace(/\s/g, ''));
        });
    }
});

function create_meter_list_link(drilling_team) {
    var link = window.location.origin + "/feedback_bohrmeter?drilling_team=" + drilling_team
    navigator.clipboard.writeText(link).then(function() {
        frappe.show_alert( __("Link in der Zwischenablage") );
      }, function() {
         frappe.show_alert( __("Kein Zugriff auf Zwischenablage") );
    });
}
