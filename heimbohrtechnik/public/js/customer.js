frappe.ui.form.on('Customer', {
    setup(frm) {
        frm.set_query('default_sales_taxes_and_charges', 'accounts', function(doc, cdt, cdn) {
            var d = locals[cdt][cdn];
            var filters = {
                'company': d.company
            }
            return {'filters': filters}
        });
        frm.set_query('default_purchase_taxes_and_charges', 'accounts', function(doc, cdt, cdn) {
            var d = locals[cdt][cdn];
            var filters = {
                'company': d.company
            }
            return {'filters': filters}
        });
    },
    before_save(frm) {
        if (!frm.doc.__islocal) {
            set_first_address(frm);
        }
    },
    refresh(frm) {
        frm.add_custom_button("<i class='fa fa-calendar'></i>  Link", function() {
            get_calendar_link(frm);
        }, __("Bohrplan") );
        frm.add_custom_button("Löschen", function() {
            cur_frm.set_value("key", null);
            cur_frm.save();
        }, __("Bohrplan") );
        if ((!frm.doc.__islocal) && (frappe.user.has_role("Sales Master Manager"))) {
            frm.add_custom_button(__("Umsatzentwicklung"), function() {
                frappe.set_route("query-report", "Customer sales trend", {"customer": frm.doc.name});
            });
        }
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Drilling Statistics"), function() {
                frappe.set_route("query-report", "Drilling Statistics", {"customer": frm.doc.name});
            });
            frm.add_custom_button("Kontoauszug", function() {
                frappe.set_route("query-report", "Kundenauszug", {"party_type": "Customer", "customer": frm.doc.name});
            });
        }
    }
});

function set_first_address(frm) {
    frappe.call({
        'method': 'erpnextswiss.scripts.crm_tools.get_primary_customer_address',
        'args': {
            'customer': frm.doc.name
        },
        'async': false,
        'callback': function(response) {
            if (response.message) {
                var address = response.message;
                var adr_line = address.address_line1 + ", " + address.pincode + " " + address.city;
                cur_frm.set_value('hauptadresse', adr_line);
            }
        }
    });
}

function get_calendar_link(frm) {
    if (!frm.doc.key) {
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_key',
            'async': false,
            'callback': function(response) {
                if (response.message) {
                    cur_frm.set_value('key', response.message);
                    copy_calendar_link(true);
                    cur_frm.save();
                }
            }
        });
    } else {
        copy_calendar_link(true);
    }
}

function copy_calendar_link(as_link) {
    var link = window.location.origin + "/bohrplan?customer=" + cur_frm.doc.name
        + "&key=" + cur_frm.doc.key; 
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
