// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pricing Analysis"] = {
    "filters": [
        {
            "fieldname":"item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname":"item_code",
            "label": __("Item Code"),
            "fieldtype": "Data"
        },
        {
            "fieldname":"item_name",
            "label": __("Item Name"),
            "fieldtype": "Data"
        },
        {
            "fieldname":"customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        }
    ]
};
