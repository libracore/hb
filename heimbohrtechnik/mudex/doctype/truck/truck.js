// Copyright (c) 2021-2025, libracore AG and contributors
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
            // button to create truck gas receipt link
            frm.add_custom_button("<i class='fa fa-money'></i> Tankbeleg", function() {
                create_gas_receipt_link(frm, true);
            });
            // button to create truck delivery link
            frm.add_custom_button("<i class='fa fa-truck'></i> LKW-Abholung", function() {
                create_truck_delivery(frm, true);
            });
        }
    }
});

function create_delivery_link(frm, as_link) {
    var link = window.location.origin + "/schlammanlieferung?truck=" + frm.doc.name 
        + "&customer=" + frm.doc.customer; 
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

function create_gas_receipt_link(frm, as_link) {
    var link = window.location.origin + "/tankbeleg?truck=" + frm.doc.name 
        + "&key=" + frm.doc.key; 
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

function create_truck_delivery(frm, as_link) {
    var d = new frappe.ui.Dialog({
        'fields': [
            {'fieldname': 'item', 'fieldtype': 'Link', 'options': 'Item', 'label': __("Item")}
        ],
        'primary_action': function(){
            d.hide();
            var values = d.get_values();
            var link = window.location.origin + "/lkwabholung/lkwabholung?truck=" + frm.doc.name 
                + "&customer=" + frm.doc.customer + "&key=" + frm.doc.key + "&item=" + values.item; 
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
        },
        'primary_action_label': __('OK'),
        'title': __("LKW-Abholungslink erstellen")
    });
    d.show();
}
