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
    
    frappe.drill_planner.make(page);
	frappe.drill_planner.run(page);
    setTimeout(function(){ frappe.drill_planner.reload_data(page); }, 1);
    
    // drag start
    document.addEventListener('dragstart', function(event) {
        event.dataTransfer.setData('Text', event.target.id);
        document.getElementById(event.target.id).style.backgroundColor = 'green';
    });
}

frappe.drill_planner = {
    make: function(page) {
        var me = frappe.drill_planner;
        me.page = page;
        me.body = $('<div id="drill_planner_main_element" style="overflow: auto; position: relative; max-height: calc(100vH - 15vH);"></div>').appendTo(me.page.main);

        // set today as default "from" date
        var now = new Date();
        var from_date = frappe.datetime.add_days(now, 0);
        var to_date = frappe.datetime.add_days(now, 30);
        var data = frappe.drill_planner.get_content(page, from_date, to_date);
        $(frappe.render_template('drill_planner', data)).appendTo(me.body);
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
    },
    reload_data: function(page) {
        var me = frappe.drill_planner;
        me.page = page;
        var from_date = document.getElementById("from").value;
        var to_date = document.getElementById("to").value;
        
        // remove old data
        $('#drill_planner_main_element').remove();
        
        // create new content
        me.body = $('<div id="drill_planner_main_element" style="overflow: auto; position: relative; max-height: calc(100vH - 15vH);"></div>').appendTo(me.page.main);
        var data = frappe.drill_planner.get_content(page, from_date, to_date);
        $(frappe.render_template('drill_planner', data)).appendTo(me.body);
        
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
                    weekend: content.weekend
                };
		   }
		});
        
        return data
    },
    add_overlay: function(data) {
        var added_list = [];
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
                        
                        frappe.call({
                            method: "heimbohrtechnik.heim_bohrtechnik.page.drill_planner.drill_planner.get_traffic_lights",
                            args: {
                                "project": project
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
                                var innerHTML = '<span class="indicator ' + ampel_indicators.a1 + '"></span>';
                                innerHTML = innerHTML + '<span class="indicator ' + ampel_indicators.a2 + '"></span>';
                                innerHTML = innerHTML + '<span class="indicator ' + ampel_indicators.a3 + '"></span>';
                                innerHTML = innerHTML + '<span class="indicator ' + ampel_indicators.a4 + '"></span>';
                                innerHTML = innerHTML + '<span class="indicator ' + ampel_indicators.a5 + '"></span>';
                                innerHTML = innerHTML + '<span class="indicator ' + ampel_indicators.a6 + '"></span>';
                                innerHTML = innerHTML + '<span class="indicator ' + ampel_indicators.a7 + '"></span>';
                                innerHTML = innerHTML + '<i class="fa fa-info-circle pointer" onclick="frappe.drill_planner.show_detail_popup(' + "'" + project + "'" + ');"></i><br>';
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].object + "<br>";
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].object_name + "<br>";
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].object_location + "<br>";
                                innerHTML = innerHTML + Object.entries(data.drilling_teams[i].project_details)[y][1].ews_details;
                                overlay.innerHTML = innerHTML;

                                overlay.style.backgroundColor  = 'transparent';
                                overlay.style.color  = 'white';
                                overlay.style.height = String(search_elementTextRectangle.height) + 'px';
                                overlay.style.position = 'absolute';

                                var left_korrektur_faktor = parseInt($(".container.page-body").css("marginLeft")) + 15;
                                var pos_left = search_elementTextRectangle.left;
                                var pos_top = search_elementTextRectangle.top;

                                overlay.style.left = String(pos_left - left_korrektur_faktor) + 'px';
                                overlay.style.top = String(pos_top - 111) + 'px';
                                overlay.style.minWidth = '160px';

                                overlay.setAttribute('draggable', true);

                                var drill_planner_div = document.getElementById("drill_planner_main_element");

                                drill_planner_div.appendChild(overlay);
                            }
                        });
                    }
                }
            }
        }
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
                                if (project.customer) {
                                    customer = '<a href="/desk#Form/Customer/' + project.customer + '" target="_blank">' + project.customer + '</a>';
                                }
                                
                                var object_link = '<a href="/desk#Form/Object/' + object.name + '" target="_blank">' + project.object_name + '</a>';
                                
                                var mud_disposer = __('No Mud Disposer found');
                                if (object.mud_disposer) {
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
                                
                                var html = '<a href="/desk#Form/Project/' + project.name + '" target="_blank">' + project.name + "</a><br>";
                                html = html + customer + "<br>";
                                html = html + object_link + "<br>";
                                html = html + project.object_location + "<br>";
                                html = html + project.ews_details + "<br>";
                                html = html + mud_disposer + "<br>";
                                html = html + drilling_equipment + "<br>";
                                html = html + manager + "<br>";
                                html = html + "Status - Details...<br>";
                                frappe.msgprint(html, __("Details"));
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
