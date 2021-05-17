frappe.pages['drill-planner'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Drill Planner'),
		single_column: true
	});
    
    // set full-width if not
    if (document.getElementsByTagName("body")[0].className != 'full-width') {
        frappe.ui.toolbar.toggle_full_width();
    }
    if (frappe.is_mobile()) {
        frappe.drill_planner.make_mobile(page);
    } else {
        frappe.drill_planner.make(page);
        frappe.drill_planner.run(page);
        
        // drag start
        document.addEventListener('dragstart', function(event) {
            event.dataTransfer.setData('Text', event.target.id);
            var drag_element = document.getElementById(event.target.id);
            drag_element.classList.add("hidden");
        });
    }
}

frappe.drill_planner = {
    make: function(page) {
        var me = frappe.drill_planner;
        me.page = page;
        
        me.header = $('<div class="row" id="header_row"></div>').appendTo(me.page.main);
        me.header_left = $('<div class="col-sm-2"></div>').appendTo(me.header);
        me.header_right = $('<div class="col-sm-10" id="drill_planner_header_element" style="overflow-x: scroll; overflow-y: scroll;"></div>').appendTo(me.header);
        
        me.body = $('<div class="row" id="body_row"></div>').appendTo(me.page.main);
        me.body_left = $('<div class="col-sm-2"></div>').appendTo(me.body);
        me.body_right = $('<div class="col-sm-10" id="drill_planner_main_element" style="overflow-x: scroll; overflow-y: scroll; position: relative; max-height: calc(100vH - 25vH);"></div>').appendTo(me.body);

        // set today as default "from" date
        var now = new Date();
        var from_date = frappe.datetime.add_days(now, 0);
        var to_date = frappe.datetime.add_days(now, 30);
        
        // render templates
        var data = frappe.drill_planner.get_content(page, from_date, to_date);
        $(frappe.render_template('drill_planner_header_left', {})).appendTo(me.header_left);
        $(frappe.render_template('drill_planner_header', data)).appendTo(me.header_right);
        $(frappe.render_template('drill_planner_left', data)).appendTo(me.body_left);
        $(frappe.render_template('drill_planner', data)).appendTo(me.body_right);
    },
    make_mobile: function(page) {
        var me = frappe.drill_planner;
        me.page = page;
        
        $(frappe.render_template('mobile_view', {})).appendTo(me.page.main);
    },
    run: function(page) {
		// set today as default "from" date
        var now = new Date();
        document.getElementById("from").value = frappe.datetime.add_days(now, 0);
        
        // set today + 30d as default "to" date
        document.getElementById("to").value = frappe.datetime.add_days(now, 30);
        
        // set trigger for date changes
        this.page.main.find("#from").on('change', function() {frappe.drill_planner.reload_data(page);});
        this.page.main.find("#to").on('change', function() {frappe.drill_planner.reload_data(page);});
        setTimeout(function(){ frappe.drill_planner.reload_data(page); }, 1);
    },
    reload_data: function(page) {
        var me = frappe.drill_planner;
        me.page = page;
        var from_date = document.getElementById("from").value;
        var to_date = document.getElementById("to").value;
        
        
        $('#header_row').remove();
        $('#body_row').remove();
        
        me.header = $('<div class="row" id="header_row"></div>').appendTo(me.page.main);
        me.header_left = $('<div class="col-sm-2"></div>').appendTo(me.header);
        me.header_right = $('<div class="col-sm-10" id="drill_planner_header_element" style="overflow-x: scroll; overflow-y: hidden;"></div>').appendTo(me.header);
        
        me.body = $('<div class="row" id="body_row"></div>').appendTo(me.page.main);
        me.body_left = $('<div class="col-sm-2" id="drill_planner_main_element_left" style="overflow-y: scroll; overflow-x: hidden; max-height: calc(100vH - 25vH);"></div>').appendTo(me.body);
        me.body_right = $('<div class="col-sm-10" id="drill_planner_main_element" style="overflow-x: hidden; overflow-y: hidden; position: relative; max-height: calc(100vH - 25vH);"></div>').appendTo(me.body);
        
        // render templates
        var data = frappe.drill_planner.get_content(page, from_date, to_date);
        $(frappe.render_template('drill_planner_header_left', {})).appendTo(me.header_left);
        $(frappe.render_template('drill_planner_header', data)).appendTo(me.header_right);
        $(frappe.render_template('drill_planner_left', data)).appendTo(me.body_left);
        $(frappe.render_template('drill_planner', data)).appendTo(me.body_right);
        
        // reset from and to date
        document.getElementById("from").value = from_date;
        document.getElementById("to").value = to_date;
        
        // set trigger for date changes
        this.page.main.find("#from").on('change', function() {frappe.drill_planner.reload_data(page);});
        this.page.main.find("#to").on('change', function() {frappe.drill_planner.reload_data(page);});
        
        frappe.drill_planner.add_overlay(data);
    },
    get_content: function(page, from_date, to_date) {
        var data;
        
        // get drilling teams
        frappe.call({
		   method: "heimbohrtechnik.heim_bohrtechnik.page.drill_planner.drill_planner.get_content",
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
                    total_width: content.total_width,
                    weekend: content.weekend,
                    kw_list: content.kw_list,
                    day_list: content.day_list,
                    today: content.today
                };
		   }
		});
        
        return data
    },
    add_overlay: function(data) {
        var added_list = [];
        var main_layout_element = document.getElementsByClassName("row layout-main")[0].getBoundingClientRect();
        var left_korrektur_faktor = (main_layout_element.left + 16) + $("#drill_planner_main_element_left").width();
        for (var i = 0; i<data.drilling_teams.length; i++) {
            for (var y = 0; y<Object.entries(data.drilling_teams[i].project_details).length; y++) {
                if (!added_list.includes(Object.entries(data.drilling_teams[i].project_details)[y][1].object)) {
                    added_list.push(Object.entries(data.drilling_teams[i].project_details)[y][1].object);
                    var search_element = document.getElementById(Object.entries(data.drilling_teams[i].project_details)[y][1].object);
                    if (search_element) {
                        var search_elementTextRectangle = search_element.getBoundingClientRect();
                        var project = Object.entries(data.drilling_teams[i].project_details)[y][1].object;
                        
                        var overlay = document.createElement("div");
                        overlay.id = 'dragObjecT-' + project;
                        
                        var selected_start = document.getElementById("from").value;
                        var selected_end = document.getElementById("to").value;
                        
                        frappe.call({
                            method: "heimbohrtechnik.heim_bohrtechnik.page.drill_planner.drill_planner.get_overlay_data",
                            args: {
                                "project": project,
                                "selected_start": selected_start,
                                "selected_end": selected_end
                            },
                            async: false,
                            callback: function(response) {
                                var ampel_indicators = response.message;
                                /*
                                 Ampeln:
                                 a1 = Baustelle besichtigt: rot/grün (Checkbox)
                                 a2 = Bewilligungen: von Untertabelle jede als Dokument (rot nichts, gelb einige, grün alle)
                                 a3 = Kundenauftrag: Rot fehlt, gelb auf Entwurf, grün gültig
                                 a4 = Materialstatus: rot fehlt/gelb bestellt (Lieferantenauftrag)/grün an Lager (Wareneingang)
                                 a5 = Kran benötigt? (grau nein, rot nicht geplant, grün organisiert)
                                 a6 = Bohrschlammentsorgung (rot: keiner, grün ein Schlammentsorger (Lieferant) im Objekt)
                                 a7 = Bohranzeige versendet (Checkbox auf Projekt)
                                */
                                var innerHTML =  '<div class="ampel-indicator hasTooltip" style="background-color: ' + ampel_indicators.a1.color + ';"></div><span style="display: none;">' + ampel_indicators.a1.tooltip + '</span>';
                                innerHTML = innerHTML + '<div class="ampel-indicator hasTooltip" style="background-color: ' + ampel_indicators.a2.color + ';"></div><span style="display: none;">' + ampel_indicators.a2.tooltip + '</span>';
                                innerHTML = innerHTML + '<div class="ampel-indicator hasTooltip" style="background-color: ' + ampel_indicators.a3.color + ';"></div><span style="display: none;">' + ampel_indicators.a3.tooltip + '</span>';
                                innerHTML = innerHTML + '<div class="ampel-indicator hasTooltip" style="background-color: ' + ampel_indicators.a7.color + ';"></div><span style="display: none;">' + ampel_indicators.a7.tooltip + '</span>';
                                innerHTML = innerHTML + '<div class="ampel-indicator hasTooltip" style="background-color: ' + ampel_indicators.a4.color + ';"></div><span style="display: none;">' + ampel_indicators.a4.tooltip + '</span>';
                                innerHTML = innerHTML + '<div class="ampel-indicator hasTooltip" style="background-color: ' + ampel_indicators.a5.color + ';"></div><span style="display: none;">' + ampel_indicators.a5.tooltip + '</span>';
                                innerHTML = innerHTML + '<div class="ampel-indicator hasTooltip" style="background-color: ' + ampel_indicators.a6.color + ';"></div><span style="display: none;">' + ampel_indicators.a6.tooltip + '</span>';
                                
                                innerHTML = innerHTML + '<i class="fa fa-info-circle pointer hasTooltip" style="margin-left: 5px; font-size: 20px; margin-top: 2px;" onclick="frappe.drill_planner.show_detail_popup(' + "'" + project + "'" + ');"></i><span style="display: none;">' + __("Click me for more informations") + '</span><br>';
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].object + " (" + ampel_indicators.manager + ")" + "<br>";
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].object_name + "<br>";
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].object_location + "<br>";
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].ews_details;
                                overlay.innerHTML = innerHTML;
                                
                                if (
                                    ampel_indicators.a1.color == 'green' &&
                                    ampel_indicators.a2.color == 'green' &&
                                    ampel_indicators.a3.color == 'green' &&
                                    ampel_indicators.a7.color == 'green' &&
                                    ampel_indicators.a4.color == 'green' &&
                                    (ampel_indicators.a5.color == 'green'||ampel_indicators.a5.color == 'grey') &&
                                    ampel_indicators.a6.color == 'green'
                                ) {
                                    overlay.style.backgroundColor  = '#eefdec';
                                } else if (
                                    ampel_indicators.a1.color == 'green' &&
                                    ampel_indicators.a2.color == 'green' &&
                                    ampel_indicators.a3.color == 'green' &&
                                    ampel_indicators.a7.color == 'green'
                                ) {
                                    overlay.style.backgroundColor  = '#ffffbf';
                                } else {
                                    overlay.style.backgroundColor  = '#ffeae9';
                                }
                                overlay.style.color  = 'black';
                                overlay.style.height = String((search_elementTextRectangle.height + 2)) + 'px';
                                overlay.style.position = 'absolute';
                                
                                var pos_left = search_elementTextRectangle.left;
                                var pos_top = search_elementTextRectangle.top;

                                overlay.style.left = String(pos_left - left_korrektur_faktor) + 'px';
                                overlay.style.top = String(pos_top - 244) + 'px';
                                
                                overlay.style.minWidth = String(ampel_indicators.total_overlay_width) + "px";
                                overlay.setAttribute('draggable', true);

                                var drill_planner_div = document.getElementById("drill_planner_main_element");

                                drill_planner_div.appendChild(overlay);
                            }
                        });
                    }
                }
            }
            $('.hasTooltip').hover(function() {
                $(this).next('span').addClass('showTooltip');
            }, function() {
                $(this).next('span').removeClass('showTooltip');
            });
        }
        
        // Scroll controlling
        $("#drill_planner_main_element").on('scroll', function(e) { 
            var ele = $(e.currentTarget);
            var left = ele.scrollLeft();
            $("#drill_planner_header_element").scrollLeft(left);
            var top = ele.scrollTop();
            $("#drill_planner_main_element_left").scrollTop(top);
        });
        $("#drill_planner_main_element_left").on('scroll', function(e) { 
            var ele = $(e.currentTarget);
            var top = ele.scrollTop();
            $("#drill_planner_main_element").scrollTop(top);
        });
        $("#drill_planner_header_element").on('scroll', function(e) { 
            var ele = $(e.currentTarget);
            var left = ele.scrollLeft();
            $("#drill_planner_main_element").scrollLeft(left);
        });
    },
    show_detail_popup: function(_project) {
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
                                var customer = __('No Customer found');
                                var customer_name = '';
                                if (project.customer) {
                                    customer = '<a href="/desk#Form/Customer/' + project.customer + '" target="_blank">' + project.customer + '</a>';
                                    customer_name = "(" + project.customer_name + ")";
                                }
                                
                                var object_link = '<a href="/desk#Form/Object/' + object.name + '" target="_blank">' + project.object_name + '</a>';
                                
                                var mud_disposer = __('No Mud Disposer found');
                                var mud_disposer_name = '';
                                if (object.mud_disposer) {
                                    frappe.call({
                                        "method": "frappe.client.get",
                                        "args": {
                                            "doctype": "Supplier",
                                            "name": object.mud_disposer
                                        },
                                        "async": false,
                                        "callback": function(_supplier) {
                                            if (_supplier.message) {
                                                var supplier = _supplier.message;
                                                mud_disposer_name = "(" + supplier.supplier_name + ")";
                                            }
                                        }
                                    });
                                    mud_disposer = '<a href="/desk#Form/Mud Disposer/' + object.mud_disposer + '" target="_blank">' + object.mud_disposer + '</a>';
                                }
                                
                                var drilling_equipment = __('No Drilling Equipment found');
                                if (object.drilling_equipment) {
                                    drilling_equipment = '<a href="/desk#Form/Drilling Equipment/' + object.drilling_equipment + '" target="_blank">' + object.drilling_equipment + '</a>';
                                }
                                
                                var manager = __('No Manager found');
                                if (object.manager) {
                                    manager = '<a href="/desk#Form/User/' + object.manager + '" target="_blank">' + object.manager + '</a>';
                                }
                                
                                var html = '<table style="width: 100%;">';
                                html = html + '<tr><td><b>' + __('Project') + '</b></td>';
                                html = html + '<td>' + '<a href="/desk#Form/Project/' + project.name + '" target="_blank">' + project.name + '</a></td></tr>';
                                html = html + '<tr><td><b>' + __('Customer') + '</b></td>';
                                html = html + '<td>' + customer + ' ' + customer_name + '</td></tr>';
                                html = html + '<tr><td><b>' + __('Object') + '</b></td>';
                                html = html + '<td>' + object_link + '</td></tr>';
                                html = html + '<tr><td><b>' + __('Location') + '</b></td>';
                                html = html + '<td>' + project.object_location + '</td></tr>';
                                html = html + '<tr><td><b>' + __('EWS Details') + '</b></td>';
                                html = html + '<td>' + project.ews_details + '</td></tr>';
                                html = html + '<tr><td><b>' + __('Mud Disposer') + '</b></td>';
                                html = html + '<td>' + mud_disposer + ' ' + mud_disposer_name +'</td></tr>';
                                html = html + '<tr><td><b>' + __('Drilling Equipment') + '</b></td>';
                                html = html + '<td>' + drilling_equipment + '</td></tr>';
                                html = html + '<tr><td><b>' + __('Manager') + '</b></td>';
                                html = html + '<td>' + manager + '</td></tr>';
                                html = html + '<tr><td><b>' + __('Status') + '</b></td>';
                                html = html + '<td>Status - Details...</td></tr>';
                                
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
                                           method: "heimbohrtechnik.heim_bohrtechnik.page.drill_planner.drill_planner.reschedule_project",
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
                                                frappe.drill_planner.reload_data(frappe.drill_planner.page);
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
    allow_drop: function(ev) {
        ev.preventDefault();
        var to_get_droped = $("[data-dropid='" + ev.target.dataset.dropid + "']")[0];
        to_get_droped.classList.add("ondragover");
    },
    drag_leave: function(ev) {
        ev.preventDefault();
        var leaved = $("[data-dropid='" + ev.target.dataset.dropid + "']")[0];
        leaved.classList.remove("ondragover");
    },
    drop: function(ev) {
        ev.preventDefault();
        var data = ev.dataTransfer.getData("text");
        var to_drop = document.getElementById(data);
        to_drop.style.position = "unset";
        ev.target.appendChild(to_drop);
        
        // reschedule_project
        frappe.call({
		   method: "heimbohrtechnik.heim_bohrtechnik.page.drill_planner.drill_planner.reschedule_project",
		   args: {
				"project": data.replace("dragObjecT-", ""),
				"team": ev.target.dataset.team,
                "day": ev.target.dataset.day,
                "start_half_day": ev.target.dataset.start
		   },
           async: false,
		   callback: function(response) {
				frappe.drill_planner.reload_data(frappe.drill_planner.page);
		   }
		});
    }
}
