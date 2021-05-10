// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

// child table filter sets
cur_frm.fields_dict.addresses.grid.get_field('address').get_query =   
    function(frm, dt, dn) {   
        var v = locals[dt][dn];
        return {
            query: "frappe.contacts.doctype.address.address.address_query",
            filters: {
                "link_doctype": v.dt,
                "link_name": v.party
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
                "link_name": v.party
            }
        }
    };
    
frappe.ui.form.on('Object', {
    refresh: function(frm) {
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
        }
    },
    button_search_plz: function(frm) {
        search_plz(frm);
    },
    plz: function(frm) {
        update_location(frm);
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
            window.open(
                "https://map.geo.admin.ch/?lang=de&topic=ech&bgLayer=ch.swisstopo.swissimage&layers=ch.swisstopo.zeitreihen,ch.bfs.gebaeude_wohnungs_register,ch.bav.haltestellen-oev,ch.swisstopo.swisstlm3d-wanderwege&layers_opacity=1,1,1,0.8&layers_visibility=false,false,false,false&layers_timestamp=18641231,,,&E=" + e + "&N=" + n + "&zoom=12",
                '_blank'
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
                    }
                });
            } else if (v.dt === "Supplier") {
                frappe.call({
                    "method": "frappe.client.get",
                    "args": {
                        "doctype": "Supplier",
                        "name": v.party
                    },
                    "callback": function(response) {
                        var supplier = response.message;
                        frappe.model.set_value(dt, dn, 'party_name', supplier.supplier_name);
                    }
                });
            }
        }
    }
});

function search_plz(frm) {
    frappe.prompt([
        {'fieldname': 'plz', 'fieldtype': 'Data', 'label': 'PLZ', 'reqd': 1}  
    ],
    function(values){
        var filters = [['pincode','=', values.plz]];
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Pincode',
                filters: filters,
                fields: ['name', 'pincode', 'city', 'canton_code']
            },
            async: false,
            callback: function(response) {
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
}

function convert_ch_to_gps(frm) {
    if (locals.topo_prevent_loop) {
        locals.topo_prevent_loop = false;
    } else {
        frappe.call({
            method: 'convert_ch_to_gps',
            doc: frm.doc,
            callback: function(response) {
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
            method: 'convert_gps_to_ch',
            doc: frm.doc,
            callback: function(response) {
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
}
