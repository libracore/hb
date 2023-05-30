// extend dashboard
try {
    cur_frm.dashboard.add_transactions([
        {
            'label': 'Documents',
            'items': ['Construction Site Description', 'Bohranzeige', 'Request for Public Area Use', 'Infomail']
        },
        {
            'label': 'Drilling',
            'items': ['Construction Site Delivery', 'Subcontracting Order', 'Request for Public Area Use', 'Layer Directory', 'Injection report']

        }
    ]);
} catch { /* do nothing for older versions */ }

frappe.ui.form.on('Project', {
    refresh(frm) {
        // show permits & checklist (in case coming from another record where it was hidden)
        var checklists = document.querySelectorAll("[data-fieldname='checklist']");
        try {
            for (var i = 0; i < checklists.length; i++) {
                checklists[i].parentElement.parentElement.parentElement.parentElement.style.display = "Block";
            }
        } catch { /* do nothing */ }
        // filter suppliers by activity
        frm.fields_dict.checklist.grid.get_field('supplier').get_query =   
            function(doc, cdt, cdn) {    
                var row = locals[cdt][cdn];
                return {
                    query: "heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability",
                    filters: {
                        'capability': row.activity,
                        'disabled': 0
                    }
                };
        };
        // filter for drilling teams
        cur_frm.fields_dict['drilling_team'].get_query = function(doc) {
            if (frm.doc.project_type !== "Internal") {
                return {
                    filters: {
                        "drilling_team_type": "Bohrteam"
                    }
                }
            }
        }
        frm.fields_dict.subprojects.grid.get_field('team').get_query = function(doc, cdt, cdn) {    
            return {
                filters: {
                    "drilling_team_type": "Verlängerungsteam"
                }
            };
        };
        
        // check if mud can be invoiced
        if (!frm.doc.__islocal) {
            frappe.call({
                'method': 'heimbohrtechnik.mudex.doctype.truck_delivery.truck_delivery.has_invoiceable_mud',
                'args': {'object': frm.doc.name},
                'callback': function(response) {
                    if (response.message) {
                        frm.add_custom_button( __("Abrechnen"), function() {
                            create_mud_invoice(frm.doc.name);
                        }, "MudEX");
                    }
                }
            });
            // add link-button to drillplanner
            frm.add_custom_button(__("Öffne Bohrplaner"), function() {
                frappe.route_options = {"from": cur_frm.doc.expected_start_date, "project_name": cur_frm.doc.name}
                frappe.set_route("bohrplaner");
            });
            // add button to open construction site description
            add_construction_site_description_button(frm, frm.doc.name);
            // show insurance information
            show_insurance_information(frm.doc.name);
            // split project button
            frm.add_custom_button(__("Projekt teilen"), function() {
                frappe.confirm(
                    __('Soll das Projekt wirklich aufgeteilt werden?'),
                    function(){
                        // on yes
                        frappe.call({
                            'method': "heimbohrtechnik.heim_bohrtechnik.project.split_project",
                            'args': {
                                'project': frm.doc.name
                            },
                            'callback': function(response) {
                                window.location.href=response.message.uri;
                            }
                        });
                    },
                    function(){
                        // on no
                    }
                )
            }, __("More") );
            // create full project file
            frm.add_custom_button(__("Dossier erstellen"), function() {
                create_full_file(frm);
            }, __("PDFs"));
            // create and attach pdf
            frm.add_custom_button(__("Bohrauftrag"), function() {
                create_pdf(frm);
            }, __("PDFs"));
            
            // for external projects
            if (frm.doc.project_type === "External") {
                // show siblings
                check_display_siblings("Project", frm.doc.name);
                // open cloud button
                if (!frm.doc.cloud_url) {
                    frappe.call({
                        'method': "heimbohrtechnik.heim_bohrtechnik.nextcloud.get_cloud_url",
                        'args': {
                            'project': frm.doc.name
                        },
                        'callback': function(response) {
                            cur_frm.set_value("cloud_url", response.message);
                        }
                    });
                }
                frm.add_custom_button(__("Cloud"), function() {
                    window.open(frm.doc.cloud_url, '_blank').focus();
                });
            }
            // request google review
            if ((frm.doc.review_email) && (!frm.doc.review_date)) {
                frm.add_custom_button(__("Google Rezension anfragen"), function() {
                    request_review(frm);
                });
            }
            // prepare localStorage
            localStorage.setItem("project", frm.doc.name);
            localStorage.setItem("project_manager", frm.doc.manager);
        } else {
            // new project: switch to internal and assign name/title
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.utils.get_next_internal_project_number',
                'callback': function(response) {
                    cur_frm.set_value("object_name", "Wartung");
                    cur_frm.set_value("project_type", "Internal");
                    cur_frm.set_value("project_name", response.message);
                }
            });
        }
        if (frm.doc.project_type === "Internal") {
            // button to change description
            frm.add_custom_button(__("Beschreibung ändern"), function() {
                frappe.prompt([
                    {
                        'fieldname': 'description', 
                        'fieldtype': 'Data', 
                        'label': __("Description"), 
                        'reqd': 1,
                        'default': frm.doc.object_name
                    }  
                ],
                function(values){
                    cur_frm.set_value("object_name", values.description);
                },
                'Beschreibung ändern',
                'OK'
                )
            });
            // hide drilling fields
            cur_frm.set_df_property('object', 'hidden', 1);
            cur_frm.set_df_property('drill_notice_sent', 'hidden', 1);
            cur_frm.set_df_property('thermozement', 'hidden', 1);
            cur_frm.set_df_property('section_checklist', 'hidden', 1);
            cur_frm.set_df_property('customer_details', 'hidden', 1);
            cur_frm.set_df_property('section_subprojects', 'hidden', 1);
        }
        // fetch visit information
        fetch_visit_date(frm);
        // show noise permit checkbox if applicable
        if (frm.doc.permits) {
            for (var i = 0; i < frm.doc.permits.length; i++) {
                if (frm.doc.permits[i].permit === "Lärmschutzbewilligung") {
                    cur_frm.set_df_property("noise_permit_requested", "hidden", 0);
                    break;
                }
            }
        }
    },
    before_save(frm) {
        // hook to update subcontracting orders in case of changes
        if ((frm.doc.subprojects) && (frm.doc.subprojects.length)) {
            for (var s = 0; s < frm.doc.subprojects.length; s++) {
                if ((frm.doc.subprojects[s].subcontracting_order) && (frm.doc.subprojects[s].team)) {
                    frappe.call({
                        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.subcontracting_order.subcontracting_order.update_from_project',
                        'args': {
                            'subcontracting_order': frm.doc.subprojects[s].subcontracting_order,
                            'start_date': frm.doc.subprojects[s].start,
                            'end_date': frm.doc.subprojects[s].end,
                            'drilling_team': frm.doc.subprojects[s].team,
                            'description': frm.doc.subprojects[s].description
                        }
                    });
                }
            }
        }
    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
    }
});

function create_full_file(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.create_full_project_file',
        'args': {'project': frm.doc.name},
        'callback': function(response) {
            cur_frm.reload_doc();
        },
        'freeze': true,
        'freeze_message': __("Dossier erstellen, bitte warten...")
    });
}

function create_pdf(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.update_attached_project_pdf',
        'args': {'project': frm.doc.name},
        'callback': function(response) {
            cur_frm.reload_doc();
        },
        'freeze': true,
        'freeze_message': __("Bohrauftrag (pdf) erstellen, bitte warten...")
    });
}

function request_review(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.request_google_review',
        'args': {'project': frm.doc.name},
        'callback': function(response) {
            frappe.show_alert("Mail versendet...");
            cur_frm.reload_doc();
        },
        'freeze': true,
        'freeze_message': __("Google Rezension anfragen...")
    });
}

function fetch_visit_date(frm) {
    if (frm.doc.visit_date) {
        frappe.call({
            'method': "frappe.client.get",
            'args': {
                'doctype': "Event",
                'name': frm.doc.visit_date
            },
            'callback': function(response) {
                var visit_event = response.message;

                if (visit_event) {
                    var info = "<p>" 
                        + (visit_event.starts_on ? (new Date(visit_event.starts_on)).toLocaleString() : "??") 
                        + " - " 
                        + (visit_event.ends_on ? (new Date(visit_event.starts_on)).toLocaleString() : "??") 
                        + "</p>";
                    cur_frm.set_df_property('visit_info_html', 'options', info);
                }
            }
        });
    } else {
        // clear
        console.log("clear");
        cur_frm.set_df_property('visit_info_html', 'options', "<div></div>");
    }
}
