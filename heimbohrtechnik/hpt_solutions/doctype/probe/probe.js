// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Probe', {
    radius: function(frm) {
        if (frm.doc.radius) {
            // V = PI * (r^2) * h
            let V_m3 = (frm.doc.radius ** 2) * Math.PI;
            cur_frm.set_value("volume_per_m", V_m3); 
        }
    },
    nominative_pressure: function(frm) {
        if (frm.doc.nominative_pressure) {
            cur_frm.set_value("max_short_inner_pressure", frm.doc.nominative_pressure * 1.5); 
        }
    }
});

