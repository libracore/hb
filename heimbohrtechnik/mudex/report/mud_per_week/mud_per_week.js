// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Mud per Week"] = {
    "filters": [
        {
            "fieldname":"fiscal_year",
            "label": __("Fiscal Year"),
            "fieldtype": "Link",
            "options": "Fiscal Year",
            "default": frappe.defaults.get_user_default("Fiscal Year"),
            "reqd": 1
        },
        {
            "fieldname":"with_details",
            "label": __("Details"),
            "fieldtype": "Check"
        }
    ],
    "initial_depth": 0
};
