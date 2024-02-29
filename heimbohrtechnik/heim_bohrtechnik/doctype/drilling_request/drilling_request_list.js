frappe.listview_settings['Drilling Request'] = {
    'add_fields': ["status", "quotation_until", "object_street", "object", "quotation"],
    'filters': [["status","=", "Offen"]],
    'get_indicator': function(doc) {
        var status_color = {
            "Offen": "red",
            "In Arbeit": "orange",
            "Abgeschlossen": "green"
        };
        
        return [ __(doc.status), status_color[doc.status], "status,=,"+doc.status];
    }
};
