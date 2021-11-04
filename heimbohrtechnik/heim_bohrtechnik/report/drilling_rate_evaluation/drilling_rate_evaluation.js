// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Drilling Rate Evaluation"] = {
    "filters": [
        {
            "fieldname":"object",
            "label": __("Object"),
            "fieldtype": "Link",
            "options": "Object"
        },
        {
            "fieldname":"street",
            "label": __("Street"),
            "fieldtype": "Data"
        },
        {
            "fieldname":"location",
            "label": __("Location"),
            "fieldtype": "Data"
        },
    ]
};
