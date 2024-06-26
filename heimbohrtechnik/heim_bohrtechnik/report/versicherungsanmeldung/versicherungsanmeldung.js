// Copyright (c) 2022-2024, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Versicherungsanmeldung"] = {
    "filters": [
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), (-1) * ((new Date().getDay() - 1)) + 7),
            "reqd": 1
        },
        {
            "fieldname":"to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_days(frappe.datetime.get_today(), (-1) * ((new Date().getDay() - 1)) + 12),
            "reqd": 1
        }
    ],
    "onload": function() {
        frappe.query_report.page.add_inner_button( __("Nach Excel"), function() {
            create_excel();
        });
    }
};

function create_excel() {
    frappe.prompt([
        {'fieldname': 'input', 'fieldtype': 'Data', 'label': 'Zeile oder Projektnummer', 'reqd': 1}  
    ],
    function(values){
        var project = null;
        // in case of an index, use this
        if ((parseInt(values.input) > 0) && (parseInt(values.input) <= frappe.query_report.data.length)) {
            project = frappe.query_report.data[parseInt(values.input - 1)].project;
        } else {
            for (var i = 0; i < frappe.query_report.data.length; i++) {
                if (frappe.query_report.data[i].project.includes(values.input)) {
                    project = frappe.query_report.data[i].project;
                    break;
                }
            }
        }
        
        if (project) {
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.project.insurance_application',
                'args': {
                    'project': project
                },
                'callback': function(response) {
                    navigator.clipboard.writeText(response.message).then(function() {
                        frappe.show_alert( __("Daten in der Zwischenablage, bitte ins Versicherungstool einfügen") );
                        frappe.db.set_value("Project", project, "insurance_declared", 1);
                    }, function() {
                         frappe.show_alert( __("Kein Zugriff auf Zwischenablage") );
                    });
                }
            });
        } else {
            frappe.messageprint( __("Projekt nicht gefunden") );
        }
    },
    __('Versicherungsanmeldung für ein Projekt erstellen'),
    __('Erstellen')
    );
}
