// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Kundenauszug"] = {
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
            "fieldname":"party_type",
            "label": __("Type"),
            "fieldtype": "Select",
            "options": "Customer\nSupplier",
            "reqd": 1,
            "default": "Customer",
            "on_change": function(query_report) {
                console.log("Change party type");
                show_conditional_filters();
            }
        },
        {
            "fieldname":"customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname":"supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier"
        },
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today()
        }
    ],
    "onload": function() {
        show_conditional_filters();
        
        setTimeout(function() {
            frappe.query_report.page.remove_inner_button( __("Set Chart") );
            frappe.query_report.page.remove_inner_button( __("Hide Chart") );
        }, 500);
        
        frappe.query_report.page.add_inner_button( __("PDF"), function() {
            create_pdf();
        });
    }
};

function show_conditional_filters() {
    if (frappe.query_report.get_filter_value("party_type") === "Supplier") {
        show_filter("supplier");
        hide_filter("customer");
    } else {
        show_filter("customer");
        hide_filter("supplier");
    }
}

function show_filter(filter) {
    toggle_filter(filter, "block");
}

function hide_filter(filter) {
    toggle_filter(filter, "none");
}

function toggle_filter(filter, display) {
    var filters = document.querySelectorAll("[data-fieldname='" + filter + "']");
    for (var i = 0; i < filters.length; i++) {
        filters[i].style.display = display;
    }
}

function create_pdf() {
    var filters = frappe.query_report.get_filter_values();
    if ((filters.company) && 
        (((filters.party_type === "Customer") && (filters.customer)) 
            || ((filters.party_type === "Supplier") && (filters.supplier)))) {
        var w = window.open(
            frappe.urllib.get_full_url("/api/method/heimbohrtechnik.heim_bohrtechnik.report.kundenauszug.kundenauszug.download_pdf"
                + "?company=" + encodeURIComponent(filters.company)
                + "&party_type=" + encodeURIComponent(filters.party_type)
                + "&customer=" + encodeURIComponent(filters.customer || "")
                + "&supplier=" + encodeURIComponent(filters.supplier || "")
                + "&from_date=" + encodeURIComponent(filters.from_date || "")
                + "&to_date=" + encodeURIComponent(filters.to_date || "")
            ));
        if (!w) {
            frappe.msgprint(__("Please enable pop-ups")); 
        }
    } else {
        frappe.msgprint(__("Bitte Filter setzen")); 
    }

}
