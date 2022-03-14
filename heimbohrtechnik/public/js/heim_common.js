// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt
// Common functions

// 1 sec after start (has to be delayed after document ready)
window.onload = async function () {
    setTimeout(function() {
        // mark navbar
        var navbars = document.getElementsByClassName("navbar");
        if (navbars.length > 0) {
            if (window.location.hostname.includes("erp-test")) {
                navbars[0].style.backgroundColor = "#d68080";
                console.log("colored");
            } else if (frappe.defaults.get_user_default("company") === "MudEX AG") {
                navbars[0].style.backgroundColor = "#006400";
                console.log("colored MudEX");
            } else if (frappe.defaults.get_user_default("company").includes("Drilling")) {
                navbars[0].style.backgroundColor = "#f4ca16";
                console.log("colored Drilling Support");
            } else if (frappe.defaults.get_user_default("company").includes("Immo")) {
                navbars[0].style.backgroundColor = "#800000";
                console.log("colored Immo");
            }
        }
    }, 1000);
}

// document loaded
document.addEventListener("DOMContentLoaded", function(event) {
    var sheet = window.document.styleSheets[0];
    if (!frappe.user.has_role("System Manager")) {
        // disable deleting document attachments
        sheet.insertRule('.attachment-row>.close { display: none !important; }');
    }
});

function get_object_address(frm) {
    if (frm.doc.object) {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Object",
                'name': frm.doc.object
            },
            'callback': function(response) {
                var object = response.message;

                if (object) {
                    cur_frm.set_value('object_address_display', (object.object_street || "") + "<br>" + (object.object_location || ""));
                } 
            }
        });
    }
}

function get_object_description(frm) {
    if (frm.doc.object) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.utils.get_object_description",
            'args': {
                'object_name': frm.doc.object
            },
            'callback': function(response) {
                var html = response.message;

                if (html) {
                    cur_frm.set_value('object_description', html);
                } 
            }
        });
    }
}

function get_project_description(frm) {
    if (frm.doc.object) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.utils.get_project_description",
            'args': {
                'project': frm.doc.object
            },
            'callback': function(response) {
                var html = response.message;

                if (html) {
                    cur_frm.set_value('object_description', html);
                } 
            }
        });
    }
}

function set_conditional_net_total(frm) {
    var conditional_net_total = 0;
    var calculation_base = 0;
    if (frm.doc.items) {
        frm.doc.items.forEach(function (item) {
            if ((item.eventual !== 1) && (item.alternativ !== 1)) {
                conditional_net_total += item.amount;
                if (item.exclude_from_markup_discount !== 1) {
                    calculation_base += item.amount;
                }
            }
        });
    }
    cur_frm.set_value("conditional_net_total", conditional_net_total);
    cur_frm.set_value("markup_discount_base", calculation_base);
}

function set_conditional_grand_total(frm) {
    var conditional_grand_total = frm.doc.conditional_net_total - frm.doc.discount_amount;
    if (frm.doc.taxes) {
        frm.doc.taxes.forEach(function (tax) {
            conditional_grand_total = conditional_grand_total * ((tax.rate / 100) + 1);
        });
    }
    cur_frm.set_value("conditional_grand_total", conditional_grand_total); 
}

function recalculate_markups_discounts(frm) {
    var amount = frm.doc.markup_discount_base;
    var total_discount = 0;
    // calculate markups
    if (frm.doc.markup_positions) {
        frm.doc.markup_positions.forEach(function (markup) {
            if (markup.percent != 0) {
                var markup_amount = amount * (markup.percent / 100);
                frappe.model.set_value(markup.doctype, markup.name, "amount", markup_amount);
                frappe.model.set_value(markup.doctype, markup.name, "basis", amount);
            }
            amount += markup.amount;
            total_discount -= markup.amount;
        });
    }
    // calculate discounts
    if (frm.doc.discount_positions) {
        frm.doc.discount_positions.forEach(function (discount) {
            if (discount.percent != 0) {
                var discount_amount = amount * (discount.percent / 100);
                frappe.model.set_value(discount.doctype, discount.name, "amount", discount_amount);
                frappe.model.set_value(discount.doctype, discount.name, "basis", amount);
            }
            amount -= discount.amount;
            total_discount += discount.amount;
        });
    }
    // apply to overall discount
    update_additional_discount(frm, total_discount);
}

function update_additional_discount(frm, discount_amount) {
    if ((frm.doc.total !== 0 ) && (frm.doc.total >= discount_amount)) {
        cur_frm.set_value("additional_discount_percentage", (100 * discount_amount) / frm.doc.total);
        cur_frm.set_value("discount_amount", discount_amount);
    } else {
        cur_frm.set_value("additional_discount_percentage", null);
        cur_frm.set_value("discount_amount", discount_amount);
    }
    
    set_conditional_grand_total(frm);
}

function get_required_activities(frm, dt, dn) {
    var v = locals[dt][dn];
    if (v.supplier) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.filters.get_required_activities",
            'args': {
                'supplier': v.supplier,
                'activity': v.activity
            },
            'callback': function(response) {
                var activities = response.message;
                for (var i = 0; i < activities.length; i++) {
                    for (var r = 0; r < frm.doc.checklist.length; r++) {
                        if (frm.doc.checklist[r].activity === activities[i]) {
                            frappe.model.set_value(frm.doc.checklist[r].doctype, frm.doc.checklist[r].name, 
                                'supplier', v.supplier);
                            frappe.model.set_value(frm.doc.checklist[r].doctype, frm.doc.checklist[r].name, 
                                'supplier_name', v.supplier_name);
                        }
                    }
                }
                
                cur_frm.refresh_field('addresses');
            }
        });
    } else {
        frappe.model.set_value(v.doctype, v.name, "supplier_name", null);
    }
}

function prepare_checklist_and_permits(frm) {
    if ((!frm.doc.permits) || (frm.doc.permits.length === 0)) {
        // no permits, load standards
        frappe.call({
            "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_standard_permits",
            "callback": function(response) {
                var standard_permits = response.message;
                for (var i = 0; i < standard_permits.length; i++) {
                    var child = cur_frm.add_child('permits');
                    frappe.model.set_value(child.doctype, child.name, 'permit', standard_permits[i]);
                }
                cur_frm.refresh_field('permits');
            }
        });
    }
    if ((!frm.doc.checklist) || (frm.doc.checklist.length === 0)) {
        // no checklist positions, load standards
        frappe.call({
            "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_standard_activities",
            "callback": function(response) {
                var standard_activities = response.message;
                for (var i = 0; i < standard_activities.length; i++) {
                    var child = cur_frm.add_child('checklist');
                    frappe.model.set_value(child.doctype, child.name, 'activity', standard_activities[i]);
                }
                cur_frm.refresh_field('checklist');
            }
        });
    }
}

function get_mud_from_depth(depth) {
    // depth / 10 [m3] / 1.25 [t]
    return Math.floor((depth / 10) / 1.25);
}

function get_now() {
    var now = new Date();
    var timestamp = now.getFullYear() + "-" 
        + ((now.getMonth() + 1).toString().padStart(2, '0')) + "-" 
        + (now.getDate().toString().padStart(2, '0')) + " " 
        + (now.getHours().toString().padStart(2, '0')) + ":" 
        + (now.getMinutes().toString().padStart(2, '0')) + ":" 
        + (now.getSeconds().toString().padStart(2, '0'));
    return timestamp;
}

function create_mud_invoice(object_name) {
    frappe.call({
        'method': 'heimbohrtechnik.mudex.doctype.truck_delivery.truck_delivery.create_invoice',
        'args': {
            'object': object_name
        },
        'callback': function(response) {
            frappe.show_alert("<a href=\"/desk#Form/Sales Invoice/" 
                + response.message + "\">" + response.message + "</a>");
            cur_frm.reload_doc();
        }
    });
}

function cache_email_footer() {
    try {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Signature",
                'name': frappe.session.user
            },
            'callback': function(response) {
                var signature = response.message;

                if (signature) {
                    locals.email_footer = signature.email_footer;
                } 
            }
        });
    } catch (e) { 
        console.log("signature not found"); 
    }
}

function create_delivery_link(object, object_key, as_link) {
    frappe.prompt([
            {'fieldname': 'truck', 'fieldtype': 'Link', 'label': __('Truck'), 'options': 'Truck', 'reqd': 1}
        ],
        function(values){
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    'doctype': "Truck",
                    'name': values.truck
                },
                'callback': function(response) {
                    var customer = response.message.customer;
                    var link = window.location.origin + "/schlammanlieferung?truck=" + values.truck 
                        + "&customer=" + customer + "&object=" + object + "&key=" + object_key; 
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
        },
        __("Select truck"),
        __('OK')
    );
}

function show_pincode_information(object) {
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.utils.get_object_pincode_details",
        'args': {
            'object': object
        },
        'callback': function(response) {
            var details = response.message;
            if (details) {
                cur_frm.dashboard.add_comment( details.plz + " (" + details.city + "): " 
                    + details.bohrmeterpreis.toFixed(2) + " CHF/m, Arteser: "
                    + ((details.arteser) ? "ja" : "nein") 
                    + ", " + (details.hinweise || "keine Hinweise") 
                , 'blue', true);
            }
        }
    });
}

function select_naming_series(frm) {
    if (frm.doc.doctype === "Quotation") {
        if (frm.doc.company.includes("MudEX")) {
            cur_frm.set_value("naming_series", "AN-MX-.YY.#####");
        } else if (frm.doc.company.includes("Drilling")) {
            cur_frm.set_value("naming_series", "AN-HDSE-.YY.#####");
        } else if (frm.doc.company.includes("Immo")) {
            cur_frm.set_value("naming_series", "AN-IH-.YY.#####");
        }
    } else if (frm.doc.doctype === "Sales Order") {
        if (frm.doc.company.includes("MudEX")) {
            cur_frm.set_value("naming_series", "AB-MX-.YY.#####");
        } else if (frm.doc.company.includes("Drilling")) {
            cur_frm.set_value("naming_series", "AB-HDSE-.YY.#####");
        } else if (frm.doc.company.includes("Immo")) {
            cur_frm.set_value("naming_series", "AB-IH-.YY.#####");
        }
    } else if (frm.doc.doctype === "Delivery Note") {
        if (frm.doc.company.includes("MudEX")) {
            cur_frm.set_value("naming_series", "LS-MX-.YY.#####");
        } else if (frm.doc.company.includes("Drilling")) {
            cur_frm.set_value("naming_series", "LS-HDSE-.YY.#####");
        } else if (frm.doc.company.includes("Immo")) {
            cur_frm.set_value("naming_series", "LS-IH-.YY.#####");
        }
    } else if (frm.doc.doctype === "Sales Invoice") {
        if (frm.doc.is_return === 1) {
            if (frm.doc.company.includes("MudEX")) {
                cur_frm.set_value("naming_series", "GS-MX-.YY.#####");
            } else if (frm.doc.company.includes("Drilling")) {
                cur_frm.set_value("naming_series", "GS-HDSE-.YY.#####");
            } else if (frm.doc.company.includes("Immo")) {
                cur_frm.set_value("naming_series", "GS-IH-.YY.#####");
            } else {
                cur_frm.set_value("naming_series", "GS-.YY.#####");
            }
        } else {
            if (frm.doc.company.includes("MudEX")) {
                cur_frm.set_value("naming_series", "RE-MX-.YY.#####");
            } else if (frm.doc.company.includes("Drilling")) {
                cur_frm.set_value("naming_series", "RE-HDSE-.YY.#####");
            } else if (frm.doc.company.includes("Immo")) {
                cur_frm.set_value("naming_series", "RE-IH-.YY.#####");
            }
        }
    } else if (frm.doc.doctype === "Payment Reminder") {
        if (frm.doc.company.includes("MudEX")) {
            cur_frm.set_value("naming_series", "MA-MX-.YY.#####");
        } else if (frm.doc.company.includes("Drilling")) {
            cur_frm.set_value("naming_series", "MA-HDSE-.YY.#####");
        } else if (frm.doc.company.includes("Immo")) {
            cur_frm.set_value("naming_series", "MA-IH-.YY.#####");
        }
    }
}
