// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Artikelzusammenfassung"] = {
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
            "fieldname":"bkp_group",
            "label": __("BKP"),
            "fieldtype": "Link",
            "options": "BKP Group"
        },
        {
            "fieldname":"price_list",
            "label": __("Price List"),
            "fieldtype": "Link",
            "options": "Price List",
            "default": frappe.defaults.get_default("selling_price_list"),
            "reqd": 1
        }
    ]
};
