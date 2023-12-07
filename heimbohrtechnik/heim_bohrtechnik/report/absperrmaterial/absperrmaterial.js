// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Absperrmaterial"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        }
    ]
};
