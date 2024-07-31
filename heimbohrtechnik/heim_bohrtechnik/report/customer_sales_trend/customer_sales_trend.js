// Copyright (c) 2023-2024, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer sales trend"] = {
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
            "options": "Customer",
            "reqd": 1
        },
        {
            "fieldname":"base",
            "label": __("Base"),
            "fieldtype": "Select",
            "options": "Sales Order\nSales Invoice",
            "default": "Sales Order",
            "reqd": 1
        },
        {
            "fieldname":"aggregation",
            "label": __("Type"),
            "fieldtype": "Select",
            "options": "Yearly\nQuarterly\nMonthly",
            "default": "Yearly",
            "reqd": 1
        },
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date"
        }
    ]
};

