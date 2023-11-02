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
    ],
    	"formatter":function (value, row, column, data, default_formatter) {
		if (value == 0) {
            return `<div style="background-color: red;">${value}</div>`;
		} else if (value > 0 && value < 150) {
            return `<div style="background-color: orange;">${value}</div>`;
        } else if (value > 149) {
            return `<div style="background-color: green;">${value}</div>`;
        } else if (value == -1) {
            return `<div style="background-color: #f08080;">0</div>`;
        } else if (value == -2) {
            return `<div></div>`;
        }
		return default_formatter(value, row, column, data);
	}
};
