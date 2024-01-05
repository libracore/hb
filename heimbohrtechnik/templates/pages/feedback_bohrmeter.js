$(document).ready(function(){
    make();
    run();
});


function make() {
}

function run() {
    //Create Document on submit
    $(".btn-submit").on('click', function() {
        var link_key = get_link_key()
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.insert_feedback',
            'args': {
                'drilling_team': document.getElementById('drilling_team').value, 
                'drilling_meter': document.getElementById('drilling_meter').value, 
                'date': document.getElementById('date').value, 
                'project': document.getElementById('project').value, 
                'project2': document.getElementById('project2').value,
                'link_key': link_key
            },
            'callback': function(r) {
            }
        });
    });
    // Autofill Drilling Team
    var drilling_team_prep = window.location.toString().split("=");
    var drilling_team_prep_2 = drilling_team_prep[1].split("&");
    var drilling_team = drilling_team_prep_2[0].replace(/%20/g, " ").replace(/%C3%BC/g, "ü").replace(/%C3%B6/g, "ö").replace(/%C3%A4/g, "ä");
    document.getElementById('drilling_team').value = drilling_team;
    // Handle button visibillity
    // Validate key
    var link_key = get_link_key()
    //~ var link_prep = window.location.toString().split("=");
    //~ var link_key = link_prep[link_prep.length -1]
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.check_key',
        'args': {
            'link_key': link_key,
            'team': drilling_team
        },
        'callback': function(response) {
            if (response.message) {
                console.log(response.message);
                var check = response.message[0]
                var projects = response.message[1]
                console.log(check);
                console.log(projects);
            } else {
                var check = false
            }
            //Set Projects as Options for Select Field
            var project_icon = document.getElementById('project_icon');
                project_icon.addEventListener('click', function() {
                    chose_project(projects);
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
}

function get_link_key() {
    var link_prep = window.location.toString().split("=");
    var link_key = link_prep[link_prep.length -1]
    return link_key
}

function chose_project(projects) {
    console.log("hoi");
    //~ html = document.getElementById('msgprint')
    //~ frappe.msgprint(frappe.render_template('heimbohrtechnik/templates/pages/msgprint.html'), "Projekt wählen");
}
