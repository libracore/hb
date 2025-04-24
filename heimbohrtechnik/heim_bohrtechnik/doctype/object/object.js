// Copyright (c) 2021-2024, libracore AG and contributors
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
        if (v.dt === "Supplier") {              // note: disabled controlled in server-side query
            filters = {
                'query': 'heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability',
                'filters': {
                    'capability': v.address_type
                }
            }
        } else {
            filters = {
                'query': 'heimbohrtechnik.heim_bohrtechnik.filters.customers',
                'filters': {
                    "disabled": 0
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
                    'capability': v.activity,
                    'disabled': 0
                }
            }
        return filters
    };
    
frappe.ui.form.on('Object', {
    refresh: function(frm) {
        // Create button to find Hotels nearby
        frm.add_custom_button(__("Hotel"), function() {
            find_hotel(frm);
        }, __("Find"));
        frm.add_custom_button(__("Trough"), function() {
            find_trough(frm);
        }, __("Find"));
        frm.add_custom_button(__("Mud"), function() {
            find_mud(frm);
        }, __("Find"));
        frm.add_custom_button(__("Parking"), function() {
            find_parking(frm);
        }, __("Find"));
        
        // show permits & checklist (in case coming from another record where it was hidden)
        var checklists = document.querySelectorAll("[data-fieldname='checklist']");
        try {
            for (var i = 0; i < checklists.length; i++) {
                checklists[i].parentElement.parentElement.parentElement.parentElement.style.display = "Block";
            }
        } catch { /* do nothing */ }
        if (!frm.doc.__islocal) {
            // check if project exists
            frappe.call({
                'method': 'has_project',
                'doc': frm.doc,
                'callback': function(response) {
                    if (response.message === 1) {
                        // has a project
                        frm.add_custom_button( frm.doc.name, function() {
                            frappe.set_route("Form", "Project", frm.doc.name);
                        }).addClass("btn-primary");
                        // hide permits & checklist
                        try {
                            
                            for (var i = 0; i < checklists.length; i++) {
                                checklists[i].parentElement.parentElement.parentElement.parentElement.style.display = "None";
                            }
                        } catch { /* do nothing */ }
                        
                        // try to add cloud button
                        frappe.call({
                            'method': "frappe.client.get",
                            'args': {
                                'doctype': "Project",
                                'name': frm.doc.name
                            },
                            'callback': function(response) {
                                var project = response.message;
                                if (project.cloud_url) {
                                    frm.add_custom_button(__("Cloud"), function() {
                                        window.open(project.cloud_url, '_blank').focus();
                                    });
                                }
                            } 
                        });
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
                    window.open("/desk#object-overview?object=" + frm.doc.name, "_blank");
                });
            }
            // button to order probes
            frm.add_custom_button("EWS bestellen", function() {
                order_ews(frm.doc.name);
            });
            // add button to open construction site description
            add_construction_site_description_button(frm, frm.doc.name)
            // split project button
            frm.add_custom_button(__("Objekt teilen"), function() {
                frappe.call({
                    'method': "heimbohrtechnik.heim_bohrtechnik.doctype.object.object.split_object",
                    'args': {
                        'object_name': frm.doc.name
                    },
                    'callback': function(response) {
                        window.location.href=response.message.uri;
                    }
                });
            }, __("More") );
            // show siblings
            check_display_siblings("Object", frm.doc.name);
        }
        if ((!frm.doc.addresses) || (frm.doc.addresses.length === 0)) {
            // fresh document, no addresses - load template
            update_address_on_plz(frm);
        }
        if ((!frm.doc.checklist) || (frm.doc.checklist.length === 0)) {
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
            update_checklist_on_plz(frm);
            update_address_on_plz(frm);
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
        
        get_elevation(frm);
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
            // check_add_checklist(frm, "Geologe"); // 2022-09-07: not required
        }
    },
    needs_insurance: function(frm) {
        if (frm.doc.needs_insurance) {
            frappe.confirm(
                'Soll die Versicherung in die Checkliste eingefügt werden?',
                function(){
                    // on yes
                    // add to related project if applicable
                    frappe.call({
                        'method': "heimbohrtechnik.heim_bohrtechnik.doctype.object.object.update_project_checklist",
                        'args': {
                            'obj': frm.doc.name,
                            'activity_type': "Versicherung"
                        }
                    });
                },
                function(){
                    // on no
                }
            );
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
        // set wall strength (important: before updating detail string server-sided)
        var v = locals[cdt][cdn];
        if ((v.ews_diameter > 0) && (v.pressure_level)) {
            var wall_strength = get_wall_strength_from_diameter(v.ews_diameter, v.pressure_level);
            frappe.model.set_value(cdt, cdn, "ews_wall_strength", wall_strength);
        }
        
        update_ews_details(frm, cdt, cdn);
    },
    probe_type: function(frm, cdt, cdn) {
        verify_diameter(frm, cdt, cdn);
        update_ews_details(frm, cdt, cdn);
    },
    ews_specification_remove(frm, cdt, cdn) {
        console.log("remove");
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
                    if (contact.address) {
                        frappe.model.set_value(dt, dn, 'address', contact.address);
                    }
                }
            });
        } else {
            frappe.model.set_value(dt, dn, 'phone', null);
            frappe.model.set_value(dt, dn, 'email', null);
        }
    },
    party: function(frm, dt, dn) {
        var v = locals[dt][dn];
        // clean address and contact
        frappe.model.set_value(dt, dn, 'address', null);
        frappe.model.set_value(dt, dn, 'contact', null);
        frappe.model.set_value(dt, dn, 'party_name', null);
        if (v.party) {
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
                                if (contact) {
                                    frappe.model.set_value(dt, dn, 'contact', contact.name);
                                }
                            }
                        });
                    }
                });
                
                // in checklist cases: link in checklist as well
                if (["Kran extern", "Kran intern", "Geologe", "Mulde", "Schlammentsorgung"].includes(v.address_type)) {
                    set_checklist_supplier(frm, v.address_type, v.party);
                }
            }
        }
    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
        
        get_default_trough_size(frm, dt, dn);
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
    if (!locals.gps_location_pending) {
        locals.gps_location_pending = true;     // prevent multiple calls from plz/city change events
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_gps',
            'args': {
                'street': (frm.doc.object_street || ""),
                'location': (frm.doc.plz || "") + " " + (frm.doc.city || "")
            },
            'callback': function(response) {
                locals.gps_location_pending = false;
                if (response.message) {
                    if (response.message === "queued") {
                        // the request has been sent, check back in a second
                        setTimeout( function() {
                            find_gps(cur_frm);
                        }, 1000);
                    } else {
                        cur_frm.set_value("gps_coordinates", response.message);
                    }
                } else {
                    console.log("Nothing found at " + frm.doc.object_street + " " + frm.doc.plz + " " + frm.doc.city);
                }
            }
        });
    }
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

function get_elevation(frm) {
    if (frm.doc.ch_coordinates) {
        let xy = frm.doc.ch_coordinates.split(" / ");
        if (xy.length === 2) {
            frappe.call({
                'method': 'erpnextswiss.erpnextswiss.swisstopo.get_height_above_sea_level',
                'args': {
                    'x': xy[0].replaceAll("'", ""),
                    'y': xy[1].replaceAll("'", "")
                },
                'callback': function(response) {
                    if (response.message) {
                        cur_frm.set_value("m_u_m", response.message);
                    }
                }
            });
        } else {
            console.log("Get elevation: Invalid coordinates");
        }
    } else {
        console.log("Get elevation: No coordinates");
    }
}

function update_ews_details(frm, cdt, cdn) {
    frappe.call({
        'method': 'get_ews_details',
        'doc': frm.doc,
        'callback': function(response) {
            cur_frm.set_value("ews_details", response.message);
        }
    });
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

function update_checklist_on_plz(frm) {
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.utils.get_standard_activities",
        "args": {
            "pincode": frm.doc.plz
        },
        "callback": function(response) {
            var standard_checklist = response.message;
            cur_frm.clear_table("checklist");
            fill_checklist(frm, standard_checklist);
        }
    });
}

function update_address_on_plz(frm) {
    frappe.call({
        "method": "heimbohrtechnik.heim_bohrtechnik.doctype.heim_settings.heim_settings.get_address_template",
        "args": {
            "pincode": frm.doc.plz
        },
        "callback": function(response) {
            var address_types = response.message;
            cur_frm.clear_table('addresses');
            for (var i = 0; i < address_types.length; i++) {
                var child = cur_frm.add_child('addresses');
                frappe.model.set_value(child.doctype, child.name, 'address_type', address_types[i].type);
                frappe.model.set_value(child.doctype, child.name, 'dt', address_types[i].dt);
            }
            cur_frm.refresh_field('addresses');
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
    // make sure only to use the first supplier of this type (e.g. mud can occur multiple times)
    var first_supplier = supplier;
    for (var i = 0; i < frm.doc.addresses.length; i++) {
        if (frm.doc.addresses[i].address_type == activity_type) {
            first_supplier = frm.doc.addresses[i].party;
            break;
        }
    }
    // find supplier name
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Supplier",
            'name': first_supplier
        },
        'callback': function(response) {
            // find activity and assign supplier
            for (var a = 0; a < (frm.doc.checklist || []).length; a++) {
                if (frm.doc.checklist[a].activity === activity_type) {
                    frappe.model.set_value(frm.doc.checklist[a].doctype, frm.doc.checklist[a].name, 'supplier', first_supplier);
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
            'supplier': first_supplier
        }
    });
}

function verify_diameter(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if ((row.probe_type) && (row.ews_diameter)) {
        // fetch possible diameters
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Probe Type",
                'name': row.probe_type
            },
            'callback': function(response) {
                var probe_type = response.message;
                if ((probe_type.diameters) && (!probe_type.diameters.includes(row.ews_diameter.toString()))) {
                    frappe.msgprint("Vorsicht: dieser Durchmesser ist bei dem Sondentyp nicht verfügbar.");
                }
            }
        });
    }
}

function find_hotel(frm) {
    if (frm.doc.gps_coordinates) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.locator.find_closest_hotels",
            'args': {
                'object_name': frm.doc.name
            },
            'callback': function (r) {
                var d = new frappe.ui.Dialog({
                    'fields': [
                        {'fieldname': 'ht', 'fieldtype': 'HTML'}
                    ],
                    'title': __("Hotels")
                });
                d.fields_dict.ht.$wrapper.html(r.message.html);
                d.show();
                
                for (var i = 0; i < r.message.hotels.length; i++) {
                    find_true_distance(cur_frm, r.message.hotels[i].gps_latitude, r.message.hotels[i].gps_longitude,"hotel_distance_" + i, "hotel_time_" + i);
                }
            }
        });
    } else {
        frappe.msgprint(__("Keine Koordinaten"));
    }
}

var parkingDialog = null;

function find_parking(frm) {
    if (frm.doc.gps_coordinates) {
        if (!parkingDialog) {
            // Erstelle den Dialog, wenn er noch nicht existiert
            parkingDialog = new frappe.ui.Dialog({
                'fields': [
                    {'fieldname': 'ht', 'fieldtype': 'HTML'}
                ],
                'title': __("Parkings")
            });
        } else {
            // Reset den Inhalt des Dialogs, wenn er bereits existiert
            parkingDialog.fields_dict.ht.$wrapper.empty();
        }

        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.locator.find_closest_parkings",
            'args': {
                'object_name': frm.doc.name
            },
            'callback': function (r) {
                parkingDialog.fields_dict.ht.$wrapper.html(r.message.html);
                parkingDialog.show();
            }
        });
    } else {
        frappe.msgprint(__("Keine Koordinaten"));
    }
}


function find_true_distance(frm, to_lat, to_long, target_distance_field, target_duration_field) {
    frappe.call({
        'method': "heimbohrtechnik.heim_bohrtechnik.locator.get_true_distance",
        'args': {
            'from_lat': frm.doc.gps_lat,
            'from_long': frm.doc.gps_long,
            'to_lat': to_lat,
            'to_long': to_long
        },
        'callback': function (r) {
            document.getElementById(target_distance_field).innerHTML=r.message.data['distance_in_kilometers'].toFixed(1) + " km";
            document.getElementById(target_duration_field).innerHTML=r.message.data['travel_time'].split(".")[0];
        }
    });
 }

function find_trough(frm) {
    if (frm.doc.gps_coordinates) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.locator.find_closest_troughs",
            'args': {
                'object_name': frm.doc.name
            },
            'callback': function (r) {
                var d = new frappe.ui.Dialog({
                    'fields': [
                        {'fieldname': 'ht', 'fieldtype': 'HTML'}
                    ],
                    'title': __("Trough")
                });
                d.fields_dict.ht.$wrapper.html(r.message.html);
                d.show();
                
                for (var i = 0; i < r.message.hotels.length; i++) {
                    find_true_distance(cur_frm, r.message.hotels[i].gps_latitude, r.message.hotels[i].gps_longitude,"hotel_distance_" + i, "hotel_time_" + i);
                }
            }
        });
    } else {
        frappe.msgprint(__("Keine Koordinaten"));
    }
}

function find_mud(frm) {
    if (frm.doc.gps_coordinates) {
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.locator.find_closest_mud",
            'args': {
                'object_name': frm.doc.name
            },
            'callback': function (r) {
                var d = new frappe.ui.Dialog({
                    'fields': [
                        {'fieldname': 'ht', 'fieldtype': 'HTML'}
                    ],
                    'title': __("Mud")
                });
                d.fields_dict.ht.$wrapper.html(r.message.html);
                d.show();
                
                for (var i = 0; i < r.message.hotels.length; i++) {
                    find_true_distance(cur_frm, r.message.hotels[i].gps_latitude, r.message.hotels[i].gps_longitude,"hotel_distance_" + i, "hotel_time_" + i);
                }
            }
        });
    } else {
        frappe.msgprint(__("Keine Koordinaten"));
    }
}
