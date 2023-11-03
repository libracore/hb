// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Invoice', {
    object: function(frm) {
        get_object_address(frm);
        get_project_description(frm);
    },
    refresh: function(frm) {
        // fetch sales invoice object text if new document and has object
        if ((frm.doc.__islocal) && (frm.doc.object)) {
            get_project_description(frm);
        }
        
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
        
        // check duplicate discount
        if (frm.doc.docstatus === 0) {
            check_duplicate_discounts(frm);
        }
        
        // check if there are available akonto positions
        if (frm.doc.__islocal) {
            find_akontos(frm);
        }
        
        //Validate prices with sales order
        if (!frm.doc.__islocal) {
            validate_prices(frm);
        }
    },
    before_save: function(frm) {
        set_conditional_net_total(frm);
        recalculate_markups_discounts(frm);
        
        // set naming series (for company)
        if (frm.doc.__islocal) {
            select_naming_series(frm);
        }
        
        // check and apply accrual
        check_warranty(frm);
    },
    after_cancel: function(frm) {
        // if this is a MudEX invoice to HB, cancel related invoice
        if ((frm.doc.company.includes("MudEX")) && (frm.doc.customer === "K-00010")) {
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.utils.cancel_mudex_invoice',
                'args': {
                    'reference': frm.doc.name
                },
                'callback': function(r) {
                    if (r.message) {
                        frappe.show_alert(r.message + " wurde auch storniert");
                    }
                }
            });
        }
        
        // if there is an akonto booking, cancel
        cancel_akonto_booking(frm);
    },
    on_submit: function(frm) {
        check_create_akonto_booking(frm);
        
        // create and attach PDF
        frappe.call({
            'method': 'erpnextswiss.erpnextswiss.attach_pdf.attach_pdf',
            'args': {
                'doctype': frm.doc.doctype,
                'docname': frm.doc.name,
                'print_format': "Ausgangsrechnung"
            },
            'callback': function(response) {
                cur_frm.reload_doc();
            }
        });
    }
});

frappe.ui.form.on('Discount Position', {
    discount: function(frm, dt, dn) {
        update_additional_discount(frm);
    },
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});

frappe.ui.form.on('Markup Position', {
    discount: function(frm, dt, dn) {
        update_additional_discount(frm);
    },
    percent: function(frm, dt, dn) {
        recalculate_markups_discounts(frm);
    },
    markup_positions_add: function(frm, dt, dn) {
        set_conditional_net_total(frm);
    }
});

function check_duplicate_discounts(frm) {
    var sales_order = null;
    for (var i = 0; i < frm.doc.items.length; i++) {
        if (frm.doc.items[i].sales_order) {
            sales_order = frm.doc.items[i].sales_order;
            break;
        }
    }
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_invoiced_markup_discounts",
        "args": {
            "sales_order": sales_order
        },
        "async": false,
        "callback": function(response) {
            var positions = response.message;
            console.log(positions);
            // check markups
            if (frm.doc.markup_positions) {
                for (var m = frm.doc.markup_positions.length - 1; m >= 0; m--) {
                    for (var i = 0; i < response.message.length; i++) {
                        if ((frm.doc.markup_positions[m].description === response.message[i].description)
                            && (response.message[i].parent !== frm.doc.name)) {
                            // already in another invoice - remove
                            cur_frm.get_field("markup_positions").grid.grid_rows[m].remove();
                            frappe.show_alert(__("Doppelten Zuschlag {0} entfernt").replace("{0}", frm.doc.markup_positions[m].description))
                            break;
                        }
                    }
                }
            }
            if (frm.doc.discount_positions) {
                for (var m = frm.doc.discount_positions.length - 1; m >= 0; m--) {
                    for (var i = 0; i < response.message.length; i++) {
                        if ((frm.doc.discount_positions[m].description === response.message[i].description)
                            && (response.message[i].parent !== frm.doc.name)) {
                            // already in another invoice - remove
                            cur_frm.get_field("discount_positions").grid.grid_rows[m].remove();
                            frappe.show_alert(__("Doppelten Abzug {0} entfernt").replace("{0}", frm.doc.discount_positions[m].description))
                            break;
                        }
                    }
                }
            }
            cur_frm.refresh_fields(["markup_positions", "discount_positions"]);
        }
    });
}

function find_akontos(frm) {
    if ((frm.doc.items) && (frm.doc.items.length > 0)) {
        frappe.call({
            "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_available_akonto",
            "args": {
                "sales_order": frm.doc.items[0].sales_order
            },
            "callback": function(response) {
                var akonto = response.message;
                console.log(akonto);
                if (akonto.length > 0) {
                    for (var a = 0; a < akonto.length; a++) {
                        add_akonto(
                            "Akonto vom " + new Date(akonto[a].date).toLocaleString("de", {'day': '2-digit', 'month': '2-digit', 'year': 'numeric'}) + " (" + frm.doc.currency + " " + akonto[a].amount.toLocaleString("de-ch") + " inkl. MwSt)", 
                            akonto[a].amount, 
                            akonto[a].net_amount, 
                            akonto[a].reference
                        );
                    }
                }
            }
        });
    }
}

function add_akonto(text, amount, net_amount, reference) {
    var child = cur_frm.add_child('discount_positions');
    frappe.model.set_value(child.doctype, child.name, 'description', text);
    frappe.model.set_value(child.doctype, child.name, 'amount', net_amount);
    frappe.model.set_value(child.doctype, child.name, 'akonto_net_amount', net_amount);
    frappe.model.set_value(child.doctype, child.name, 'akonto_gross_amount', amount);
    frappe.model.set_value(child.doctype, child.name, 'akonto_invoice_item', reference);
    cur_frm.refresh_field('discount_positions');
}

// This function checks if an akonto has been used and books it
function check_create_akonto_booking(frm) {
    if (frm.doc.discount_positions) {
        for (var a = 0; a < frm.doc.discount_positions.length; a++) {
            if (frm.doc.discount_positions[a].akonto_invoice_item) {
                frappe.call({
                    "method": "heimbohrtechnik.heim_bohrtechnik.utils.book_akonto",
                    "args": {
                        "sales_invoice": frm.doc.name,
                        "net_amount": frm.doc.discount_positions[a].akonto_net_amount
                    },
                    "callback": function(response) {
                        console.log("Akonto booked: " + response.message);

                    }
                });
            }
        }
    }
}

// This function cancels akonto bookings (if present)
function cancel_akonto_booking(frm) {
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.utils.cancel_akonto",
        "args": {
            "sales_invoice": frm.doc.name
        }
    });
}

function validate_prices(frm) {
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.sales_invoice.validate_prices",
        'args': {
            'objekt': frm.doc.object
        },
        'callback': function(response) {
            var details = response.message;
            if ((details[0]) && (details[0].length > 0)) {
                cur_frm.dashboard.add_comment( "Achtung, Preise für folgende Artikel unterschiedlich zu Sales Order " + details[1] + ":" +
                for (let i = 0; i < details[0].length; i++) {
                    "Hallo"
                }), 'red', true);
            }
        }
    });
}
