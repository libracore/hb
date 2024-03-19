$(document).ready(function(){
    make();
    run();
});

function make() {
    // get options for deputys
    get_deputys();
}

function run() {
    //get all arguments and safe it in the HTML File
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
        if (args['drilling_team']) {
            document.getElementById('drilling_team').value = args['drilling_team'].replace(/%20/g, " ").replace(/%C3%BC/g, "ü").replace(/%C3%B6/g, "ö").replace(/%C3%A4/g, "ä");
        }
        if (args['key']) {
            document.getElementById('key').value = args['key'];
        }        
    } else {
        // no arguments provided
        
    }
    // Check if key in link is valid
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.check_key',
        'args': {
            'link_key': document.getElementById('key').value,
            'team': document.getElementById('drilling_team').value
        },
        'callback': function(response) {
            var check = false;
            document.getElementById('check_memory').value = check;
            if (response.message) {
                check = response.message.is_valid;
                document.getElementById('check_memory').value = check;
                var projects_html = response.message.projects_html;
            }
            //Set Projects as Options for Select Field
            var project_icon = document.getElementById('project_icon');
                project_icon.addEventListener('click', function() {
                    var field = 'project';
                    chose_project(projects_html, field);
                });
            var project_icon2 = document.getElementById('project_icon2');
                project_icon2.addEventListener('click', function() {
                    var field = 'project2';
                    chose_project(projects_html, field);
                });
            //Check if all mandatory fields are filled
            var input = document.getElementById('form');
            input.addEventListener('input', function() {
                handle_button_visibillity(check);
            });
        }
    });
    //calculate total drilling meters
    var total_drilling_meter = document.getElementById('drilling_meter');
    var project_meter = document.getElementById('project_meter');
    var project_meter2 = document.getElementById('project_meter2');
    project_meter.addEventListener('input', function() {
        calculate_total_meter();
    });
    project_meter2.addEventListener('input', function() {
        calculate_total_meter();
    });
    //create document in ERPNext, when submit button has been pushed
    $(".btn-submit").on('click', function() {
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.insert_feedback',
            'args': {
                'drilling_team': document.getElementById('drilling_team').value, 
                'drilling_meter': document.getElementById('drilling_meter').value, 
                'date': document.getElementById('date').value, 
                'project': document.getElementById('project').value, 
                'project2': document.getElementById('project2').value,
                'flushing': document.getElementById('flushing').value,
                'hammer_change': document.getElementById('hammer_change').value,
                'impact_part_change': document.getElementById('impact_part_change').value,
                'link_key': document.getElementById('key').value = args['key']
            },
            'callback': function(r) {
                frappe.msgprint("<b>Daten erfolgreich übermittelt!</b>", "Info");
            }
        });
    });
}

function chose_project(projects_html, field) {
    document.getElementById('field_memory').value = field;
    var message = frappe.msgprint(projects_html, "Projekt wählen");
}

function set_project(self, choice) {
    var field = document.getElementById('field_memory').value;
    var check = document.getElementById('check_memory').value;
    document.getElementById(field).value = choice;
    handle_button_visibillity(check);
    frappe.ui.open_dialogs[0].hide();
}
function handle_button_visibillity(check) {
    if (check == "true") {
        check = true;
    }
    var button = document.getElementById('submit');
    var meter = document.getElementById('drilling_meter').value
    var date = document.getElementById('date').value
    var project = document.getElementById('project').value
    //Display button
    if (meter !== '' && date !== '' && project !== '' && check == true) {
        button.style.display = 'block';
    } else {
        button.style.display = 'none';
    }
}

function get_deputys() {
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.get_deputy_list',
        'callback': function(r) {
            var deputys = r.message
            var deputySelect = document.getElementById('deputy');
            deputys.forEach(function(option) {
                var deputyElement = document.createElement('option');
                deputyElement.text = option;
                deputySelect.add(deputyElement);
            });
        }
    });
}

function calculate_total_meter() {
    var meter = parseInt(document.getElementById('project_meter').value)
    if (isNaN(meter)) {
        meter = 0;
    }
    var meter2 = parseInt(document.getElementById('project_meter2').value)
    if (isNaN(meter2)) {
        meter2 = 0;
    }
    document.getElementById('drilling_meter').value = meter + meter2;
}
