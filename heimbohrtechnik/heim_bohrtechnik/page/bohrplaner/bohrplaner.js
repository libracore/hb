var disable_text = __("Disable Auto Update");

frappe.pages['bohrplaner'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Bohrplaner',
        single_column: true
    });
    
    // add waiting area
    frappe.bohrplaner.add_wait(page);
    
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
    
    if (!frappe.user.has_role("Bohrmeister")) {
        page.add_menu_item(__('Drucken'), () => {
            var from = $("#from").val();
            var to = $("#to").val();
            print_content(page, from, to);
        });
    
        page.set_primary_action( __('Search'), () => {
            frappe.bohrplaner.search(page);
        });
    
        page.add_menu_item( __('Find conflicts'), () => {
            frappe.bohrplaner.find_conflicts(page);
        });
        
        page.add_menu_item( __('Alle Projekte schieben...'), () => {
            frappe.bohrplaner.move_projects(page);
        });
        
        page.add_menu_item( __('Bohrmeterübersicht'), () => {
            frappe.set_route("query-report", "Drilling Capacity Overview", {'from_date': $("#from").val(), 'to_date': $("#to").val()});
        });
        
        page.add_menu_item( __('Freien Termin suchen'), () => {
            get_avaliable_drilling_teams();
        });
    } else {
        //Set Dates Ready only, if User is a Drilling Master
        document.getElementById("from").readOnly = true;
        document.getElementById("to").readOnly = true; 
    }
    
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
        
        if (frappe.user.has_role("Bohrmeister")) {
            // hard-coded values for drilling masters
            let current_day = (new Date()).getDay();
            if (current_day < 5) {
                locals.planning_days = (6 - current_day);
            } else {
                locals.planning_days = 1;
            }
            locals.planning_past_days = 30;
            locals.print_block_length_factor = 42;
        } else {
            var planning_days = 30;
            // fetch planning days
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_user_planning_days',
                'async': false,
                'args': {
                    'user': frappe.session.user
                },
                'callback': function(response) {
                    locals.planning_days = response.message.planning_days;
                    locals.planning_past_days = response.message.planning_past_days;
                    locals.print_block_length_factor = response.message.print_block_length_factor;
                }
            });
        }
        
        // set today as default "from" date
        var now = new Date();
        var from_date = frappe.datetime.add_days(now, (-1) * locals.planning_past_days);
        var to_date = frappe.datetime.add_days(now, locals.planning_days);
        
        //get template data
        var data = frappe.bohrplaner.get_content(page, from_date, to_date);
        
        // render calendar grid
        data['print_view'] = 0;
        data['web_view'] = 0;
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
            
            frappe.bohrplaner.reset_dates(page);
            
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
         // start waiting indicator
        frappe.bohrplaner.start_wait(page);
        setTimeout(function(){
            frappe.bohrplaner._get_overlay_data(page);
        }, 100);
    },
    _get_overlay_data: function(page) {
        var from = $("#from").val();
        var to = $("#to").val();
        frappe.call({
           'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_overlay_datas",
           'args': {
                "from_date": from,
                "to_date": to
           },
           'async': false,
           'callback': function(response) {
                var contents = response.message;
                for (var i = 0; i < contents.length; i++) {
                    var data = contents[i];
                    frappe.bohrplaner.add_overlay(page, data);
                }
                    frappe.bohrplaner.get_subproject_overlay_data(page);
           }
        });
        frappe.call({
           'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_internal_overlay_datas",
           'args': {
                "from_date": from,
                "to_date": to
           },
           'async': false,
           'callback': function(response) {
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
           'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_subproject_overlay_datas",
           'args': {
                "from_date": from,
                "to_date": to
           },
           'async': false,
           'callback': function(response) {
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
           'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_absences_overlay_datas",
           'args': {
                "from_date": from,
                "to_date": to
           },
           'async': false,
           'callback': function(response) {
                var contents = response.message;
                for (var i = 0; i < contents.length; i++) {
                    var data = contents[i];
                    frappe.bohrplaner.add_absences_overlay(page, data);
                }
                // in case of search, mark project
                if (frappe.route_options.project_name) {
                    frappe.bohrplaner.mark_project(frappe.route_options.project_name);
                }
                
                frappe.bohrplaner.add_mfk_overlay(page);
                
                // stop waiting indicator
                frappe.bohrplaner.stop_wait(page);
           }
        });
    },
    add_overlay: function(page, data, as_print=false) {
        var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="' + data.vmnm + '"]');
        $(place).css("position", "relative");
        var qty = data.dauer;
        
        $(frappe.render_template('booking_overlay', {
            'width': 42 * qty, 
            'box_height': 13,
            'padding': 0,
            'font_size': 7,
            'min_width': 35,
            'max_width': 70,
            'project': data.project, 
            'saugauftrag': data.saugauftrag, 
            'pneukran': data.pneukran, 
            'manager_short': data.manager_short, 
            'drilling_equipment': data.drilling_equipment, 
            'ampeln': data.ampeln,
            'dragable': (frappe.user.has_role("Dispo")) ? 'true' : 'false',
            'ews_details': data.ews_details,
            'traffic_light': data.traffic_light,
            'toitoi': data.toitoi,
            'red_drop': data.red_drop,
            'blue_drop': data.blue_drop
        })).appendTo(place);
        return
    },
    add_internal_overlay: function(page, data) {
        var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="' + data.vmnm + '"]');
        $(place).css("position", "relative");
        var qty = data.dauer
        var width = 42 * qty;
        $(frappe.render_template('internal_overlay', {'width': width, 'project': data.project, 'font_size': 7})).appendTo(place);
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
        var qty = data.dauer;                               // duration is in half-days, i.e. 2 = 1 day
        
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
            'subcontracting_order': data.subcontracting_order,
            'dragable': (frappe.user.has_role("Dispo")) ? 'true' : 'false',
            'multi_day': (data.dauer > 2) ? 'multi_day' : 'single_day',
            'background': data.background,
            'manager_short': data.manager_short
        })).appendTo(place);
        return
    },
    add_absences_overlay: function(page, data) {
        var place = $('[data-bohrteam="absences"][data-date="' + data.start + '"][data-vmnm="vm"]');
        if (place.length === 0) {
            // in case this cannot be place because of the weekend at the start, move to the right
            var start_date_parts = data.start.split(".");
            var new_start = frappe.datetime.add_days(start_date_parts[2] + "-" + start_date_parts[1] + "-" + start_date_parts[0], 1);
            var new_start_parts = new_start.split("-");
            place = $('[data-bohrteam="absences"][data-date="' + new_start_parts[2] + '.' + new_start_parts[1] + '.' + new_start_parts[0] + '"][data-vmnm="vm"]');
        }
        $(place).css("position", "relative");
        var qty = data.dauer
        var width = (42 * qty);
        
        $(frappe.render_template('absence_overlay', {
            'width': width, 
            'absence': data.absence,
            'employee_name': data.employee_name,
            'shift': data.shift,
            'color': data.color,
            'remarks': data.remarks
        })).appendTo(place);
        return
    },
    add_mfk_overlay: function(page, data) {
        var from = $("#from").val();
        var to = $("#to").val();
        frappe.call({
           'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_mfk_overlay_datas",
           'args': {
                "from_date": from,
                "to_date": to
           },
           'async': false,
           'callback': function(response) {
                var contents = response.message;
                for (var i = 0; i < contents.length; i++) {
                    var data = contents[i];
                    
                    var place = $('[data-bohrteam="' + data.drilling_team + '"][data-date="' + data.start_date + '"][data-vmnm="nm"]');
                    $(place).css("position", "relative");
                    var width = 42
                    
                    $(frappe.render_template('mfk_overlay', {
                        'truck': data.truck,
                        'start_date': data.start_date,
                        'start_time': data.start_time,
                        'end_date': data.end_date,
                        'end_time': data.end_time,
                        'shift': data.shift
                    })).appendTo(place);
                }
                return
           }
        });
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
        var view_from = from;
        var view_to = to;
        var data = frappe.bohrplaner.get_content(page, view_from, view_to);
        data['print_view'] = 0;
        data['web_view'] = 0;
        // render calendar grid
        $(frappe.render_template('calendar_grid', data)).appendTo(page.body);
        // set saved dates
        document.getElementById("from").value = view_from;
        document.getElementById("to").value = view_to;
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
            'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_project_details",
            'args': {
                'project': _project
            },
            'callback': function(response) {
                let details = response.message;
            
                if (details.object) {
                    let data = {
                        'object': details.object.name,
                        'base_object': null,
                        'project': details.project.name,
                        'sales_order': details.project.sales_order,
                        'object_location': details.object.object_location,
                        'object_street': details.object.object_street,
                        'cloud_url': details.project.cloud_url,
                        'subprojects': []
                    };
                    let object_name_parts = details.object.name.split("-");
                    if (object_name_parts.length > 2) {
                        data.base_object = object_name_parts[0] + "-" + object_name_parts[1]
                    }
                    data.customer = __('No Customer found');
                    data.customer_name = '';
                    if (details.project.customer) {
                        data.customer = details.project.customer;
                        data.customer_name = details.project.customer_name;
                    }
                    
                    data.mud_disposer = null;
                    data.mud_disposer_name = null;
                    for (var i = 0; i < details.project.checklist.length; i++) {
                        if (details.project.checklist[i].activity === "Schlammentsorgung") {
                            data.mud_disposer_name = details.project.checklist[i].supplier_name;
                            data.mud_disposer = details.project.checklist[i].supplier;
                        }
                    }
                    
                    data.drilling_equipment = [];
                    if (details.construction_site_description.drilling_equipment) {
                        for (var i = 0; i < details.construction_site_description.drilling_equipment.length; i++) {
                            data.drilling_equipment.push(details.construction_site_description.drilling_equipment[i].drilling_equipment);
                        }
                    }
                    
                    data.manager = details.project.manager_name ? details.project.manager_name : __('No Manager found');
                    
                    if (details.project.subprojects) {
                        for (let s = 0; s < details.project.subprojects.length; s++) {
                            // only use the last part of the drilling team name (shorter)
                            let sub_team_parts = (details.project.subprojects[s].team || "").split(" ");
                            data.subprojects.push(new Date(details.project.subprojects[s].start).toLocaleDateString() 
                                + ": " + details.project.subprojects[s].description
                                + (sub_team_parts.length > 1 ? (" (" + sub_team_parts[sub_team_parts.length - 1] + ")") : "")
                            );
                        }
                    }
                    
                    data.ews_details = details.project.ews_details ? details.project.ews_details : __('No EWS Details found');
                    
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
                                'default': details.project.expected_start_date, 
                                'reqd': 1,
                                'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                            },
                            {
                                'fieldname': 'start_hd', 
                                'label': __('Start Half-Day'),
                                'fieldtype': 'Select',
                                'options': 'VM\nNM', 
                                'default': details.project.start_half_day,
                                'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                            },
                            {
                                'fieldname': 'drilling_team', 
                                'label': __("Drilling Team"), 
                                'fieldtype': 'Link', 
                                'options': 'Drilling Team', 
                                'default': details.project.drilling_team, 
                                'reqd': 1,
                                'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                            },
                            {
                                'fieldname': 'duration', 
                                'label': __("Duration"), 
                                'fieldtype': 'Float', 
                                'default': details.project.duration, 
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
                                'default': details.project.expected_end_date, 
                                'reqd': 1,
                                'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                            },
                            {
                                'fieldname': 'end_hd', 
                                'label': __('End Half-Day'), 
                                'fieldtype': 'Select', 
                                'options': 'VM\nNM', 
                                'default': details.project.end_half_day,
                                'read_only': (frappe.user.has_role("Dispo")) ? 0 : 1
                            },
                            {
                                'fieldname': 'visit_date', 
                                'label': __('Visit date'), 
                                'fieldtype': 'Date', 
                                'default': details.project.visit_date
                            },
                            {
                                'fieldname': 'meter_per_day', 
                                'label': __('Meter per Day'), 
                                'fieldtype': 'Int', 
                                'default': details.project.drilling_meter_per_day,
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
                                    "project": details.project.name,
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
    open_absence: function(element) {
        var absence = $(element).attr("data-absence");
        url_to_form("Leave Application", absence, function (r) { window.open(r.message, '_blank'); });
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
        var d = new frappe.ui.Dialog({
            'fields': [   
                {'fieldname': 'project', 'fieldtype': 'Link', 'label': __('Project'), 'options': 'Project', 'reqd': 1, 'change': function() {
                        if (d.get_value('project')) {
                            frappe.call({
                                'method':"heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_subproject_overview",
                                'args':{
                                    'project': d.get_value('project')
                                 },
                                'callback': function(r) {
                                    var options_html = r.message;
                                    d.set_df_property('subproject_view', 'options', options_html);
                                }
                            });
                        } else {
                            var options_html = '<p>Bitte ein Projekt auswählen</p>';
                            d.set_df_property('subproject_view', 'options', options_html);
                        }
                    }
                },
                {'fieldname': 'subproject_view', 'fieldtype': 'HTML', 'label': __('Subproject Overview'), 'options': '<p>Bitte ein Projekt auswählen</p>'}
            ],
            'primary_action': function() {
                d.hide();
                frappe.call({
                    'method': 'frappe.client.get',
                    'args': {
                        'doctype': 'Project',
                        'name': d.get_value('project')
                    },
                    'callback': function(r) {
                        if (r.message) {
                            frappe.route_options.from = r.message.expected_start_date;
                            frappe.route_options.project_name = d.get_value('project');
                            frappe.bohrplaner.load_route(page);
                        }
                    }
                });
            },
            'primary_action_label': __('OK'),
            'title': __('Search project')
        });
        d.show();
    },
    find_conflicts: function(page) {
        /* launch conflict finder */
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_conflicts',
            'callback': function(r) {
                if (r.message) {
                    // html = frappe.render_template("conflict_dialog", r.message);
                    var d = new frappe.ui.Dialog({
                        'fields': [
                            {'fieldname': 'ht', 'fieldtype': 'HTML'}
                        ],
                        'primary_action': function(){
                            d.hide();
                            frappe.prompt([
                                    {
                                        'fieldname': 'drilling_team', 
                                        'fieldtype': 'Link', 
                                        'label': __('Drilling Team'), 
                                        'options': 'Drilling Team', 
                                        'reqd': 1
                                    }
                                ],
                                function(values){
                                    frappe.call({
                                        'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.resolve_conflicts',
                                        'args': {
                                            'drilling_team': values.drilling_team
                                        },
                                        'callback': function(r) {
                                            frappe.show_alert( __("Updated") );
                                            frappe.bohrplaner.reset_dates(page);
                                        }
                                    });
                                },
                                __('Resolve conflicts'),
                                __('Resolve')
                            )

                        },
                        'primary_action_label': __('Resolve'),
                        'title': __("Conflicts")
                    });
                    d.fields_dict.ht.$wrapper.html(r.message);
                    d.show();
                }
            }
        });
    },
    add_wait: function(page) {
        var indicator_area = $(".indicator.whitespace-nowrap.hide");
        indicator_area.attr('id', 'wait_area');
        indicator_area.append('<i class="fa fa-spinner fa-spin" style="color: #274b82;"></i>');
        
    },
    start_wait: function(page) {
        $("#wait_area").removeClass("hide");
    },
    stop_wait: function(page) {
        $("#wait_area").addClass("hide");
    },
    move_projects: function(page) {
        var d = new frappe.ui.Dialog({
            'fields': [
                {
                    'fieldname': 'project', 
                    'fieldtype': 'Link', 
                    'label': __("Project"), 
                    'options': "Project", 
                    'change': function() {
                        if (d.get_value('project')) {
                            frappe.call({
                                'method':"frappe.client.get",
                                'args':{
                                    'doctype': "Project",
                                    'name': d.get_value('project')
                                 },
                                'callback': function(r) {
                                    d.set_value('drilling_team', r.message.drilling_team);
                                }
                            });
                        } 
                    }
                },
                {
                    'fieldname': 'drilling_team', 
                    'fieldtype': 'Data', 
                    'label': __("Drilling Team"), 
                    'read_only': 1
                },
                {
                    'fieldname': 'days', 
                    'fieldtype': 'Float', 'label': __("Days"), 'default': 1
                }
            ],
            'primary_action': function(){
                d.hide();
                var values = d.get_values();
                frappe.call({
                    'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.move_projects',
                    'args': {
                        'from_project': values.project,
                        'drilling_team': values.drilling_team,
                        'days': values.days
                    },
                    'freeze': true,
                    'freeze_message': __("Projekte schieben..."),
                    'callback': function(r) {
                        frappe.show_alert( __("Updated") );
                        console.log(r.message);
                        frappe.bohrplaner.reset_dates(page);
                    }
                });
            },
            'primary_action_label': __('Schieben'),
            'title': __("Alle Projekte nach hinten schieben")
        });
        d.show();
    },
    get_capacity: function(page, from, to) {
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.get_capacity',
            'args': {
                'from_date': document.getElementById("from").value,
                'to_date': document.getElementById("to").value
            },
            'callback': function(r) {
                console.log(r);
                frappe.msgprint(r.message, "Freie Kapazität");
            }
        });
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
           'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.reschedule_project",
           'args': {
                "project": ref_id,
                "team": team,
                "day": day,
                "start_half_day": start_half_day
           },
           'callback': function(response) {
                
           }
        });
    } else {
        frappe.call({
           'method': "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.reschedule_subcontracting",
           'args': {
                "subcontracting": ref_id,
                "team": team,
                "day": day
           },
           'callback': function(response) {
                
           }
        });
    }
}

function print_content(page, from, to) {
   
    frappe.dom.freeze('Bitte warten, das PDF wird erzeugt...');

    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.print_bohrplaner',
        'args': {
            'start_date': document.getElementById("from").value
        },
        'callback': function(r) {
            window.open(r.message.url, '_blank');
            
            frappe.dom.unfreeze();
        }
    });
}

function route_to_subproject(elmnt) {
    trigger = $(elmnt);
    frappe.route_options.from = trigger.attr('data-start');
    frappe.route_options.project_name = trigger.attr('data-subproject');
    cur_dialog.hide();
    frappe.bohrplaner.load_route(frappe.bohrplaner.page);
    
}
