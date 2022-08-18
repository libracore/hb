// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

// child table filter sets
cur_frm.fields_dict.addresses.grid.get_field('address').get_query =   
    function(frm, dt, dn) {   
        var v = locals[dt][dn];
        return {
            query: "frappe.contacts.doctype.address.address.address_query",
            filters: {
                "link_doctype": v.dt,
                "link_name": v.party || null
            }
        }
    }; 

cur_frm.fields_dict.addresses.grid.get_field('party').get_query =   
    function(frm, dt, dn) {   
        var filters = {};
        var v = locals[dt][dn];
        if (v.dt === "Supplier") {
            filters = {
                'query': 'heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability',
                'filters': {
                    'capability': v.address_type
                }
            }
        }
        return filters
    };

cur_frm.fields_dict.addresses.grid.get_field('contact').get_query =   
    function(frm, dt, dn) {
        var v = locals[dt][dn];
        return {
            query: "frappe.contacts.doctype.contact.contact.contact_query",
            filters: {
                "link_doctype": v.dt,
                "link_name": v.party || null
            }
        }
    };

cur_frm.fields_dict.checklist.grid.get_field('supplier').get_query =   
    function(frm, dt, dn) {   
        var filters = {};
        var v = locals[dt][dn];
            filters = {
                'query': 'heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability',
                'filters': {
                    'capability': v.activity
                }
            }
        return filters
    };
    
frappe.ui.form.on('Object', {
    refresh: function(frm) {
        // show permits & checklist
        try {
            document.querySelectorAll("[data-fieldname='checklist']")[0].parentElement.parentElement.parentElement.parentElement.style.display = "Block";
        } catch { /* do nothing */ }
        if (!frm.doc.__islocal) {
            // check if project exists
            frappe.call({
                method: 'has_project',
                doc: frm.doc,
                callback: function(response) {
                    if (response.message === 1) {
                        // has a project
                        frm.add_custom_button( frm.doc.name, function() {
                            frappe.set_route("Form", "Project", frm.doc.name);
                        }).addClass("btn-primary");
                        // hide permits & checklist
                        try {
                            document.querySelectorAll("[data-fieldname='checklist']")[0].parentElement.parentElement.parentElement.parentElement.style.display = "None";
                        } catch { /* do nothing */ }
                    } else {
                        // has no project
                        frm.add_custom_button(__('Create project'), function() {
                            frappe.call({
                                method:"create_project",
                                doc: frm.doc,
                                callback: function(response) {
                                    cur_frm.reload_doc();
                                }
                            });
                        }).addClass("btn-primary");
                    }
                }
            });
            // button to create truck link
            frm.add_custom_button("<i class='fa fa-truck'></i> Link", function() {
                create_delivery_link(frm.doc.name, frm.doc.object_key, true);
            }, "MudEX");
            // button to create truck QR code
            frm.add_custom_button("<i class='fa fa-truck'></i> QR-Code", function() {
                create_delivery_link(frm.doc.name, frm.doc.object_key, false);
            }, "MudEX");
            // fill delivered mud
            frappe.call({
                'method': 'get_delivered_mud',
                'doc': frm.doc,
                'callback': function(response) {
                    cur_frm.set_df_property('delivered_mud','options','<label class="control-label" style="padding-right: 0px;">' + __("Delivered Mud") + '</label><div class="control-value like-disabled-input" style="">' + (response.message || 0).toLocaleString() + '</div><p class="help-box small text-muted hidden-xs">kg</p>');
                }
            });
            // check if mud can be invoiced
            frappe.call({
                'method': 'heimbohrtechnik.mudex.doctype.truck_delivery.truck_delivery.has_invoiceable_mud',
                'args': {'object': frm.doc.name},
                'callback': function(response) {
                    if (response.message) {
                        frm.add_custom_button( __("Abrechnen"), function() {
                            create_mud_invoice(frm.doc.name);
                        }, "MudEX");
                    }
                }
            });
            // navigate to environment
            if (frm.doc.gps_coordinates) {
                frm.add_custom_button("Umgebung", function() {
                    window.location = ("/desk#object-overview?object=" + frm.doc.name);
                    location.reload(true); 
                });
            }
            // button to order probes
            frm.add_custom_button("EWS bestellen", function() {
                order_ews(frm.doc.name);
            });
            // add button to open construction site description
            add_construction_site_description_button(frm, frm.doc.name)
        } else {
            if ((!frm.doc.addresses) || (frm.doc.addresses.length === 0)) {
                // fresh document, no addresses - load template
                frappe.call({
                    "method": "heimbohrtechnik.heim_bohrtechnik.doctype.heim_settings.heim_settings.get_address_template",
                    "callback": function(response) {
                        var address_types = response.message;
                        for (var i = 0; i < address_types.length; i++) {
                            var child = cur_frm.add_child('addresses');
                            frappe.model.set_value(child.doctype, child.name, 'address_type', address_types[i].type);
                            frappe.model.set_value(child.doctype, child.name, 'dt', address_types[i].dt);
                        }
                        cur_frm.refresh_field('addresses');
                    }
                });
            }
            prepare_checklist_and_permits(frm);
        }
    },
    before_save: function(frm) {
        var depth = 0;
        (frm.doc.ews_specification || []).forEach(function (drilling) {
            depth += ((drilling.ews_count || 0) * (drilling.ews_depth || 0));
        });
        cur_frm.set_value('expected_mud', 1000 * get_mud_from_depth(depth));    // store in kg not t
    },
    validate: function(frm) {
        // check if all mandatory permits are present
        if ((frm.doc.permits) && (frm.doc.permits.length > 0)) {
            frappe.call({
                "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_mandatory_permits",
                "async": 0,
                "callback": function(response) {
                    var mandatory_permits = response.message;
                    var found = false;
                    for (var i = 0; i < mandatory_permits.length; i++) {
                        for (var j = 0; j < frm.doc.permits.length; j++) {
                            if (frm.doc.permits[j].permit === mandatory_permits[i]) {
                                found = true;
                                break;
                            }
                        }
                        if (!found) {
                            frappe.msgprint( ( __("Permit {0} is mandatory but missing") ).replace("{0}", mandatory_permits[i]), __("Validation") );
                            frappe.validated=false;
                        } 
                    }
                }
            });
        } else {
            frappe.msgprint( __("Are there really no required permits?"), __("Validation") );
        }
    },
    button_search_plz: function(frm) {
        search_plz(frm);
    },
    object_street: function(frm) {
        update_gps(frm);
    },
    plz: function(frm) {
        update_location(frm);
        if ((frm.doc.__islocal) && (frm.doc.plz)) {
            update_permits_on_plz(frm);
        }
    },
    city: function(frm) {
        update_location(frm);
    },
    kanton: function(frm) {
        update_location(frm);
    },
    ch_coordinates: function(frm) {
        convert_ch_to_gps(frm);
    },
    gps_coordinates: function(frm) {
        convert_gps_to_ch(frm);
    },
    button_open_map: function(frm) {
        if (frm.doc.ch_coordinates) {
            var parts = frm.doc.ch_coordinates.split("/");
            var e= parts[0].replaceAll(" ", "").replaceAll("'", "");
            var n = parts[1].replaceAll(" ", "").replaceAll("'", "");
            frappe.call({
                "method": "erpnextswiss.erpnextswiss.swisstopo.get_swisstopo_url_from_ch",
                "args": {
                    "x": e,
                    "y": n,
                    "language": "de",
                    "zoom": 12
                },
                "callback": function(response) {
                    var url = response.message;
                    window.open(url, '_blank');
                }
            });
        } else if (frm.doc.plz) {
            frappe.call({
                "method": "erpnextswiss.erpnextswiss.swisstopo.get_swisstopo_url_from_pincode",
                "args": {
                    "pincode": frm.doc.plz,
                    "language": "de",
                    "zoom": 7
                },
                "callback": function(response) {
                    var url = response.message;
                    window.open(url, '_blank');
                }
            });
        }
    },
    cooling_capacity: function(frm) {
        recalculate_drilling_meter(frm);
    },
    withdrawal_capacity: function(frm) {
        recalculate_drilling_meter(frm);
    },
    drilling_method: function(frm) {
        if (frm.doc.drilling_method) {
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    'doctype': "Drilling Method",
                    'name': frm.doc.drilling_method
                },
                'callback': function(response) {
                    cur_frm.set_value('load_type', response.message.load_type);
                } 
            });
        }
    },
    accompaniment: function(frm) {
        if (frm.doc.accompaniment == 1) {
            // make sure geologist is in address and checklist
            check_add_address(frm, "Geologe");
            check_add_checklist(frm, "Geologe");
        }
    }
});

frappe.ui.form.on('Object EWS', {
    ews_count: function(frm, cdt, cdn) {
        update_ews_details(frm, cdt, cdn);
    },
    ews_depth: function(frm, cdt, cdn) {
        update_ews_details(frm, cdt, cdn);
    },
    ews_diameter: function(frm, cdt, cdn) {
        update_ews_details(frm, cdt, cdn);
    },
    ews_diameter_unit: function(frm, cdt, cdn) {
        update_ews_details(frm, cdt, cdn);
    },
    pressure_level: function(frm, cdt, cdn) {
        update_ews_details(frm, cdt, cdn);
    }    
});

frappe.ui.form.on('Object Address', {
    address: function(frm, dt, dn) {
        var v = locals[dt][dn];
        if (v.address) {
            frappe.call({
                "method": "frappe.client.get",
                "args": {
                    "doctype": "Address",
                    "name": v.address
                },
                "callback": function(response) {
                    var address = response.message;
                    var html = v.party_name;
                    html += "<br>" + address.address_line1;
                    if (address.address_line2) {
                        html += "<br>" + address.address_line2;
                    }
                    html += "<br>" + address.pincode + " " + address.city;
                    html += "<br>" + address.country;
                    frappe.model.set_value(dt, dn, 'address_display', html);
                }
            });
        } else {
            frappe.model.set_value(dt, dn, 'address_display', null);
        }
    },
    contact: function(frm, dt, dn) {
        var v = locals[dt][dn];
        if (v.contact) {
            frappe.call({
                "method": "frappe.client.get",
                "args": {
                    "doctype": "Contact",
                    "name": v.contact
                },
                "callback": function(response) {
                    var contact = response.message;
                    frappe.model.set_value(dt, dn, 'phone', contact.phone);
                    frappe.model.set_value(dt, dn, 'email', contact.email_id);
                }
            });
        } 
    },
    party: function(frm, dt, dn) {
        var v = locals[dt][dn];
        if (v.party) {
            // clean address and contact
            frappe.model.set_value(dt, dn, 'address', null);
            frappe.model.set_value(dt, dn, 'contact', null);
            // fetch party name
            if (v.dt === "Customer") {
                frappe.call({
                    "method": "frappe.client.get",
                    "args": {
                        "doctype": "Customer",
                        "name": v.party
                    },
                    "callback": function(response) {
                        var customer = response.message;
                        frappe.model.set_value(dt, dn, 'party_name', customer.customer_name);
                        // get default address
                        frappe.call({
                            'method': "erpnextswiss.scripts.crm_tools.get_primary_customer_address",
                            'args': {
                                'customer': v.party
                            },
                            'callback': function(response) {
                                var address = response.message;
                                frappe.model.set_value(dt, dn, 'address', address.name);
                            }
                        });
                        // get default contact
                        frappe.call({
                            'method': "erpnextswiss.scripts.crm_tools.get_primary_customer_contact",
                            'args': {
                                'customer': v.party
                            },
                            'callback': function(response) {
                                var contact = response.message;
                                frappe.model.set_value(dt, dn, 'contact', contact.name);
                            }
                        });
                    }
                });
            } else if (v.dt === "Supplier") {
                frappe.call({
                    'method': "frappe.client.get",
                    'args': {
                        'doctype': "Supplier",
                        'name': v.party
                    },
                    'callback': function(response) {
                        var supplier = response.message;
                        frappe.model.set_value(dt, dn, 'party_name', supplier.supplier_name);
                        
                        // get default address
                        frappe.call({
                            'method': "erpnextswiss.scripts.crm_tools.get_primary_supplier_address",
                            'args': {
                                'supplier': v.party
                            },
                            'callback': function(response) {
                                var address = response.message;
                                frappe.model.set_value(dt, dn, 'address', address.name);
                            }
                        });
                        // get default contact
                        frappe.call({
                            'method': "erpnextswiss.scripts.crm_tools.get_primary_supplier_contact",
                            'args': {
                                'supplier': v.party
                            },
                            'callback': function(response) {
                                var contact = response.message;
                                frappe.model.set_value(dt, dn, 'contact', contact.name);
                            }
                        });
                    }
                });
                
                // in checklist cases: link in checklist as well
                if (["Kran", "Kran intern", "Geologe", "Mulde", "Schlammentsorgung"].includes(v.address_type)) {
                    set_checklist_supplier(frm, v.address_type, v.party);
                }
            }
        }
    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
    }
});

function search_plz(frm) {
    frappe.prompt([
        {'fieldname': 'plz', 'fieldtype': 'Data', 'label': 'PLZ', 'reqd': 1}  
    ],
    function(values){
        var filters = [['pincode','=', values.plz]];
        frappe.call({
            'method': 'frappe.client.get_list',
            'args': {
                'doctype': 'Pincode',
                'filters': filters,
                'fields': ['name', 'pincode', 'city', 'canton_code']
            },
            'async': false,
            'callback': function(response) {
                if (response.message) {
                    if (response.message.length == 1) {
                        // got exactly one city
                        var city = response.message[0].city;
                        cur_frm.set_value('plz', values.plz);
                        cur_frm.set_value('city', city);
                        cur_frm.set_value('kanton', response.message[0].canton_code);
                    } else {
                        // multiple cities found, show selection
                        var cities = "";
                        response.message.forEach(function (record) {
                            cities += (record.city + "\n");
                        });
                        cities = cities.substring(0, cities.length - 1);
                        frappe.prompt([
                                {'fieldname': 'city', 
                                 'fieldtype': 'Select', 
                                 'label': 'City', 
                                 'reqd': 1,
                                 'options': cities,
                                 'default': response.message[0].city
                                }  
                            ],
                            function(v2){
                                var city = v2.city;
                                cur_frm.set_value('plz', values.plz);
                                cur_frm.set_value('city', city);
                                for (var i = 0; i < response.message.length; i++) {
                                    if (city === response.message[i].city) {
                                        cur_frm.set_value('kanton', response.message[i].canton_code);
                                    }
                                }
                            },
                            __('City'),
                            __('Set')
                        );
                    }
                } else {
                    // got no match
                    frappe.show_alert("No match");
                    cur_frm.set_value('plz', values.plz);
                }
            }
        });
    },
    __('Search PLZ'),
    __('Search')
    )
}

function update_location(frm) {
    cur_frm.set_value("object_location", (frm.doc.plz || "") + " " + (frm.doc.city || "") + " " + (frm.doc.kanton || ""));
    update_gps(frm);
}

function update_gps(frm) {
    if ((frm.doc.object_street) && (frm.doc.object_location) && (!frm.doc.gps_coordinates)) {
        find_gps(frm);
    }
}

function find_gps(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_gps',
        'args': {
            'street': frm.doc.object_street,
            'location': frm.doc.object_location
        },
        'callback': function(response) {
            if (response.message) {
                cur_frm.set_value("gps_coordinates", response.message);
            }
        }
    });
}

function convert_ch_to_gps(frm) {
    if (locals.topo_prevent_loop) {
        locals.topo_prevent_loop = false;
    } else {
        frappe.call({
            'method': 'convert_ch_to_gps',
            'doc': frm.doc,
            'callback': function(response) {
                if (response.message) {
                    locals.topo_prevent_loop = true;
                    cur_frm.set_value("gps_coordinates", response.message);
                }
            }
        });
    }
}

function convert_gps_to_ch(frm) {
    if (locals.topo_prevent_loop) {
        locals.topo_prevent_loop = false;
    } else {
        frappe.call({
            'method': 'convert_gps_to_ch',
            'doc': frm.doc,
            'callback': function(response) {
                if (response.message) {
                    locals.topo_prevent_loop = true;
                    cur_frm.set_value("ch_coordinates", response.message);
                }
            }
        });
    }
}

function update_ews_details(frm, cdt, cdn) {
    var v = locals[cdt][cdn];
    if (frm.doc.ews_specification) {
        if (frm.doc.ews_specification.length === 1) {
            var details = (v.ews_count || "?") + "x "
                + (v.ews_depth || "?") + "m, "
                + (v.ews_diameter || "?") + (v.ews_diameter_unit || "");
            if (v.pressure_level) {
                details += ", " + (v.pressure_level || "");
            }
            if (frm.doc.drilling_type === "Brunnen") {
                details = "Brunnen " + details;
            }
            cur_frm.set_value("ews_details", details);
        } else {
            cur_frm.set_value("ews_details", "divers");
        }
    }
    // set wall strength
    if ((v.ews_diameter > 0) && (v.pressure_level)) {
        frappe.model.set_value(v.doctype, v.name, "ews_wall_strength", 
            get_wall_strength_from_diameter(v.ews_diameter, v.pressure_level));
    }
}

function recalculate_drilling_meter(frm) {
    if ((frm.doc.cooling_capacity) && (frm.doc.withdrawal_capacity)) {
        cur_frm.set_value("drilling_meter", ((frm.doc.cooling_capacity * 1000) / frm.doc.withdrawal_capacity));
    } else {
        cur_frm.set_value("drilling_meter", 0);
    }
}

function update_permits_on_plz(frm) {
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_standard_permits",
        "args": {
            "pincode": frm.doc.plz
        },
        "callback": function(response) {
            var standard_permits = response.message;
            cur_frm.clear_table("permits");
            fill_permits(frm, standard_permits);
        }
    });
}

function check_add_address(frm, address_type) {
    var has_address = false;
    for (var a = 0; a < (frm.doc.addresses || []).length; a++) {
        if (frm.doc.addresses[a].address_type === address_type) {
            has_address = true;
            break;
        }
    }
    if (!has_address) {
        var child = cur_frm.add_child('addresses');
        frappe.model.set_value(child.doctype, child.name, 'address_type', address_type);
        cur_frm.refresh_field('addresses');

    }
}

function check_add_checklist(frm, activity_type) {
    var has_checklist = false;
    for (var a = 0; a < (frm.doc.checklist || []).length; a++) {
        if (frm.doc.checklist[a].activity === activity_type) {
            has_checklist = true;
            break;
        }
    }
    if (!has_checklist) {
        var child = cur_frm.add_child('checklist');
        frappe.model.set_value(child.doctype, child.name, 'activity', activity_type);
        cur_frm.refresh_field('checklist');

    }
}

function set_checklist_supplier(frm, activity_type, supplier) {
    // make sure this item is in the checklist
    check_add_checklist(frm, activity_type);
    // find supplier name
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Supplier",
            'name': supplier
        },
        'callback': function(response) {
            // find activity and assign supplier
            for (var a = 0; a < (frm.doc.checklist || []).length; a++) {
                if (frm.doc.checklist[a].activity === activity_type) {
                    frappe.model.set_value(frm.doc.checklist[a].doctype, frm.doc.checklist[a].name, 'supplier', supplier);
                    frappe.model.set_value(frm.doc.checklist[a].doctype, frm.doc.checklist[a].name, 'supplier_name', response.message.supplier_name);
                    break;
                }
            }
        }
    });
    // add to related project if applicable
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.doctype.object.object.update_project_checklist",
        'args': {
            'obj': frm.doc.name,
            'activity_type': activity_type,
            'supplier': supplier
        }
    });
}
