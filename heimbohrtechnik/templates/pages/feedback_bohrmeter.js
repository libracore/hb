$(document).ready(function(){
    make();
    run();
});


function make() {
}

function run() {
    $(".btn-submit").on('click', function() { 
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.insert_feedback',
            'args': {
                'drilling_team': document.getElementById('drilling_team').value, 
                'drilling_meter': document.getElementById('drilling_meter').value, 
                'date': document.getElementById('date').value, 
                'project': document.getElementById('project').value, 
                'project2': document.getElementById('project2').value
            },
            'callback': function(r) {
            }
        });
    });
    // Autofill Drilling Team
    var drilling_team_prep = window.location.toString().split("=");
    var drilling_team_prep_2 = drilling_team_prep[1].split("&");
    var drilling_team = drilling_team_prep_2[0].replace(/%20/g, " ");
    document.getElementById('drilling_team').value = drilling_team;
    // Handle button visibillity
    // Validate key
    var link_prep = window.location.toString().split("=");
    var link_key = link_prep[link_prep.length -1]
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.check_key',
        'args': {
            'link_key': link_key,
            'team': drilling_team
        },
        'callback': function(response) {
            if (response.message) {
                var check = response.message
            } else {
                var check = false
            }
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
