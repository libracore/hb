// Copyright (c) 2025, libracore AG and contributors
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
    onload: function(report) {
        report.page.add_inner_button("Consumables Overview", function() {
            frappe.set_route("query-report", "Consumables Overview");
        });
    },
};
