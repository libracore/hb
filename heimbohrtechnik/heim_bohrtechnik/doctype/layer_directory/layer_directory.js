// Copyright (c) 2022-2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Layer Directory', {
    refresh: function(frm) {
        
    },
    project: function(frm) {
        autocomplete_object(frm);
    },
    validate: function(frm) {
        if ((frm.doc.so_mud_amount) 
            && (!frm.doc.ignore_mud_deviation) 
            && (frm.doc.amount_disposed > 0)
            && (frm.doc.amount_disposed < frm.doc.so_mud_amount)) {
            frappe.msgprint( __("Vorsicht, es wurde weniger Schlamm angeliefert als im Kundenauftrag erwartet"), __("Validation") );
        }
        if ((!frm.doc.drilling_tools) || (frm.doc.drilling_tools.length === 0)) {
            frappe.msgprint( __("Bitte mindestens ein Bohrwerkzeug erfassen."), __("Validation") );
        }
    },
    before_submit: function(frm) {
        if ((frm.doc.so_mud_amount) 
            && (!frm.doc.ignore_mud_deviation) 
            && (frm.doc.amount_disposed > 0)
            && (frm.doc.amount_disposed < frm.doc.so_mud_amount)) {
            frappe.msgprint( __("Eine Schlammunterlieferung kann nur mit der Option <b>Schlammmenge ignorieren</b> gebucht werden.") );
            frappe.validated = false;
        }
    },
    mixing_type: function(frm) {
        set_product(frm);
    }
});

function autocomplete_object(frm) {
    if (frm.doc.project) {
        frappe.call({
            'method': "get_autocomplete_data",
            'doc': frm.doc,
            'args': {
                'project': frm.doc.project
            },
            'callback': function(response) {
                var data = response.message;

                cur_frm.set_value("object_name", data.object.object_name);
                cur_frm.set_value("object_street", data.object.object_street);
                cur_frm.set_value("object_location", data.object.object_location);
                cur_frm.set_value("drilling_team", data.project.drilling_team);
                //cur_frm.set_value("drilling_tool", data.drilling_team.drt);       // deprecated: this is now a child table - drt is an equipment not a drilling tool
                cur_frm.set_value("so_mud_amount", data.sales_order_mud_amount);
                
                // find permits
                for (var i = 0; i < data.project.permits.length; i++) {
                    if (data.project.permits[i].permit.includes("Bohrbewilligung kantonal")) {
                        cur_frm.set_value("permit_no", 
                            (data.project.permits[i].permit_number || ""));
                        cur_frm.set_value("permit_date", 
                            (data.project.permits[i].permit_date));
                    }
                }
                
                //set probe type and ews depth (let user choose drill, if there are multiple)
                if (data.ews_details.length < 1) {
                    frappe.msgprint("Keine Bohrung in Objekt " + data.object.name + " gefunden", "Achtung");
                } else if (data.ews_details.length > 1) {
                    var options = '';
                    for (var i = 0; i < data.ews_details.length; i++) {
                        var list_entry = "\n"+(i+1) + "- Tiefe: " + data.ews_details[i].ews_depth + "m, Durchmesser: " + data.ews_details[i].ews_diameter + "mm, Sonde: " + data.ews_details[i].probe_type;
                        options += list_entry;
                    }
                    frappe.prompt([
                        {
                            'label': 'Wähle Bohrung',
                            "fieldname": "bohrung",
                            "fieldtype": "Select",
                            "options": options,
                            "reqd": 1
                        } ],
                        function(values) {
                            var x = parseInt(values.bohrung.split("-")[0]);
                            cur_frm.set_value("probe_length", data.ews_details[x-1].ews_depth);
                            cur_frm.set_value("probe_diameter", data.ews_details[x-1].ews_diameter);
                            cur_frm.set_value("probe_type", data.ews_details[x-1].probe_type);
                            cur_frm.set_value("pressure_level", data.ews_details[x-1].pressure_level);
                            set_drilling_order(data.ews_details[x-1].count, data.ews_details[x-1].ews_depth);
                        }
                    );
                } else {
                    cur_frm.set_value("probe_length", data.ews_details[0].ews_depth);
                    cur_frm.set_value("probe_diameter", data.ews_details[0].ews_diameter);
                    cur_frm.set_value("probe_type", data.ews_details[0].probe_type);
                    cur_frm.set_value("pressure_level", data.ews_details[0].pressure_level);
                    set_drilling_order(data.ews_details[0].count, data.ews_details[0].ews_depth);
                }
                
                // find addresses
                for (var i = 0; i < data.object.addresses.length; i++) {
                    if (data.object.addresses[i].address_type === "Geologe") {
                        if (data.object.addresses[i].is_simple === 1) {
                            cur_frm.set_value("geologist", 
                                (data.object.addresses[i].simple_name || "") + ", " 
                                    + (data.object.addresses[i].simple_address || ""));
                        } else {
                            cur_frm.set_value("geologist", (data.object.addresses[i].party_name || ""));
                        }
                    } else if (data.object.addresses[i].address_type === "Mulde") {
                        if (data.object.addresses[i].is_simple === 1) {
                            cur_frm.set_value("forwarder", 
                                (data.object.addresses[i].simple_name || "") + ", " 
                                    + (data.object.addresses[i].simple_address || ""));
                        } else {
                            cur_frm.set_value("forwarder", (data.object.addresses[i].party_name || ""));
                        }
                    } else if (data.object.addresses[i].address_type === "Schlammentsorgung") {
                        if (data.object.addresses[i].is_simple === 1) {
                            cur_frm.set_value("disposer", 
                                (data.object.addresses[i].simple_name || "") + ", " 
                                    + (data.object.addresses[i].simple_address || ""));
                        } else {
                            cur_frm.set_value("disposer", (data.object.addresses[i].party_name || ""));
                        }
                    }
                }
            }
        });
    }
}

function set_drilling_order(count, depth) {
    var drilling_order = count + "x " + depth +"m"
    cur_frm.set_value("drilling_order", drilling_order);
}
    
function set_product(frm) {
    if (frm.doc.mixing_type == "ZEO-THERM 2.0") {
        cur_frm.set_value("product", "Küchler");
    } else {
        cur_frm.set_value("product", "Schwenk");
    }
}
