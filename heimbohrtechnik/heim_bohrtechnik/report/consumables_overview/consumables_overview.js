// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Consumables Overview"] = {
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
        },
        {
            "fieldname":"period_filter",
            "label": __("Period"),
            "fieldtype": "Select",
            "options": "Per Day\nPer Week\nPer Month",
            "default": "Per Week"
        }
	],
    onload: function(report) {
        report.page.add_inner_button("Feedback Drilling Meter", function() {
            frappe.set_route("query-report", "Feedback Drilling Meter");
        });
    },
};
