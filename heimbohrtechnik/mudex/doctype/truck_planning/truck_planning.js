// Copyright (c) 2021-2026, libracore AG and contributors
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
            window.open(get_feedback_link(frm), '_blank').focus();
        });
        // button to create truck link
        frm.add_custom_button("<i class='fa fa-truck'></i> Link", function() {
            let link = get_feedback_link(frm); 
            navigator.clipboard.writeText(link).then(function() {
                frappe.show_alert( __("Link in der Zwischenablage") );
              }, function() {
                 frappe.show_alert( __("Kein Zugriff auf Zwischenablage") );
            });
        });
        // button to create navigation link
        frm.add_custom_button("<i class='fa fa-map-marker'></i> Navigation", function() {
            window.open(get_navigation_link(frm), '_blank').focus();
        });
        // button to create whatsapp link
        frm.add_custom_button("<i class='fa fa-whatsapp'></i> Whatapp", function() {
            if (!frm.doc.truck_phone) {
                frappe.prompt([
                        {'fieldname': 'phone', 'fieldtype': 'Data', 'label': __('Phone'), 'reqd': 1}  
                    ],
                    function(values){
                        cur_frm.set_value("truck_phone", values.phone);
                        open_whatsapp(frm);
                    },
                    'Telefonnummer eingeben',
                    'OK'
                );
            } else {
                open_whatsapp(frm);
            }
        });
        // button to create whatsapp to clipboard
        frm.add_custom_button("<i class='fa fa-clipboard'></i> Whatapp", function() {
            let link = get_whatsapp_message(frm); 
            navigator.clipboard.writeText(link).then(function() {
                frappe.show_alert( __("Link in der Zwischenablage") );
              }, function() {
                 frappe.show_alert( __("Kein Zugriff auf Zwischenablage") );
            });
        });
    },
    object_name: function(frm) {
        cur_frm.set_value("object_address", cur_frm.doc.object_street + "<br>" + cur_frm.doc.object_location);
        set_details();
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
                    
                    if (frm.doc.object) {
                        set_details();
                    }
                }
            });
        }
    }
});

function set_details() {
    cur_frm.set_value("object_details", cur_frm.doc.truck_title + ": "
        + cur_frm.doc.object + " - " 
        + cur_frm.doc.object_street + ", "
        + cur_frm.doc.object_location);
}

function get_feedback_link(frm) {
    return window.location.origin + "/schlammanlieferung?truck=" + cur_frm.doc.truck 
        + "&customer=" + cur_frm.doc.truck_customer 
        + "&object=" + cur_frm.doc.object 
        + "&key=" + cur_frm.doc.object_key; 
}

function get_navigation_link(frm) {
    return "https://www.google.com/maps/dir//" 
        + (cur_frm.doc.object_street || "").replace(" ", "+") + ","
        + (cur_frm.doc.object_location || "").replace(" ", "+"); 
}

function get_whatsapp_message(frm) {
    let date = (frm.doc.start_time || "").split(" ")[0];
    let time = (frm.doc.start_time || " ").split(" ")[1].substring(0, 5);
    let street = (frm.doc.object_address || "<br>").split("<br>")[0];
    let city = (frm.doc.object_address || "<br>").split("<br>")[1];
    let googleMapsLink = get_navigation_link(frm);
    let feedbackLink = get_feedback_link(frm);
    
    const message = `Hallo, bitte am ${date} um ${time} Uhr in
${street}
${city}
${googleMapsLink}
absaugen.
Hier ist der Wiegelink: ${feedbackLink}`;

    return message;
}

function open_whatsapp(frm) {
    window.open(create_whatsapp_link(frm), '_blank').focus();
}

function create_whatsapp_link(frm) {
    let phoneNumber = (frm.doc.truck_phone || "").replaceAll("+", "").replaceAll(" ", "");
    const encodedMessage = encodeURIComponent(get_whatsapp_message(frm));
    return `https://wa.me/${phoneNumber}?text=${encodedMessage}`;
}
