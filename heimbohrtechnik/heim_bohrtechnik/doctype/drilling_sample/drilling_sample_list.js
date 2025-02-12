// Copyright (c) 2025, libracore and contributors
// For license information, please see license.txt

frappe.listview_settings['Drilling Sample'] = {
    get_indicator: function(doc) {
        var status_colour = {
            "bestätigt": "green",
            "erfasst": "orange"
        };
        return [__(doc.status), status_colour[doc.status], "status,=," + doc.status];
    }
};