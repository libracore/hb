// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Versicherungsanmeldung"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), (-1) * ((new Date().getDay() - 1)) + 7),
            "reqd": 1
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), (-1) * ((new Date().getDay() - 1)) + 12),
            "reqd": 1
        }
    ]
};
