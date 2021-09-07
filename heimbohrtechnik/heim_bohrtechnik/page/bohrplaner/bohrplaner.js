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
    if (frappe.is_mobile()) {
        frappe.bohrplaner.make_mobile(page);
    } else {
        // create page
        frappe.bohrplaner.make(page);
        // run page
        frappe.bohrplaner.run(page);
    }
}

frappe.bohrplaner = {
    make: function(page) {
        var me = frappe.bohrplaner;
        me.page = page;
        
        // set today as default "from" date
        var now = new Date();
        var from_date = frappe.datetime.add_days(now, 0);
        var to_date = frappe.datetime.add_days(now, 30);
        
        //get template data
        var data = frappe.bohrplaner.get_content(page, from_date, to_date);
        
        // render calendar grid
        $(frappe.render_template('calendar_grid', data)).appendTo(me.page.body);
    },
    run: function(page) {
		// set today as default "from" date
        var now = new Date();
        document.getElementById("from").value = frappe.datetime.add_days(now, 0);
        
        // set today + 30d as default "to" date
        document.getElementById("to").value = frappe.datetime.add_days(now, 30);
        
        // set trigger for date changes
        this.page.main.find("#from").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        this.page.main.find("#to").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        
        // get/add overlays
        frappe.bohrplaner.get_overlay_data(page);
        
        
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
                
		   }
		});
    },
    add_overlay: function(page, data) {
        var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="' + data.vmnm + '"]');
        $(place).css("position", "relative");
        var qty = data.dauer
        var width = 42 * qty;
        $(frappe.render_template('booking_overlay', {'width': width, 'object': data.object, 'project': data.name, 'ampeln': data.ampeln})).appendTo(place);
        return
    },
    reset_dates: function(page) {
        // pre safe new dates
        var from = $("#from").val();
        var to = $("#to").val();
        // remove old grid
        $("#bohrplan_wrapper").remove();
        //get template data
        var data = frappe.bohrplaner.get_content(page, from, to);
        // render calendar grid
        $(frappe.render_template('calendar_grid', data)).appendTo(page.body);
        // set safed dates
        document.getElementById("from").value = from;
        document.getElementById("to").value = to;
        // reset triggers
        this.page.main.find("#from").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        this.page.main.find("#to").on('change', function() {frappe.bohrplaner.reset_dates(page);});
        // get/add overlays
        frappe.bohrplaner.get_overlay_data(page);
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
    }
}

function allowDrop(ev) {
    ev.preventDefault();
    var to_get_droped = $("[data-dropid='" + ev.target.dataset.dropid + "']")[0];
    to_get_droped.classList.add("ondragover");
}

function dragLeave(ev) {
    ev.preventDefault();
    var leaved = $("[data-dropid='" + ev.target.dataset.dropid + "']")[0];
    leaved.classList.remove("ondragover");
}

function drag(ev) {
    ev.dataTransfer.setData('text', ev.target.id);
    var drag_element = document.getElementById(event.target.id);
    drag_element.classList.add("hidden");
}

function drop(ev) {
    ev.preventDefault();
    var data = ev.dataTransfer.getData('text');
    $("[data-dropid='" + ev.target.dataset.dropid + "']").css("position", "relative");
    var dropped_element = document.getElementById(data);
    ev.target.appendChild(dropped_element);
    dropped_element.classList.remove("hidden");
    $("[data-dropid='" + ev.target.dataset.dropid + "']").removeClass("ondragover");
    reshedule(data, $(ev.target).attr("data-bohrteam"), $(ev.target).attr("data-date"), $(ev.target).attr("data-vmnm"))
}

function reshedule(project, team, day, start_half_day) {
    frappe.call({
       method: "heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.reschedule_project",
       args: {
            "project": project,
            "team": team,
            "day": day,
            "start_half_day": start_half_day
       },
       callback: function(response) {
            
       }
    });
}
