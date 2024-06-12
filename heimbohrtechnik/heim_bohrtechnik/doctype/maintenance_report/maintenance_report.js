// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maintenance Report', {
    refresh: function(frm) {
        // prepare filters
        cur_frm.fields_dict['project'].get_query = function(doc) {
            return {
                'filters': {
                    'project_type': "Internal"
                }
            }
        }
        cur_frm.fields_dict['truck'].get_query = function(doc) {
            return {
                'filters': {
                    'drilling_team': cur_frm.doc.drilling_team
                }
            }
        }
        
        if (frm.doc.__islocal) {
            if ((!frm.doc.project) && (frappe.route_history.length > 0) && (frappe.route_history[0][1] === "Project")) {
                // find last visited project from navigation history
                cur_frm.set_value('project', frappe.route_history[0][2]);
            }
            // new form from a route: fetch project
            if (frm.doc.project) {
                fetch_project_details(frm);
            }
        }
    },
    project: function(frm) {
        if (frm.doc.project) {
            fetch_project_details(frm);
        }
    }
});

function fetch_project_details(frm) {
    frappe.call({
        "method": "frappe.client.get",
        "args": {
            "doctype": "Project",
            "name": frm.doc.project
        },
        "callback": function(response) {
            var project = response.message;
            cur_frm.set_value('drilling_team', project.drilling_team);
            cur_frm.set_value('date', project.expected_start_date);
            
        }
    });
}
