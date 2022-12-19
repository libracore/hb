$('document').ready(function(){
    make();
    //~ run();
    //~ console.log(frappe.render_template(frappe.templates.calendar_grid, {}))
});


function make() {
    var planning_days = 30;
       
    // set today as default "from" date
    var now = new Date();
    locals.from_date = now;
    locals.to_date = add_days(now, planning_days);
    
    //get template data
    //~ var data = get_grid(locals.from_date, locals.to_date);
    
    frappe.call({
       method: "heimbohrtechnik.templates.pages.bohrplan.get_grid",
       args: {
            "from_date": locals.from_date,
            "to_date": locals.to_date
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
                today: content.today,
                print_view: false
            };
            
            $(frappe.render_template(frappe.templates.calendar_grid, data)).appendTo($("#page-bohrplan"));
            
            run(locals.from_date, locals.to_date);
       }
    });
    
    //~ console.log(data);
    // render calendar grid
    //document.getElementById("grid").innerHTML = frappe.render_template('heimbohrtechnik/heim_bohrtechnik/page/bohrplaner/calendar_grid.html', data);
    //~ console.log(frappe.render_template(frappe.templates.calendar_grid, data))
    //console.log(frappe.render_template("/assets/heimbohrtechnik/calendar_grid.html", data))
}

function run(from_date, to_date) {
    // get command line parameters
    var arguments = window.location.toString().split("?");
    var customer = null;
    var key = null;
    if (!arguments[arguments.length - 1].startsWith("http")) {
        var args_raw = arguments[arguments.length - 1].split("&");
        var args = {};
        args_raw.forEach(function (arg) {
            var kv = arg.split("=");
            if (kv.length > 1) {
                args[kv[0]] = kv[1];
            }
        });
        if (args['customer']) {
            customer = args['customer'];
        }
        if (args['key']) {
            key = args['key'];
        }
        
    } else {
        // no arguments provided
        
    }
    
    //~ var data = get_data(from_date, to_date, customer, key);
    frappe.call({
       method: "heimbohrtechnik.templates.pages.bohrplan.get_data",
       args: {
            "from_date": from_date,
            "to_date": to_date,
            "customer": customer,
            "key": key
       },
       async: false,
       callback: function(response) {
            var contents = response.message;
            console.log(contents)
            for (var i = 0; i < contents.length; i++) {
                var data = contents[i];
                add_overlay(data);
            }
       }
    });
}

//~ function get_grid(from_date, to_date) {
    //~ var data;
    
    //~ // get drilling teams
    //~ frappe.call({
       //~ method: "heimbohrtechnik.templates.pages.bohrplan.get_grid",
       //~ args: {
            //~ "from_date": from_date,
            //~ "to_date": to_date
       //~ },
       //~ async: false,
       //~ callback: function(response) {
            //~ var content = response.message;
            //~ data = {
                //~ drilling_teams: content.drilling_teams,
                //~ days: content.days,
                //~ weekend: content.weekend,
                //~ kw_list: content.kw_list,
                //~ day_list: content.day_list,
                //~ today: content.today
            //~ };
       //~ }
    //~ });
    
    //~ return data
//~ }

//~ function get_data(from_date, to_date, customer, key) {
    //~ frappe.call({
       //~ method: "heimbohrtechnik.templates.pages.bohrplan.get_data",
       //~ args: {
            //~ "from_date": from_date,
            //~ "to_date": to_date,
            //~ "customer": customer,
            //~ "key": key
       //~ },
       //~ async: false,
       //~ callback: function(response) {
            //~ var contents = response.message;
            //~ for (var i = 0; i < contents.length; i++) {
                //~ var data = contents[i];
                //~ add_overlay(page, data);
            //~ }
       //~ }
    //~ });

//~ }

function add_days(date, days) {
    var result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function add_overlay(data) {
    var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="' + data.vmnm + '"]');
    $(place).css("position", "relative");
    var qty = data.dauer
    var width = 42 * qty;
    //~ $(frappe.render_template('heimbohrtechnik/heim_bohrtechnik/page/bohrplaner/booking_overlay.html', {
        //~ 'width': width, 
        //~ 'project': data.project, 
        //~ 'saugauftrag': data.saugauftrag, 
        //~ 'pneukran': data.pneukran, 
        //~ 'manager_short': data.manager_short, 
        //~ 'drilling_equipment': data.drilling_equipment, 
        //~ 'ampeln': data.ampeln
    //~ })).appendTo(place);
    $(frappe.render_template(frappe.templates.booking_overlay, {
        'width': width, 
        'project': data.project, 
        'saugauftrag': data.saugauftrag, 
        'pneukran': data.pneukran, 
        'manager_short': data.manager_short, 
        'drilling_equipment': data.drilling_equipment, 
        'ampeln': data.ampeln
    })).appendTo(place);
    return
}
