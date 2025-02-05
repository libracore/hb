// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Materialbezugsliste"] = {
    "filters": [
        {
            'fieldname': 'employee',
            'label': __("Employee"),
            'fieldtype': 'Link',
            'options': 'Employee',
            'reqd': 1
        }
    ]
};
