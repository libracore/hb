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
}

frappe.drill_planner = {
    make: function(page) {
        var me = frappe.drill_planner;
        me.page = page;
        me.body = $('<div id="drill_planner_main_element" style="overflow: auto;"></div>').appendTo(me.page.main);
        //me.body = $('<div></div>').appendTo(me.page.main);
        // set today as default "from" date
        var now = new Date();
        var from_date = frappe.datetime.add_days(now, 0);
        var to_date = frappe.datetime.add_days(now, 30);
        var data = frappe.drill_planner.get_content(page, from_date, to_date);
        $(frappe.render_template('drill_planner', data)).appendTo(me.body);
        
        // set trigger for date changes
        this.page.main.find("#from").on('change', function() {frappe.drill_planner.reload_data(page);});
        this.page.main.find("#to").on('change', function() {frappe.drill_planner.reload_data(page);});
    },
    run: function(page) {
		// set today as default "from" date
        var now = new Date();
        document.getElementById("from").value = frappe.datetime.add_days(now, 0);
        
        // set today + 30d as default "to" date
        document.getElementById("to").value = frappe.datetime.add_days(now, 30);
    },
    reload_data: function(page) {
        var me = frappe.drill_planner;
        me.page = page;
        var from_date = document.getElementById("from").value;
        var to_date = document.getElementById("to").value;
        
        // remove old data
        $('#drill_planner_main_element').remove();
        
        // create new content
        me.body = $('<div id="drill_planner_main_element" style="overflow: auto;"></div>').appendTo(me.page.main);
        var data = frappe.drill_planner.get_content(page, from_date, to_date);
        $(frappe.render_template('drill_planner', data)).appendTo(me.body);
        
        // reset from and to date
        document.getElementById("from").value = from_date;
        document.getElementById("to").value = to_date;
        
        // set trigger for date changes
        this.page.main.find("#from").on('change', function() {frappe.drill_planner.reload_data(page);});
        this.page.main.find("#to").on('change', function() {frappe.drill_planner.reload_data(page);});
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
    }
}