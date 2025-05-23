// Copyright (c) 2020-2025, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Saldenliste Periode"] = {
    "filters": [
        {
            "fieldname":"company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "reqd": 1,
            "default": frappe.defaults.get_user_default("company") || frappe.defaults.get_global_default("company")
        },
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": (new Date((new Date()).getFullYear(), 0, 01))
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": new Date()
        },
        {
            "fieldname":"report_type",
            "label": __("Type"),
            "fieldtype": "Select",
            "options": "\nBalance Sheet\nProfit and Loss"
        }
	]
}

// returns the date one month ago
function get_one_month_ago(date) {
    d = date;
    d.setMonth(d.getMonth() - 1);
    return d;
}
