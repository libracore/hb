// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Umsatzliste per Kunde"] = {
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
            "fieldname":"options",
            "label": __("Auswertung"),
            "fieldtype": "Select",
            "options": "Auftragsdatum\nLieferdatum\nRechnungsdatum",
            "default": "Lieferdatum",
            "reqd": 1
        }
    ]
};
