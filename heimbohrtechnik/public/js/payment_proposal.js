// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Proposal', {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Freigabeansicht"), function() {
                open_approval_view(frm);
            });
        }
    }
});

function open_approval_view(frm) {
    window.open("/desk#invoice-review?payment_proposal=" + frm.doc.name, "_blank");
}
