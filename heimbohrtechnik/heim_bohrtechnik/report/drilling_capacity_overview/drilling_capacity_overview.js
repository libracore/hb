// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Drilling Capacity Overview"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },    
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), 21),
            "reqd": 1
        }
    ]
};
