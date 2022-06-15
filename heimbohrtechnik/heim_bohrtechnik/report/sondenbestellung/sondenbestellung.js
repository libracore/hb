// Copyright (c) 2022, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sondenbestellung"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), (-1) * ((new Date().getDay() - 1)) + 14),
            "reqd": 1
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), (-1) * ((new Date().getDay() - 1)) + 20),
            "reqd": 1
        },
        {
            "fieldname":"show_all",
            "label": __("Alle zeigen"),
            "fieldtype": "Check"
        }
    ],
    "onload": (report) => {
        // add event listener for double clicks
        cur_page.container.addEventListener("dblclick", function(event) {
            var row = event.delegatedTarget.getAttribute("data-row-index");
            var column = event.delegatedTarget.getAttribute("data-col-index");
            var content = null;
            if (event.delegatedTarget.innerText) {
                content = event.delegatedTarget.innerText;
            }
            if (content === "bestellen") {
                var object = frappe.query_report.data[row].object;
                order_ews(object);
            }
        });
}
};
