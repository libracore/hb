$('document').ready(function(){
    make();
});


function make() {
    var planning_days = 30;
    
    // fetch command line arguments
    get_command_line_arguments();
    
    // set today as default "from" date
    var now = new Date();
    locals.from_date = now;
    locals.to_date = add_days(now, planning_days);

    // fetch date range from open projects
    frappe.call({
       'method': "heimbohrtechnik.templates.pages.bohrplan.get_last_date",
       'args': {
            'customer': locals.customer,
            'drilling_team': locals.drilling_team,
            'key': locals.key
       },
       'async': false,
       'callback': function(response) {
            if (response.message) {
                locals.to_date = new Date(response.message);
            }
            // get grid
            frappe.call({
               'method': "heimbohrtechnik.templates.pages.bohrplan.get_grid",
               'args': {
                    'from_date': locals.from_date,
                    'to_date': locals.to_date,
                    'drilling_team': locals.drilling_team
               },
               'async': false,
               'callback': function(response) {
                    var content = response.message;
                    data = {
                        'drilling_teams': content.drilling_teams,
                        'days': content.days,
                        'weekend': content.weekend,
                        'kw_list': content.kw_list,
                        'day_list': content.day_list,
                        'today': content.today,
                        'print_view': false,
                        'web_view': true
                    };
                    
                    $(frappe.render_template(frappe.templates.calendar_grid, data)).appendTo($("#page-bohrplan"));
                    
                    run(locals.from_date, locals.to_date);
               }
            });
       }
    });
}

function run(from_date, to_date) {
    frappe.call({
       method: "heimbohrtechnik.templates.pages.bohrplan.get_data",
       args: {
            "from_date": from_date,
            "to_date": to_date,
            "customer": locals.customer,
            "key": locals.key,
            "drilling_team": locals.drilling_team
       },
       async: false,
       callback: function(response) {
            var contents = response.message;
            console.log(contents);
            for (var i = 0; i < contents.length; i++) {
                var data = contents[i];
                if (locals.customer) {
                    add_overlay(data);
                } else {
                    add_subproject_overlay(data);
                }
            }
       }
    });
}

function add_days(date, days) {
    var result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function add_overlay(data) {
    var place = $('[data-bohrteam="' + data.bohrteam + '"][data-date="' + data.start + '"][data-vmnm="' + data.vmnm + '"]');
    $(place).css("position", "relative");
    var qty = data.dauer
    var width = 46.77 * qty;
    $(frappe.render_template(frappe.templates.booking_overlay, {
        'width': width, 
        'project': data.project, 
        'saugauftrag': data.saugauftrag, 
        'pneukran': data.pneukran, 
        'manager_short': data.manager_short, 
        'drilling_equipment': data.drilling_equipment, 
        'ampeln': data.ampeln,
        'dragable': 'false',
        'box_height': 13,
        'padding': 0,
        'font_size': 7,
        'min_width': 35,
        'max_width': 70,
        'ews_details': data.ews_details,
        'traffic_light': data.traffic_light
    })).appendTo(place);
    return
}

function add_subproject_overlay(data) {
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
        'dragable': "false",
        'multi_day': (data.dauer > 2) ? "multi_day" : "single_day",
        'background': data.background
    })).appendTo(place);
    return
}
    
function get_command_line_arguments() {
    // get command line parameters
    var arguments = window.location.toString().split("?");
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
            locals.customer = args['customer'];
        }
        if (args['key']) {
            locals.key = args['key'];
        }
        if (args['drilling_team']) {
            locals.drilling_team = decodeURI(args['drilling_team']);
        }
        
    } else {
        // no arguments provided
        
    }
}
