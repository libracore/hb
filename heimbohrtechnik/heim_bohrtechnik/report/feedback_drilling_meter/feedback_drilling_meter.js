// Copyright (c) 2016, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Feedback Drilling Meter"] = {
	"filters": [
        {
            "fieldname":"drilling_team_filter",
            "label": __("Drilling Team"),
            "fieldtype": "Link",
            "options": "Drilling Team",
            "reqd": 1
        },
        {
            "fieldname":"year_filter",
            "label": __("Year"),
            "fieldtype": "Select",
            "options": get_years(),
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

function get_years() {
    var actual_year = new Date().getFullYear();
    console.log(actual_year)
   return String(actual_year) + "\n" + String(actual_year-1) + "\n" + String(actual_year-2) + "\n" + String(actual_year-3) + "\n" + String(actual_year-4); 
}
