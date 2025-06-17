// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Projekte mit Toitoi"] = {
    "filters": [
        {
            'fieldname': 'status',
            'label': __("Status"),
            'fieldtype': "Select",
            'options': "\nrequired\norganised"
        }
    ]
};
