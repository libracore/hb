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
        me.body = $('<div id="drill_planner_main_element" style="overflow: auto; position: relative;"></div>').appendTo(me.page.main);

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
        me.body = $('<div id="drill_planner_main_element" style="overflow: auto; position: relative;"></div>').appendTo(me.page.main);
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
                    total_width: content.total_width
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
                        var innerHTML = '<span class="indicator green"></span>';
                        innerHTML = innerHTML + '<span class="indicator red"></span>';
                        innerHTML = innerHTML + '<span class="indicator yellow"></span>';
                        innerHTML = innerHTML + '<span class="indicator green"></span>';
                        innerHTML = innerHTML + '<span class="indicator grey"></span>';
                        innerHTML = innerHTML + '<span class="indicator red"></span>';
                        innerHTML = innerHTML + '<span class="indicator green"></span>';
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
                        
                        var left_korrektur_faktor = parseInt($(".container.page-body").css("marginLeft"));
                        var pos_left = search_elementTextRectangle.left;
                        var pos_top = search_elementTextRectangle.top;
                        
                        overlay.style.left = String(pos_left - left_korrektur_faktor) + 'px';
                        overlay.style.top = String(pos_top - 111) + 'px';
                        overlay.style.minWidth = '160px';
                        
                        overlay.setAttribute('draggable', true);
                        
                        var drill_planner_div = document.getElementById("drill_planner_main_element");
                        
                        drill_planner_div.appendChild(overlay);
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
                    var html = project.name + "<br>";
                    html = html + "Auftraggeber...<br>";
                    html = html + project.object_name + "<br>";
                    html = html + project.object_location + "<br>";
                    html = html + project.ews_details + "<br>";
                    html = html + "Schlammentsorger...<br>";
                    html = html + "Typ Borhgerät...<br>";
                    html = html + "Bauleiter...<br>";
                    html = html + "Status - Details...<br>";
                    frappe.msgprint(html, __("Details"));
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
    }
}
