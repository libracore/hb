$(document).ready(function(){
    make();
    run();
});

function make() {
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
            if (response.message) {
                check = response.message.is_valid;
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
            var button = document.getElementById('submit');
            input.addEventListener('input', function() {
                var meter = document.getElementById('drilling_meter').value
                var date = document.getElementById('date').value
                var project = document.getElementById('project').value
                //Display button
                if (meter !== '' && date !== '' && project !== '' && check == true) {
                    button.style.display = 'block';
                } else {
                    button.style.display = 'none';
                }
            });
        }
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
    document.getElementById(field).value = choice;
    frappe.ui.open_dialogs[0].hide();
}
