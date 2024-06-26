// Copyright (c) 2023-2024, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

var drilling_types = [
    {'fieldname': 'flushing_drilling', 'label': "Spülbohrung"},
    {'fieldname': 'hammer_drilling', 'label': "Hammerbohrung"},
    {'fieldname': 'well_drilling', 'label': "Brunnenbohrung"},
    {'fieldname': 'small_drilling_rig', 'label': "Kleinbohrgerät auf Bohrteam"}
];

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
        }
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
        report.page.add_inner_button("Nach KW filtern", function(){
            filter_for_cw();
        });
    }
};

function get_free_date() {
    var dts = []
    for (var i = 0; i < drilling_types.length; i++) {
        dts.push(drilling_types[i].label);
    }
    frappe.prompt([
        {
            'fieldname': 'drilling_type', 
            'label': __('Drilling type'),
            'fieldtype': 'Select',
            'options': dts.join("\n")
        }
    ],
    function(values){
        var drilling_type = null;
        for (var i = 0; i < drilling_types.length; i++) {
            if (drilling_types[i].label === values.drilling_type) {
                drilling_type = drilling_types[i].fieldname;
                label = drilling_types[i].label;
                break;
            }
        }
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.report.drilling_capacity_overview.drilling_capacity_overview.get_free_date",
            'args': {
                "drilling_type": drilling_type,
                "label": label
            }
        });
    },
    'Bohrteamart angeben',
    'Termin suchen'
    )
}

function filter_for_cw() {
    var currentDate = new Date();
    var currentYear = currentDate.getFullYear();
    var options = [currentYear, currentYear + 1]
    frappe.prompt([
        {
            'fieldname': 'calendar_week', 
            'label': __('Calendar week'),
            'fieldtype': 'Int',
            "reqd": 1
        },
        {
            'fieldname': 'year', 
            'label': __('Year'),
            'fieldtype': 'Select',
            'options': options,
            'default': currentYear
        },
        {
            'fieldname': 'start_check', 
            'label': __('Startdatum ebenfalls anpassen'),
            'fieldtype': 'Check'
        }
    ],
    function(values){
        var calendar_week = values.calendar_week;
        var year = values.year;
        var start_check = values.start_check;
        frappe.call({
            'method': "heimbohrtechnik.heim_bohrtechnik.report.drilling_capacity_overview.drilling_capacity_overview.get_filter_dates",
            'args': {
                'calendar_week': calendar_week,
                'year': year,
                'start_check': start_check
            },
            'async': false,
            'callback': function(response) {
                var from_date = response.message[0];
                var to_date = response.message[1];
                frappe.query_report.set_filters({'from_date': from_date, 'to_date': to_date}) 
            }
        });
    },
    'Kalenderwoche zum filtern angeben',
    'Filtern'
    )
}
