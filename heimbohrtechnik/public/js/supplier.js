// Copyright (c) 2021-2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier', {
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
        frm.set_query('trough_address', 'capabilities', function(frm, cdt, cdn) {
            var d = locals[cdt][cdn];
            return {
                'query': "frappe.contacts.doctype.address.address.address_query",
                'filters': {
                    "link_doctype": "Supplier",
                    "link_name": frm.name || null
                }
            }
        });
    },
    refresh(frm) {
        if ((frm.doc.capabilities) 
            && (frm.doc.capabilities.length > 0)
            && (frm.doc.capabilities[0].activity == "Hotel") 
            && (!frm.doc.gps_latitude) 
            && (!locals.gps_requested)) {
            // prevent endless loop when gps cannot be found
            locals.gps_requested = true;
            set_gps_coordinates(frm);
        }
        if (!frm.doc.__islocal) {
            frm.add_custom_button("Kontoauszug", function() {
                frappe.set_route("query-report", "Kundenauszug", {"party_type": "Supplier", "supplier": frm.doc.name});
            });
        }
    },
    before_save(frm) {
        if (!frm.doc.__islocal) {
            set_first_address(frm);
            set_phone(frm);
        }
        compile_remarks(frm);
        set_supplier_group(frm);
    }
});

frappe.ui.form.on('Supplier Activity', {
    trough_address(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.trough_address) {
            fetch_gps(cdt, cdn, row.trough_address);
        }
    }
});

function set_first_address(frm) {
    frappe.call({
        'method': 'erpnextswiss.scripts.crm_tools.get_primary_supplier_address',
        'args': {
            'supplier': frm.doc.name
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

function set_phone(frm) {
    frappe.call({
        'method': 'erpnextswiss.scripts.crm_tools.get_primary_supplier_contact',
        'args': {
            'supplier': frm.doc.name
        },
        'async': false,
        'callback': function(response) {
            if (response.message) {
                var contact = response.message;
                var contact_line = contact.phone;
                cur_frm.set_value('telefon', contact_line);
            }
        }
    });
}

function set_gps_coordinates(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.migration.update_hotel_coordinates',
        'args': {
            'supplier': frm.doc.name
        },
        'callback': function(response) {
            cur_frm.reload_doc();
        }
    });
}

function compile_remarks(frm) {
    if (frm.doc.capabilities) {
        var remarks = [];
        for (var i = 0; i < frm.doc.capabilities.length; i++) {
            if (frm.doc.capabilities[i].remarks) {
                remarks.push(frm.doc.capabilities[i].remarks);
            }
        }
        cur_frm.set_value("remarks", remarks.join(", "));
    }
}

function set_supplier_group(frm) {
    var supplier_group = "Lieferant";
    if (frm.doc.capabilities) {
        for (var i = 0; i < frm.doc.capabilities.length; i++) {
            if (frm.doc.capabilities[i].activity == "Hotel") {
                supplier_group = "Hotel";
            }
        }
    }
    cur_frm.set_value("supplier_group", supplier_group);
}

function fetch_gps(cdt, cdn, address) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.locator.find_gps_for_address',
        'args': {
            'address': address
        },
        'callback': function(response) {
            if ((response.message) && (response.message.lat) && (response.message.lon)) {
                frappe.model.set_value(cdt, cdn, 'gps_lat', response.message.lat);
                frappe.model.set_value(cdt, cdn, 'gps_long', response.message.lon);
            }
        }
    });
}
