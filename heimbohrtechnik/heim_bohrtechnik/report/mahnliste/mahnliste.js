// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Mahnliste"] = {
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
            "fieldname":"customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        }
    ],
    "initial_depth": 0
};
