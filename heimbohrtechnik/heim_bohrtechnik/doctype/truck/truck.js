// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Truck', {
    refresh: function(frm) {
        if (!frm.doc.__islocal) {
            // button to create truck link
            frm.add_custom_button("<i class='fa fa-truck'></i> Link", function() {
                create_delivery_link(frm, true);
            });
            // button to create truck QR code
            frm.add_custom_button("<i class='fa fa-truck'></i> QR-Code", function() {
                create_delivery_link(frm, false);
            });
        }
    }
});

function create_delivery_link(frm, as_link) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Truck",
            'name': frm.doc.name
        },
        'callback': function(response) {
            var customer = response.message.customer;
            var link = window.location.origin + "/desk#schlammanlieferung?truck=" + frm.doc.name 
                + "&customer=" + customer; 
            if (as_link) {
                navigator.clipboard.writeText(link).then(function() {
                    frappe.show_alert( __("Link in der Zwischenablage") );
                  }, function() {
                     frappe.show_alert( __("Kein Zugriff auf Zwischenablage") );
                });
            } else {
                // open as QR code
                window.open("https://data.libracore.ch/phpqrcode/api/qrcode.php?content=" + encodeURIComponent(link) + "&ecc=H&size=6&frame=2", '_blank').focus();
            }
        }
    });
}
