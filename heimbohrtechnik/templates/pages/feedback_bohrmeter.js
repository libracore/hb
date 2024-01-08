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
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.check_key',
        'args': {
            'link_key': document.getElementById('key').value,
            'team': document.getElementById('drilling_team').value
        },
        'callback': function(response) {
            if (response.message) {
                console.log(response.message);
                var check = response.message[0]
                var projects_html = response.message[1]
                console.log(check);
                console.log(projects_html);
            } else {
                var check = false
            }
            //Set Projects as Options for Select Field
            var project_icon = document.getElementById('project_icon');
                project_icon.addEventListener('click', function() {
                    chose_project(projects_html);
                });
            //Check if all mandatory fields are filled
            var input = document.getElementById('form')
            var button = document.getElementById('submit')
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
    $(".btn-submit").on('click', function() {
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.insert_feedback',
            'args': {
                'drilling_team': document.getElementById('drilling_team').value, 
                'drilling_meter': document.getElementById('drilling_meter').value, 
                'date': document.getElementById('date').value, 
                'project': document.getElementById('project').value, 
                'project2': document.getElementById('project2').value,
                'link_key': document.getElementById('key').value = args['key']
            },
            'callback': function(r) {
            }
        });
    });
}

function chose_project(projects_html) {
    console.log("hoi");
    var message = frappe.msgprint(projects_html, "Projekt wählen");
}

function show_based_on_filter(self, choice) {
    console.log(choice);
    document.getElementById('project').value = choice;
    var msgprintElement = message.wrapper[0];
    if (msgprintElement) {
        msgprintElement.style.display = 'none';
    }
    //var modal = document.getElementByClassName('modal')//.classList.remove("show");
    //~ var modal_backdrop =  document.getElementsByClassName('modal-backdrop');
    //~ console.log(modal_backdrop)
    //~ if (modal_backdrop) {
        //~ modal_backdrop.classList.remove("show");
    //~ }
}
