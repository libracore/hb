// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Truck Planning', {
    refresh: function(frm) {
        frm.add_custom_button(__("Delivery (ERP)"), function() {
            // frappe.set_route("Form", "Truck Delivery", {'truck': frm.doc.truck});
            frappe.model.open_mapped_doc({
                'method': "heimbohrtechnik.mudex.doctype.truck_planning.truck_planning.make_truck_delivery",
                'frm': cur_frm
            });
        });
        frm.add_custom_button(__("Delivery (Web)"), function() {
            var url = window.location.origin + "/schlammanlieferung?truck=" + cur_frm.doc.truck 
                + "&customer=" + cur_frm.doc.truck_customer 
                + "&object=" + cur_frm.doc.object 
                + "&key=" + cur_frm.doc.object_key;
            window.open(url, '_blank').focus();
        });
    },
    object_name: function(frm) {
        cur_frm.set_value("object_address", cur_frm.doc.object_street + "<br>" + cur_frm.doc.object_location);
        cur_frm.set_value("object_details", cur_frm.doc.object_name + ", " 
            + cur_frm.doc.object_street + ", "
            + cur_frm.doc.object_location);
    },
    truck: function(frm) {
        if (frm.doc.truck) {
            frappe.call({
                'method': "frappe.client.get",
                'args': {
                    "doctype": "Truck",
                    "name": frm.doc.truck
                },
                'callback': function(response) {
                    var truck = response.message;
                    cur_frm.set_value('color', truck.default_color);
                }
            });
        }
    }
});

