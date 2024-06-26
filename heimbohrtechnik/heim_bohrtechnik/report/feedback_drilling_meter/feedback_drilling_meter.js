// Copyright (c) 2016, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Feedback Drilling Meter"] = {
	"filters": [
        {
            "fieldname":"drilling_team_filter",
            "label": __("Drilling Team"),
            "fieldtype": "Link",
            "options": "Drilling Team"
        },
        {
            "fieldname":"year_filter",
            "label": __("Year"),
            "fieldtype": "Int",
            "default": new Date().getFullYear(),
            "reqd": 1
        }
	],
    //Mark flushing days in red
    "formatter":function (value, row, column, data, default_formatter) {
            if (data.flushing && data.flushing.includes(column.fieldname)) {
                return `<div style="color: red; text-align: right;">${value}</div>`;
            }
        return default_formatter(value, row, column, data);
    }
};
