// extend dashboard
cur_frm.dashboard.add_transactions([
    {
        'label': 'Documents',
        'items': ['Construction Site Description', 'Bohranzeige', 'Request for Public Area Use', 'Water Supply Registration', 'Infomail']
    },
    {
        'label': 'Drilling',
        'items': ['Construction Site Delivery', 'Subcontracting Order', 'Request for Public Area Use', 'Road Block Material Order', 'Layer Directory', 'Injection report', 'Drilling Sample']

    }
]);

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
            // highlight notes if available
            if (frm.doc.notes) {
                cur_frm.dashboard.add_comment( "Hinweise beachten!", 'blue', true);
            }
            
            if (frappe.user.has_role("Projects Manager")) {     // restrict to projects managers
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
                frm.add_custom_button(__("Insurance application"), function() {
                    insurance_application(frm);
                }, __("More") );
                if ((!frm.doc.__islocal) && (frm.doc.project_type === "Internal")) {
                    frm.add_custom_button(__("Maintenance Report"), function() {
                        show_or_create_maintenance_report(frm);
                    }, __("More") );
                }
            }
            // create full project file
            frm.add_custom_button(__("Dossier erstellen"), function() {
                create_full_file(frm);
            }, __("PDFs"));
            // create and attach pdf
            frm.add_custom_button(__("Bohrauftrag"), function() {
                create_pdf(frm);
            }, __("PDFs"));
            // create and attach for combined SV+IB pdf
            frm.add_custom_button(__("SV+IB"), function() {
                create_sv_ib(frm);
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
        // show noise permit checkbox if applicable
        if (frm.doc.permits) {
            for (var i = 0; i < frm.doc.permits.length; i++) {
                if (frm.doc.permits[i].permit === "Lärmschutzbewilligung") {
                    cur_frm.set_df_property("noise_permit_requested", "hidden", 0);
                    break;
                }
            }
        }
        
        // scroll back behaviour
        if (locals.scroll_to) {
            frappe.utils.scroll_to(document.querySelector("[data-fieldname='" + locals.scroll_to + "']"));
            locals.scroll_to = null;        // reset to prevent other scrolling
        }
        
        // access: restrict field access for non-project managers
        if (!frappe.user.has_role("Projects Manager") ) {
            cur_frm.set_df_property('status', 'read_only', 1);
            cur_frm.set_df_property('expected_start_date', 'read_only', 1);
            cur_frm.set_df_property('start_half_day', 'read_only', 1);
            cur_frm.set_df_property('expected_end_date', 'read_only', 1);
            cur_frm.set_df_property('end_half_day', 'read_only', 1);
            cur_frm.set_df_property('project_type', 'read_only', 1);
            cur_frm.set_df_property('object', 'read_only', 1);
            cur_frm.set_df_property('customer', 'read_only', 1);
            cur_frm.set_df_property('sales_order', 'read_only', 1);
        }
        
        // disable heatmap
        let heatmap = document.getElementsByClassName("form-heatmap");
        for (let i = 0; i < heatmap.length; i++) {
            heatmap[i].style.display = "None";
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
    },
    expected_start_date: function(frm) {
        if (!frm.doc.__islocal && frm.doc.object && frm.doc.project_type == "External") {
            get_drilling_meters_per_day(frm);
        }
    },
    expected_end_date: function(frm) {
        if (!frm.doc.__islocal && frm.doc.object && frm.doc.project_type == "External") {
            get_drilling_meters_per_day(frm);
        }
    },
    start_half_day: function(frm) {
        if (!frm.doc.__islocal && frm.doc.object && frm.doc.project_type == "External") {
            get_drilling_meters_per_day(frm);
        }
    },
    end_half_day: function(frm) {
        if (!frm.doc.__islocal && frm.doc.object && frm.doc.project_type == "External") {
            get_drilling_meters_per_day(frm);
        }
    },
    sales_order: function(frm) {
        if (frm.doc.sales_order) {
            check_sales_order(frm);
        }
    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
        
        get_default_trough_size(frm, dt, dn);
    }
});

frappe.ui.form.on('Construction Site Description Plan', {
    file: function(frm, cdt, cdn) {
        locals.scroll_to = "plans";         // store location before scroll on save
    }    
});

frappe.ui.form.on('Project Permit', {
    file: function(frm, cdt, cdn) {
        locals.scroll_to = "permits";       // store location before scroll on save
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
    // verify that in case there is an insurance required, the certificate is available
    if (frm.doc.checklist) {
        for (let i = 0; i < frm.doc.checklist.length; i++) {
            if ((frm.doc.checklist[i].activity === "Versicherung") && (!frm.doc.checklist[i].insurance_certificate)) {
                frappe.msgprint({
                    'title': __("Versicherungsanmeldung"),
                    'message': __("Dieses Projekt benötigt eine Versicherungsanmeldung, jedoch ist das Zertifikat noch nicht abgelegt. Bitte das Zertifikat in der Checkliste eintragen."), 
                    'indicator': 'red'
                });
                return
            }
        }
    }
    
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

function create_sv_ib(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.update_attached_sv_ib_pdf',
        'args': {'project': frm.doc.name},
        'callback': function(response) {
            cur_frm.reload_doc();
        },
        'freeze': true,
        'freeze_message': __("SV+IB(pdf) erstellen, bitte warten...")
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

function get_drilling_meters_per_day(frm) {
    if ((frm.doc.name) && (frm.doc.object) && (frm.doc.expected_start_date) && (frm.doc.start_half_day) && (frm.doc.expected_end_date) && (frm.doc.end_half_day)) {
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.utils.get_drilling_meters_per_day',
            'args': {
                'project': frm.doc.name,
                'objekt': frm.doc.object,
                'start_date': frm.doc.expected_start_date,
                'start_hd': frm.doc.start_half_day,
                'end_date': frm.doc.expected_end_date,
                'end_hd': frm.doc.end_half_day
            },
            'callback': function(response) {
                cur_frm.set_value('duration', response.message[0]);
                cur_frm.set_value('drilling_meter_per_day', response.message[1]);
            }
        });
    }
}

function insurance_application(frm) {
    if (cur_frm.is_dirty()) {
        cur_frm.save().then(function() {
            get_insurance_application(frm);
        });
    } else {
        get_insurance_application(frm);
    }
}

function get_insurance_application(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.project.insurance_application',
        'args': {
            'project': frm.doc.name
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
}

function show_or_create_maintenance_report(frm) {
    frappe.call({
        'method': 'frappe.client.get_list',
        'args': {
            'doctype': 'Maintenance Report',
            'filters': [
                ['project', '=', frm.doc.name]
            ],
            'fields': ['name'],
        },
        'callback': function(response) {
            if (response.message.length > 0) {
                frappe.set_route("Form", "Maintenance Report", response.message[0].name);
            } else {
                var target = __("New") + " " + __("Maintenance Report");
                frappe.set_route("Form", "Maintenance Report", target);
            }
        }
    });
}

function check_sales_order(frm) {
    cur_frm.save().then(() => {
        frappe.show_alert( __("Auftragsdaten abgleichen...") );
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.utils.check_create_project',
            'args': {
                'sales_order': cur_frm.doc.sales_order
            },
            'callback': function() {
                cur_frm.reload_doc();
                frappe.show_alert( __("Auftragsdaten OK") );
            }
        });
    });
}
