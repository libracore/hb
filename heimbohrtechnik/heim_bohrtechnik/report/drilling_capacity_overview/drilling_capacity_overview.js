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
    //~ html = frappe.render_template("detail_dialog", data );
    var d = new frappe.ui.Dialog({
        'fields': [
            {
                'fieldname': 'drilling_type', 
                'label': __('Drilling type'),
                'fieldtype': 'Select',
                'options': 'Spühlbohrung\nHammerbohrung\nBrunnenbohrung\nKleinbohrgerät auf Bohrteam'
            },
        ],
        'primary_action': function(){
            //~ d.hide();
            var drilling_type = d.get_values();
            // reschedule_project
            frappe.call({
                'method': "heimbohrtechnik.heim_bohrtechnik.report.drilling_capacity_overview.drilling_capacity_overview.get_free_date",
                'args': {
                    "drilling_type": drilling_type
                },
                'callback': function(response) {
                    console.log("Maschineeeeeeeee");
                }
            });
        },
    });
}

html = frappe.render_template("detail_dialog", data );
                                var d = new frappe.ui.Dialog({
                                    'fields': [
                                        {
                                            'fieldname': 'ht', 
                                            'fieldtype': 'HTML'
                                        },
                                        {
                                            'fieldname': 'section_1', 
                                            'fieldtype': 'Section Break'
                                        },
                                        {
                                            'fieldname': 'start', 
                                            'label': __('Start'), 
                                            'fieldtype': 'Date', 
                                            'default': project.expected_start_date, 
                                            'reqd': 1,
                                            'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                                        },
                                        {
                                            'fieldname': 'start_hd', 
                                            'label': __('Start Half-Day'),
                                            'fieldtype': 'Select',
                                            'options': 'VM\nNM', 
                                            'default': project.start_half_day,
                                            'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                                        },
                                        {
                                            'fieldname': 'drilling_team', 
                                            'label': __("Drilling Team"), 
                                            'fieldtype': 'Link', 
                                            'options': 'Drilling Team', 
                                            'default': project.drilling_team, 
                                            'reqd': 1,
                                            'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                                        },
                                        {
                                            'fieldname': 'duration', 
                                            'label': __("Duration"), 
                                            'fieldtype': 'Float', 
                                            'default': project.duration, 
                                            'read_only': 1,
                                            'hidden': 1
                                        },
                                        {
                                            'fieldname': 'cb_1', 
                                            'fieldtype': 'Column Break'
                                        },
                                        {
                                            'fieldname': 'end', 
                                            'label': __('End'),
                                            'fieldtype': 'Date', 
                                            'default': project.expected_end_date, 
                                            'reqd': 1,
                                            'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                                        },
                                        {
                                            'fieldname': 'end_hd', 
                                            'label': __('End Half-Day'), 
                                            'fieldtype': 'Select', 
                                            'options': 'VM\nNM', 
                                            'default': project.end_half_day,
                                            'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                                        },
                                        {
                                            'fieldname': 'visit_date', 
                                            'label': __('Visit date'), 
                                            'fieldtype': 'Date', 
                                            'default': project.visit_date
                                        },
                                        {
                                            'fieldname': 'meter_per_day', 
                                            'label': __('Meter per Day'), 
                                            'fieldtype': 'Int', 
                                            'default': project.drilling_meter_per_day,
                                            'read_only': 1,
                                            'hidden': 1
                                        },
                                    ],
                                    'primary_action': function(){
                                        d.hide();
                                        var reshedule_data = d.get_values();
                                        // reschedule_project
                                        frappe.call({
                                            'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.reschedule_project",
                                            'args': {
                                                "popup": 1,
                                                "project": project.name,
                                                'new_project_start': reshedule_data.start,
                                                "start_half_day": reshedule_data.start_hd,
                                                'new_project_end_date': reshedule_data.end,
                                                'end_half_day': reshedule_data.end_hd,
                                                'team': reshedule_data.drilling_team,
                                                'visit_date': reshedule_data.visit_date
                                            },
                                            'async': false,
                                            'callback': function(response) {
                                                frappe.bohrplaner.reset_dates(frappe.bohrplaner.page);
                                            }
                                        });
                                    },
                                    'primary_action_label': __('Reschedule'),
                                    'title': __("Details")
                                });
                                d.fields_dict.ht.$wrapper.html(html);
                                d.show();
