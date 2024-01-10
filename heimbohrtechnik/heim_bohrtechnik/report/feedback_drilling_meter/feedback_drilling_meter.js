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
	]
};

function get_years() {
   return "2024"; 
}
