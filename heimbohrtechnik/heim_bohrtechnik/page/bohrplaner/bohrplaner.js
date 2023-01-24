var disable_text = __("Disable Auto Update");

frappe.pages['bohrplaner'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Bohrplaner',
        single_column: true
    });
    
    // set full-width if not
    if (document.getElementsByTagName("body")[0].className != 'full-width') {
        frappe.ui.toolbar.toggle_full_width();
    }

    // create page
    frappe.bohrplaner.make(page);
    // run page
    frappe.bohrplaner.run(page);
    
    // buttons
    page.add_menu_item( __('Auto Update'), () => {
        frappe.bohrplaner.auto_update(page);
    });
    
    page.set_secondary_action( __('Soft Reload'), () => {
        frappe.bohrplaner.reset_dates(page);
    });
    page.add_menu_item(__('Drucken'), () => {
        var from = $("#from").val();
        var to = $("#to").val();
        print_content(page, from, to);
    });
    page.set_primary_action( __('Search'), () => {
        frappe.bohrplaner.search(page);
    });
    
    // check routes and if there is a route, navigate to this
    frappe.bohrplaner.load_route(page);
}

// on show trigger: every time the page is displayed (even if loaded in the background
frappe.pages['bohrplaner'].on_page_show = function(wrapper) {
    frappe.bohrplaner.load_route(frappe.bohrplaner.page);
}

frappe.bohrplaner = {
    make: function(page) {
        var me = frappe.bohrplaner;
        me.page = page;
        
        var planning_days = 30;
        // fetch planning days
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_user_planning_days',
            'async': false,
            'args': {
                'user': frappe.session.user
            },
            callback: function(response) {
                locals.planning_days = response.message.planning_days;
                locals.planning_past_days = response.message.planning_past_days;
            }
        });
        
        // set today as default "from" date
        var now = new Date();
        var from_date = frappe.datetime.add_days(now, (-1) * locals.planning_past_days);
        var to_date = frappe.datetime.add_days(now, locals.planning_days);
        
        //get template data
        var data = frappe.bohrplaner.get_content(page, from_date, to_date);
        
        // render calendar grid
        data['print_view'] = 0;
        $(frappe.render_template('calendar_grid', data)).appendTo(me.page.body);
    },
    run: function(page) {
        // set today as default "from" date
        var now = new Date();
        document.getElementById("from").value = frappe.datetime.add_days(now, (-1) * locals.planning_past_days);
        
        // set today + 30d as default "to" date
        document.getElementById("to").value = frappe.datetime.add_days(now, locals.planning_days);
        
        // set trigger for date changes
        this.page.main.find("#from").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        this.page.main.find("#to").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        
        // get/add overlays
        frappe.bohrplaner.get_overlay_data(page);
        
        
    },
    load_route: function(page) {
        if (frappe.route_options.from && frappe.route_options.project_name) {
            document.getElementById("from").value = frappe.datetime.add_days(frappe.route_options.from, (-1) * locals.planning_past_days);
            document.getElementById("to").value = frappe.datetime.add_days(frappe.route_options.from, locals.planning_days);
            let date_reset = new Promise(function(ok, nok) {
                frappe.bohrplaner.reset_dates(page);
                ok();
            });
            date_reset.then(
                function(value) {
                    frappe.bohrplaner.mark_project(frappe.route_options.project_name);
                },
                function(error) { /* code if some error */ }
            );
        }
    },
    get_content: function(page, from_date, to_date) {
        var data;
        
        // get drilling teams
        frappe.call({
           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_content",
           args: {
                "from_date": from_date,
                "to_date": to_date
           },
           async: false,
           callback: function(response) {
                var content = response.message;
                data = {
                    drilling_teams: content.drilling_teams,
                    days: content.days,
                    weekend: content.weekend,
                    kw_list: content.kw_list,
                    day_list: content.day_list,
                    today: content.today
                };
           }
        });
        
        return data
    },
    get_overlay_data: function(page) {
        var from = $("#from").val();
        var to = $("#to").val();
        frappe.call({
           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_overlay_datas",
           args: {
                "from_date": from,
                "to_date": to
           },
           async: false,
           callback: function(response) {
                var contents = response.message;
                for (var i = 0; i < contents.length; i++) {
                    var data = contents[i];
                    frappe.bohrplaner.add_overlay(page, data);
                }
                if (locals.print_view !== 1) {
                    frappe.bohrplaner.get_subproject_overlay_data(page);
                }
           }
        });
        frappe.call({
           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_internal_overlay_datas",
           args: {
                "from_date": from,
                "to_date": to
           },
           async: false,
           callback: function(response) {
                var contents = response.message;
                for (var i = 0; i < contents.length; i++) {
                    var data = contents[i];
                    frappe.bohrplaner.add_internal_overlay(page, data);
                }
           }
        });
    },
    get_subproject_overlay_data: function(page) {
        var from = $("#from").val();
        var to = $("#to").val();
        frappe.call({
           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_subproject_overlay_datas",
           args: {
                "from_date": from,
                "to_date": to
           },
           async: false,
           callback: function(response) {
                var contents = response.message;
                for (var i = 0; i < contents.length; i++) {
                    var data = contents[i];
                    frappe.bohrplaner.add_subproject_overlay(page, data);
                }
                frappe.bohrplaner.get_absences_overlay_data(page);
           }
        });
    },
    get_absences_overlay_data: function(page) {
        var from = $("#from").val();
        var to = $("#to").val();
        frappe.call({
           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_absences_overlay_datas",
           args: {
                "from_date": from,
                "to_date": to
           },
           async: false,
           callback: function(response) {
                var contents = response.message;
                for (var i = 0; i < contents.length; i++) {
                    var data = contents[i];
                    frappe.bohrplaner.add_absences_overlay(page, data);
                }
           }
        });
    },
    add_overlay: function(page, data) {
        var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="' + data.vmnm + '"]');
        $(place).css("position", "relative");
        var qty = data.dauer
        var width = 42 * qty;
        $(frappe.render_template('booking_overlay', {
            'width': width, 
            'project': data.project, 
            'saugauftrag': data.saugauftrag, 
            'pneukran': data.pneukran, 
            'manager_short': data.manager_short, 
            'drilling_equipment': data.drilling_equipment, 
            'ampeln': data.ampeln
        })).appendTo(place);
        return
    },
    add_internal_overlay: function(page, data) {
        var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="' + data.vmnm + '"]');
        $(place).css("position", "relative");
        var qty = data.dauer
        var width = 42 * qty;
        $(frappe.render_template('internal_overlay', {'width': width, 'project': data.project})).appendTo(place);
        return
    },
    add_subproject_overlay: function(page, data) {
        var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="vm"]');
        
        if (data.subproject_shift === 1) {
            place = $('[data-bohrteam="' + data.bohrteam + '-2"][data-date="' + data.start + '"][data-vmnm="vm"]');
        } else if (data.subproject_shift > 1) {
            place = $('[data-bohrteam="' + data.bohrteam + '-3"][data-date="' + data.start + '"][data-vmnm="vm"]');
        }
        
        $(place).css("position", "relative");
        var qty = data.dauer
        
        $(frappe.render_template('subproject_overlay', {
            'width': (42 * data.dauer), 
            'subproject': data.id, 
            'description': data.description, 
            'subproject_shift': data.subproject_shift,
            'project': data.project,
            'customer_name': data.customer_name,
            'ews_details': data.ews_details,
            'object_name': data.object_name,
            'object_street': data.object_street,
            'object_location': data.object_location,
            'parent_project': data.project,
            'subcontracting_order': data.subcontracting_order
        })).appendTo(place);
        return
    },
    add_absences_overlay: function(page, data) {
        var place = $('[data-bohrteam="absences"][data-date="' + data.start + '"][data-vmnm="vm"]');
        $(place).css("position", "relative");
        var qty = data.dauer
        var width = (42 * qty);
        
        $(frappe.render_template('absence_overlay', {
            'width': width, 
            'absence': data.absence,
            'employee_name': data.employee_name,
            'shift': data.shift
        })).appendTo(place);
        return
    },
    reset_dates: function(page) {
        // pre safe scroll-positions
        var top_position = 0;
        var lef_position = 0;
        try {
            top_position = $("#bohrplan_wrapper").scrollTop();
            lef_position = $("#bohrplan_wrapper").scrollLeft();
        } catch {
            top_position = 0;
            lef_position = 0;
        }
        
        // pre safe new dates
        var from = $("#from").val();
        var to = $("#to").val();
        // remove old grid
        $("#bohrplan_wrapper").remove();
        //get template data
        var data = frappe.bohrplaner.get_content(page, from, to);
        data['print_view'] = locals.print_view;
        // render calendar grid
        $(frappe.render_template('calendar_grid', data)).appendTo(page.body);
        // set saved dates
        document.getElementById("from").value = from;
        document.getElementById("to").value = to;
        // set scroll-positions
        $("#bohrplan_wrapper").scrollTop(top_position);
        $("#bohrplan_wrapper").scrollLeft(lef_position);
        // reset triggers
        this.page.main.find("#from").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        this.page.main.find("#to").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        // get/add overlays
        frappe.bohrplaner.get_overlay_data(page);
    },
    auto_update: function(page) {
        var target = "[data-label='" + __("Auto Update") + "'";
        try {
            if ($(target)[0].innerHTML === disable_text) {
                $(target)[0].innerHTML = __("Auto Update");
            } else {
                $(target)[0].innerHTML = disable_text;
                frappe.bohrplaner.delay_update(page);
            }
        } catch (e) {
            console.log("element not found");
        }
    },
    delay_update: function(page) {
        setTimeout( function(page) {
            var target = "[data-label='" + __("Auto Update") + "'";
            try {
                if ($(target)[0].innerHTML === disable_text) {
                    frappe.bohrplaner.reset_dates(page);
                    frappe.bohrplaner.delay_update(page);
                }
            }
            catch (e) {
                console.log("element not found");
            }
        }, (5 * 60 * 1000), page);          // reload every 5 minutes
    },
    show_detail_popup: function(elemnt) {
        var _project = $(elemnt).attr("data-popupvalue");
        frappe.call({
            "method": "frappe.client.get",
            "args": {
                "doctype": "Project",
                "name": _project
            },
            "callback": function(response) {
                var project = response.message;

                if (project) {
                    frappe.call({
                        "method": "frappe.client.get",
                        "args": {
                            "doctype": "Object",
                            "name": project.object
                        },
                        "callback": function(r) {
                            var object = r.message;

                            if (object) {
                                var data = {
                                    'object': object.name,
                                    'project': project.name,
                                    'sales_order': project.sales_order,
                                    'object_location': object.object_location,
                                    'cloud_url': project.cloud_url
                                };
                                
                                data.customer = __('No Customer found');
                                data.customer_name = '';
                                if (project.customer) {
                                    data.customer = project.customer;
                                    data.customer_name = project.customer_name;
                                }
                                
                                data.mud_disposer = null;
                                data.mud_disposer_name = null;
                                for (var i = 0; i < project.checklist.length; i++) {
                                    if (project.checklist[i].activity === "Schlammentsorgung") {
                                        data.mud_disposer_name = project.checklist[i].supplier_name;
                                        data.mud_disposer = project.checklist[i].supplier;
                                    }
                                }
                                
                                data.drilling_equipment = [];
                                if (project.drilling_equipment) {
                                    for (var i = 0; i < project.drilling_equipment.length; i++) {
                                        data.drilling_equipment.push(project.drilling_equipment[i].drilling_equipment);
                                    }
                                }
                                
                                data.manager = __('No Manager found');
                                if (project.manager) {
                                    data.manager = project.manager;
                                }
                                
                                data.ews_details = __('No EWS Details found');
                                if (project.ews_details) {
                                    data.ews_details = project.ews_details;
                                }
                                
                                html = frappe.render_template("detail_dialog", data );
                                var d = new frappe.ui.Dialog({
                                    'fields': [
                                        {'fieldname': 'ht', 'fieldtype': 'HTML'},
                                        {'fieldname': 'section_1', 'fieldtype': 'Section Break'},
                                        {'fieldname': 'start', 'label': __('Start'), 'fieldtype': 'Date', 'default': project.expected_start_date, 'reqd': 1},
                                        {'fieldname': 'start_hd', 'label': __('Start Half-Day'), 'fieldtype': 'Select', 'options': 'VM\nNM', 'default': project.start_half_day},
                                        {'fieldname': 'drilling_team', 'label': __("Drilling Team"), 'fieldtype': 'Link', 'options': 'Drilling Team', 'default': project.drilling_team, 'reqd': 1},
                                        {'fieldname': 'cb_1', 'fieldtype': 'Column Break'},
                                        {'fieldname': 'end', 'label': __('End'), 'fieldtype': 'Date', 'default': project.expected_end_date, 'reqd': 1},
                                        {'fieldname': 'end_hd', 'label': __('End Half-Day'), 'fieldtype': 'Select', 'options': 'VM\nNM', 'default': project.end_half_day}
                                    ],
                                    primary_action: function(){
                                        d.hide();
                                        var reshedule_data = d.get_values();
                                        // reschedule_project
                                        frappe.call({
                                           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.reschedule_project",
                                           args: {
                                                "popup": 1,
                                                "project": project.name,
                                                'new_project_start': reshedule_data.start,
                                                "start_half_day": reshedule_data.start_hd,
                                                'new_project_end_date': reshedule_data.end,
                                                'end_half_day': reshedule_data.end_hd,
                                                'team': reshedule_data.drilling_team
                                           },
                                           async: false,
                                           callback: function(response) {
                                                frappe.bohrplaner.reset_dates(frappe.bohrplaner.page);
                                           }
                                        });
                                    },
                                    primary_action_label: __('Reshedule'),
                                    title: __("Details")
                                });
                                d.fields_dict.ht.$wrapper.html(html);
                                d.show();
                            } else {
                                frappe.msgprint("Object not found");
                            }
                        }
                    });
                } else {
                    frappe.msgprint("Project not found");
                }
            }
        });
    },
    make_mobile: function(page) {
        var me = frappe.bohrplaner;
        me.page = page;
        
        $(frappe.render_template('mobile_view', {})).appendTo(me.page.main);
    },
    open_project: function(element) {
        var project = $(element).attr("data-project");
        url_to_form("Project", project, function (r) { window.open(r.message, '_blank'); });
    },
    open_parent_project: function(element) {
        var parent_project = $(element).attr("data-parentproject");
        url_to_form("Project", parent_project, function (r) { window.open(r.message, '_blank'); });
    },
    open_subcontracting_order: function(element) {
        var parent_project = $(element).attr("data-subcontracting_order");
        url_to_form("Subcontracting Order", parent_project, function (r) { window.open(r.message, '_blank'); });
    },
    mark_project: function(project_name) {
        var project_element = document.getElementById(project_name);
        if (project_element) {
            project_element.scrollIntoView({inline: 'center'});
            document.getElementById("bohrplan_wrapper").scrollTop = document.getElementById("bohrplan_wrapper").scrollTop - 150;
            project_element.style.backgroundColor = "yellow";
        } else {
            console.log("Project element to be marked not found: " + project_name);
        }
    },
    search: function(page) {
        frappe.prompt([
                {'fieldname': 'project', 'fieldtype': 'Link', 'label': __('Project'), 'options': 'Project', 'reqd': 1}  
            ],
            function(values){
                frappe.call({
                    'method': 'frappe.client.get',
                    'args': {
                        'doctype': 'Project',
                        'name': values.project
                    },
                    'callback': function(r) {
                        if (r.message) {
                            frappe.route_options.from = r.message.expected_start_date;
                            frappe.route_options.project_name = values.project;
                            frappe.bohrplaner.load_route(page);
                        }
                    }
                });
            },
            __('Search project'),
            __('OK')
        );
    }
}

function allowDrop(ev) {
    ev.preventDefault();
    try {
        // Check Lanetyp of drop-element and target
        var drop_data = ev.dataTransfer.getData('text');
        var drop_element = document.getElementById(drop_data);
        var lanetype_drop_element = $(drop_element).attr("data-lanetype");
        var lanetype_drop_target = ev.target.dataset.lanetype;
        if (lanetype_drop_element && lanetype_drop_target) {
            if (lanetype_drop_element == lanetype_drop_target) {
                // go for it
                var to_get_droped = $("[data-dropid='" + ev.target.dataset.dropid + "']")[0];
                to_get_droped.classList.add("ondragover");
            } else {
                // stop it
                var to_get_droped = $("[data-dropid='" + ev.target.dataset.dropid + "']")[0];
                to_get_droped.classList.add("ondragover_dissallow");
            }
        }
    } catch(err) {}
}

function dragLeave(ev) {
    ev.preventDefault();
    try {
        var leaved = $("[data-dropid='" + ev.target.dataset.dropid + "']")[0];
        leaved.classList.remove("ondragover");
        leaved.classList.remove("ondragover_dissallow");
    } catch(err) {}
}

function drag(ev) {
    ev.dataTransfer.setData('text', ev.target.id);
    var drag_element = document.getElementById(event.target.id);
}

function drop(ev) {
    ev.preventDefault();
    // Check Lanetyp of drop-element and target
    var drop_data = ev.dataTransfer.getData('text');
    var drop_element = document.getElementById(drop_data);
    var lanetype_drop_element = $(drop_element).attr("data-lanetype");
    var lanetype_drop_target = ev.target.dataset.lanetype;
    if (lanetype_drop_element && lanetype_drop_target) {
        if (lanetype_drop_element == lanetype_drop_target) {
            // go for it
            var data = ev.dataTransfer.getData('text');
            $("[data-dropid='" + ev.target.dataset.dropid + "']").css("position", "relative");
            var dropped_element = document.getElementById(data);
            ev.target.appendChild(dropped_element);
            $("[data-dropid='" + ev.target.dataset.dropid + "']").removeClass("ondragover");
            reshedule(data, $(ev.target).attr("data-bohrteam"), $(ev.target).attr("data-date"), $(ev.target).attr("data-vmnm"), lanetype_drop_element)
        } else {
            // stop it
            show_alert('Projekte und Verlängerungsteams können nicht vermischt werden.');
            $("[data-dropid='" + ev.target.dataset.dropid + "']").removeClass("ondragover_dissallow");
        }
    }
}

function reshedule(ref_id, team, day, start_half_day, lanetype) {
    if (lanetype == 'Project') {
        frappe.call({
           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.reschedule_project",
           args: {
                "project": ref_id,
                "team": team,
                "day": day,
                "start_half_day": start_half_day
           },
           callback: function(response) {
                
           }
        });
    } else {
        frappe.call({
           method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.reschedule_subcontracting",
           args: {
                "subcontracting": ref_id,
                "team": team,
                "day": day
           },
           callback: function(response) {
                
           }
        });
    }
}

function print_content(page, from, to) {
   
    frappe.dom.freeze('Bitte warten, das PDF wird erzeugt...');
    // create html
    locals.print_view = 1;
    frappe.bohrplaner.reset_dates(page);
    
    var bp_html = $("#bohrplan_wrapper").html();
                
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.print_bohrplaner',
        'args': {
            'html': bp_html
        },
        callback: function(r) {
            window.open(r.message, '_blank');
            
            // reset from print
            locals.print_view = 0;
            frappe.bohrplaner.reset_dates(page);
            frappe.dom.unfreeze();
        }
    });
        
    
}
