// Copyright (c) 2021-2024, libracore AG and contributors
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
            } else if (frappe.defaults.get_user_default("company").includes("HPT Solutions")) {
                navbars[0].style.backgroundColor = "#ffa500";
                console.log("colored Immo");
            }
        }
    }, 1000);
}

// document loaded
document.addEventListener("DOMContentLoaded", function(event) {
    var sheet = window.document.styleSheets[0];
    if ((!frappe.user.has_role("System Manager")) && (!frappe.user.name === "beuggert@hb-ag.ch")) {
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
    if ((frm.doc.markup_positions) && (frm.doc.markup_positions.length > 0)) {
        frm.doc.markup_positions.forEach(function (markup) {
            if (markup.after_discounts === 0) {
                if (markup.percent !== 0) {
                    var markup_amount = amount * (markup.percent / 100);
                    frappe.model.set_value(markup.doctype, markup.name, "amount", markup_amount);
                    frappe.model.set_value(markup.doctype, markup.name, "basis", amount);
                }
                amount += markup.amount;
                total_discount -= markup.amount;
            }
        });
    }
    // calculate discounts
    if ((frm.doc.discount_positions) && (frm.doc.discount_positions.length > 0)) {
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
    // markups after discounts
    if ((frm.doc.markup_positions) && (frm.doc.markup_positions.length > 0)) {
        frm.doc.markup_positions.forEach(function (markup) {
            if (markup.after_discounts === 1) {
                if (markup.percent !== 0) {
                    var markup_amount = amount * (markup.percent / 100);
                    frappe.model.set_value(markup.doctype, markup.name, "amount", markup_amount);
                    frappe.model.set_value(markup.doctype, markup.name, "basis", amount);
                }
                amount += markup.amount;
                total_discount -= markup.amount;
            }
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
                fill_permits(frm, standard_permits);
            }
        });
    }
    if ((!frm.doc.checklist) || (frm.doc.checklist.length === 0)) {
        // no checklist positions, load standards
        frappe.call({
            "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_standard_activities",
            "callback": function(response) {
                var standard_activities = response.message;
                fill_checklist(frm, standard_activities);
            }
        });
    }
}

function fill_permits(frm, permits) {
    for (var i = 0; i < permits.length; i++) {
        var child = cur_frm.add_child('permits');
        frappe.model.set_value(child.doctype, child.name, 'permit', permits[i]);
    }
    cur_frm.refresh_field('permits');
}

function fill_checklist(frm, activities) {
    for (var i = 0; i < activities.length; i++) {
        var child = cur_frm.add_child('checklist');
        frappe.model.set_value(child.doctype, child.name, 'activity', activities[i]);
    }
    cur_frm.refresh_field('checklist');
}

function get_mud_from_depth(depth) {
    // depth / 10 [m3] * 1.25 [t]
    return Math.floor((depth / 10) * 1.25);
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

function show_insurance_information(project) {
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.report.versicherungsanmeldung.versicherungsanmeldung.has_insurance",
        'args': {
            'project': project
        },
        'callback': function(response) {
            var details = response.message;
            if ((details) && (details.length > 0)) {
                cur_frm.dashboard.add_comment( "Versicherungen aus Auftrag "
                    + details[0].sales_order + ": "
                    + details[0].insurances
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

// compute wall strength according to DIN 8074
function get_wall_strength_from_diameter(diameter, pressure_level) {
    var wall_strength = 0;
    switch (diameter) {
        case 32:
            if (pressure_level.includes("PN16")) {
                wall_strength = 2.9;
            } else if (pressure_level.includes("PN20")) {
                wall_strength = 0;
            } else if (pressure_level.includes("PN25")) {
                wall_strength = 0;
            } else if (pressure_level.includes("PN30")) {
                wall_strength = 0;
            } else if (pressure_level.includes("PN35")) {
                wall_strength = 0;
            } else if (pressure_level.includes("PN40")) {
                wall_strength = 0;
            }
            break;
        case 40:
            if (pressure_level.includes("PN16")) {
                wall_strength = 3.7;
            } else if (pressure_level.includes("PN20")) {
                wall_strength = 4.5;
            } else if (pressure_level.includes("PN25")) {
                wall_strength = 5.4;
            } else if (pressure_level.includes("PN30")) {
                wall_strength = 7.0;
            } else if (pressure_level.includes("PN35")) {
                wall_strength = 0;
            } else if (pressure_level.includes("PN40")) {
                wall_strength = 0;
            }
            break;
        case 42:        
            if (pressure_level.includes("PN16")) {
                wall_strength = 3.5;
            } else if (pressure_level.includes("PN20")) {
                wall_strength = 4.7;
            } else if (pressure_level.includes("PN25")) {
                wall_strength = 5.7;
            } else if (pressure_level.includes("PN30")) {
                wall_strength = 7.0;
            } else if (pressure_level.includes("PN35")) {   // hipress
                wall_strength = 3.5;
            } else if (pressure_level.includes("PN40")) {
                wall_strength = 0;
            }
            break;
        case 50:        // vertex
            if (pressure_level.includes("PN16")) {
                wall_strength = 4.6;
            } else if (pressure_level.includes("PN20")) {
                wall_strength = 5.6;
            } else if (pressure_level.includes("PN25")) {
                wall_strength = 6.9;
            } else if (pressure_level.includes("PN30")) {
                wall_strength = 7.9;
            } else if (pressure_level.includes("PN35")) {
                wall_strength = 0;
            } else if (pressure_level.includes("PN40")) {
                wall_strength = 0;
            }
            break;
    }
    return wall_strength;
}

function order_ews(object, callback=null) {
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.utils.order_ews",
        'args':{
            'object': object
        },
        'callback': function(r)
        {
            var po = r.message;
            if (po.error) {
                frappe.msgprint( __(po.error) );
            } else if (po.po) {
                window.open("/desk#Form/Purchase Order/" + po.po, '_blank').focus();
            }
            if (callback) {
                callback();
            }
        }
    });
}

// This will apply warranty accruals if applicable
function check_warranty(frm) {
    // find sales order
    var sales_order = null;
    for (var i = 0; i < frm.doc.items.length; i++) {
        if (frm.doc.items[i].sales_order) {
            sales_order = frm.doc.items[i].sales_order;
            break;
        }
    }
    if (sales_order) {
        if (frm.doc.title === "Teilrechnung") {
            // get percentage
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.utils.get_warranty_accural_percent',
                'args': {
                    'sales_order': sales_order
                },
                'async': false,
                'callback': function(r) {
                    var accrual = r.message;
                    // apply to deductions
                    if (accrual > 0) {
                        var applied = false;
                        // check if this is already in the list
                        for (var i = 0; i < frm.doc.discount_positions.length; i++) {
                            if (frm.doc.discount_positions[i].description.includes("Garantierückbehalt")) {
                                frappe.model.set_value(frm.doc.discount_positions[i].doctype, frm.doc.discount_positions[i].name,
                                'percent', accrual);
                                applied = true;
                                break;
                            }
                        }
                        if (!applied) {
                            // add if it was not in the list
                            var child = cur_frm.add_child('discount_positions');
                            frappe.model.set_value(child.doctype, child.name, 'description', "Garantierückbehalt");
                            frappe.model.set_value(child.doctype, child.name, 'percent', accrual);
                        }
                    }
                }
            });
            // update calculation
            set_conditional_net_total(frm);
            recalculate_markups_discounts(frm);
        } else if (frm.doc.title === "Schlussrechnung") {
            // remove warranty accrual from discounts
            for (var i = (frm.doc.discount_positions.length - 1); i >= 0 ; i--) {
                if (frm.doc.discount_positions[i].description.includes("Garantierückbehalt")) {
                    cur_frm.get_field("discount_positions").grid.grid_rows[i].remove();
                }
            }
            // compute earlier accruals
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.utils.get_applied_warranty_accruals',
                'args': {
                    'sales_order': sales_order
                },
                'async': false,
                'callback': function(r) {
                    var accrual = r.message;
                    if (accrual > 0) {
                        // apply to markup
                        var applied = false;
                        // check if this is already in the list
                        for (var i = 0; i < frm.doc.markup_positions.length; i++) {
                            if (frm.doc.markup_positions[i].description.includes("Garantierückbehalt")) {
                                frappe.model.set_value(frm.doc.markup_positions[i].doctype, frm.doc.markup_positions[i].name,
                                'percent', 0);
                                frappe.model.set_value(frm.doc.markup_positions[i].doctype, frm.doc.markup_positions[i].name,
                                'amount', accrual);
                                applied = true;
                                break;
                            }
                        }
                        if (!applied) {
                            // add if it was not in the list
                            var child = cur_frm.add_child('markup_positions');
                            frappe.model.set_value(child.doctype, child.name, 'description', "Garantierückbehalt");
                            frappe.model.set_value(child.doctype, child.name, 'amount', accrual);
                            frappe.model.set_value(child.doctype, child.name, 'after_discounts', 1);
                        }
                    }
                }
            });
        }
    }
}

function add_construction_site_description_button(frm, object) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description.has_construction_site_description',
        'args': {'object': object},
        'callback': function(response) {
            var btn_class = "btn-warning";
            if ((response.message) && (response.message.length > 0)) {
                btn_class = "btn-primary";
            }
            frm.add_custom_button( __("Construction Site Description"), function() {
                frappe.call({
                    'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description.find_create_construction_site_description',
                    'args': {'object': object},
                    'callback': function(response) {
                        if (response.message) {
                            frappe.set_route("Form", "Construction Site Description", response.message);
                        }
                    }
                });
            }).addClass(btn_class);
        }
    });
}


function check_display_siblings(dt, dn) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.has_siblings',
        'args': {
            'doctype': dt,
            'name': dn
        },
        'callback': function(response) {
            var siblings = response.message;
            if (siblings.length > 0) {
                var comment = __('This document has siblings') + ": ";
                for (var i = 0; i < siblings.length; i++) {
                    comment += "<a href='/desk#Form/" + dt + "/" + siblings[i].name + "'>" + siblings[i].name + "</a> ";
                }
                cur_frm.dashboard.add_comment(comment, 'blue', true);
            }
        }
    });
}

function get_kw(date) {
    var current_date = new Date(date);
    var start_date =  new Date(current_date.getFullYear(), 0, 1);
    var days =  Math.floor((current_date - start_date) / (24 * 60 * 60 * 1000));
    var week = Math.ceil(( current_date.getDay() + 1 + days) / 7);
    return week;
}
