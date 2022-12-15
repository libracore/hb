// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Offene Akonto-Rechnungen"] = {
    "filters": [
        {
            "fieldname":"sales_order",
            "label": __("Sales Order"),
            "fieldtype": "Link",
            "options": "Sales Order"
        }
    ]
};
