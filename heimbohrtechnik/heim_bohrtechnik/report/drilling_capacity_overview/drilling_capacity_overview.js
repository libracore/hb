// Copyright (c) 2023, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Drilling Capacity Overview"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },    
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), 21),
            "reqd": 1
        },
    ],
    "formatter":function (value, row, column, data, default_formatter) {
        if (column.colIndex > 2) {
            if (value == 0) {
                return `<div style="background-color: red;">${value}</div>`;
            } else if (value > 0 && value < 150) {
                return `<div style="background-color: orange;">${value}</div>`;
            } else if (value > 149) {
                return `<div style="background-color: #90ee90;">${value}</div>`;
            } else if (value == -1) {
                return `<div style="background-color: #fa8072;">0</div>`;
            } else if (value == -2) {
                return `<div></div>`;
            }
        }
        return default_formatter(value, row, column, data);
    },
    "onload": (report) => {
        report.page.add_inner_button("Freien Termin suchen", function(){
            get_free_date();
        });
    }
};

function get_free_date() {
    frappe.prompt([
        {
            'fieldname': 'drilling_type', 
            'label': __('Drilling type'),
            'fieldtype': 'Select',
            'options': 'Spühlbohrung\nHammerbohrung\nBrunnenbohrung\nKleinbohrgerät auf Bohrteam'
        }
    ],
    function(values){
        console.log(values.drilling_type);
        var drilling_type = values.drilling_type;
        // reschedule_project
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.report.drilling_capacity_overview.drilling_capacity_overview.get_free_date",
            'args': {
                "drilling_type": drilling_type
            }
        });
    },
    'Bohrteamart angeben',
    'Termin suchen'
    )
}
