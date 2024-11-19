$(document).ready(function(){
    make();
    run();
});

function make() {
    // get options for deputys
    get_deputys();
    get_assistants();
    document.getElementById('date').valueAsDate = new Date();
    var set_date = document.getElementById('date').value
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
            calculate_hammer_change(document.getElementById('drilling_team').value);
            calculate_impact_part_change(document.getElementById('drilling_team').value);
            get_transmitted_information(document.getElementById('date').value, document.getElementById('drilling_team').value);
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
                var descriptions_html = response.message.descriptions_html;
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
            //Set default descriptions as Options for all description fields
            var description_06_07_icon = document.getElementById('description_06_07_icon');
                description_06_07_icon.addEventListener('click', function() {
                    var description_field = 'description_06_07';
                    chose_description(descriptions_html, description_field);
                });
            var description_07_08_icon = document.getElementById('description_07_08_icon');
                description_07_08_icon.addEventListener('click', function() {
                    var description_field = 'description_07_08';
                    chose_description(descriptions_html, description_field);
                });
            var description_08_09_icon = document.getElementById('description_08_09_icon');
                description_08_09_icon.addEventListener('click', function() {
                    var description_field = 'description_08_09';
                    chose_description(descriptions_html, description_field);
                });
            var description_09_10_icon = document.getElementById('description_09_10_icon');
                description_09_10_icon.addEventListener('click', function() {
                    var description_field = 'description_09_10';
                    chose_description(descriptions_html, description_field);
                });
            var description_10_11_icon = document.getElementById('description_10_11_icon');
                description_10_11_icon.addEventListener('click', function() {
                    var description_field = 'description_10_11';
                    chose_description(descriptions_html, description_field);
                });
            var description_11_12_icon = document.getElementById('description_11_12_icon');
                description_11_12_icon.addEventListener('click', function() {
                    var description_field = 'description_11_12';
                    chose_description(descriptions_html, description_field);
                });
            var description_12_13_icon = document.getElementById('description_12_13_icon');
                description_12_13_icon.addEventListener('click', function() {
                    var description_field = 'description_12_13';
                    chose_description(descriptions_html, description_field);
                });
            var description_13_14_icon = document.getElementById('description_13_14_icon');
                description_13_14_icon.addEventListener('click', function() {
                    var description_field = 'description_13_14';
                    chose_description(descriptions_html, description_field);
                });
            var description_14_15_icon = document.getElementById('description_14_15_icon');
                description_14_15_icon.addEventListener('click', function() {
                    var description_field = 'description_14_15';
                    chose_description(descriptions_html, description_field);
                });
            var description_15_16_icon = document.getElementById('description_15_16_icon');
                description_15_16_icon.addEventListener('click', function() {
                    var description_field = 'description_15_16';
                    chose_description(descriptions_html, description_field);
                });
            var description_16_17_icon = document.getElementById('description_16_17_icon');
                description_16_17_icon.addEventListener('click', function() {
                    var description_field = 'description_16_17';
                    chose_description(descriptions_html, description_field);
                });
            var description_17_18_icon = document.getElementById('description_17_18_icon');
                description_17_18_icon.addEventListener('click', function() {
                    var description_field = 'description_17_18';
                    chose_description(descriptions_html, description_field);
                });
            var description_18_19_icon = document.getElementById('description_18_19_icon');
                description_18_19_icon.addEventListener('click', function() {
                    var description_field = 'description_18_19';
                    chose_description(descriptions_html, description_field);
                });
            var description_19_20_icon = document.getElementById('description_19_20_icon');
                description_19_20_icon.addEventListener('click', function() {
                    var description_field = 'description_19_20';
                    chose_description(descriptions_html, description_field);
                });
            var description_20_21_icon = document.getElementById('description_20_21_icon');
                description_20_21_icon.addEventListener('click', function() {
                    var description_field = 'description_20_21';
                    chose_description(descriptions_html, description_field);
                });
            var description_21_22_icon = document.getElementById('description_21_22_icon');
                description_21_22_icon.addEventListener('click', function() {
                    var description_field = 'description_21_22';
                    chose_description(descriptions_html, description_field);
                });
            var notes_icon = document.getElementById('notes_icon');
                notes_icon.addEventListener('click', function() {
                    var description_field = 'notes';
                    chose_description(descriptions_html, description_field);
                });
            //Check if all mandatory fields are filled
            var input = document.getElementById('form');
            input.addEventListener('input', function() {
                handle_button_visibillity(check);
            });
            //Load other transmitted record if date is changed
            var entered_date = document.getElementById('date');
            entered_date.addEventListener('input', function() {
                get_transmitted_information(document.getElementById('date').value, document.getElementById('drilling_team').value);
            });
            
            //Show Object Location if Project is filled
            show_project_location("project", "location");
            show_project_location("project2", "location2");
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
    
    //show project street and location if a project has been entered
    var project_field = document.getElementById('project');
    var project_field2 = document.getElementById('project2');
    project_field.addEventListener('input', function() {
        show_project_location("project", "location");
    });
    project_field2.addEventListener('input', function() {
        show_project_location("project2", "location2");
    });
    
    //create document in ERPNext, when submit button has been pushed
    $(".btn-submit").on('click', function() {
        insert_feedback(1, args['key']);
    });
    
    $(".btn-save").on('click', function() {
        insert_feedback(0, args['key']);
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
    show_project_location(field, field.replace('project', 'location'))
}

function chose_description(descriptions_html, description_field) {
    document.getElementById('description_field_memory').value = description_field;
    var description_message = frappe.msgprint(descriptions_html, "Beschreibung wählen");
}

function set_description(self, description_choice) {
    var description_field = document.getElementById('description_field_memory').value;
    var check = document.getElementById('check_memory').value;
    document.getElementById(description_field).value = description_choice;
    frappe.ui.open_dialogs[0].hide();
}

function handle_button_visibillity(check) {
    if (check == "true") {
        check = true;
    }
    var button = document.getElementById('submit');
    var meter = document.getElementById('project_meter').value
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

function get_assistants() {
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.get_assistants_list',
        'callback': function(r) {
            var assistants = r.message
            var assistant_1Select = document.getElementById('assistant_1');
            var assistant_2Select = document.getElementById('assistant_2');
            assistants.forEach(function(option) {
                var assistantElement = document.createElement('option');
                assistantElement.text = option;
                assistant_1Select.add(assistantElement);
            });
            assistants.forEach(function(option) {
                var assistantElement = document.createElement('option');
                assistantElement.text = option;
                assistant_2Select.add(assistantElement);
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

function calculate_hammer_change(drilling_team) {
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.calculate_hammer_change',
        'args': {
            'drilling_team': drilling_team
        },
        'callback': function(response) {
            var last_change = response.message[0]
            var next_change = response.message[1]
            var hammer_change_calc = document.getElementById('hammer_change_calc');
            if (next_change < 0) {
                hammer_change_calc.textContent = " (Fällig seit " + next_change * -1 + "m!)"
                hammer_change_calc.style.color = "red";
            } else {
                hammer_change_calc.textContent = " (Vor " + last_change + "m, in " + next_change +"m)"
            }
        }
    });
}

function get_transmitted_information(date, drilling_team) {
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.get_transmitted_information',
        'args': {
            'date': date,
            'drilling_team': drilling_team
        },
        'callback': function(response) {
            if (response.message) {
                var record = response.message[0];
                var projects = response.message[1];
                var descriptions = response.message[2];
                document.getElementById('drilling_meter').value = record[0].drilling_meter;
                if (record[0].deputy) {
                    document.getElementById('deputy').value = record[0].deputy;
                } else {
                    var deputy = "Nein";
                    document.getElementById('deputy').value = deputy;
                }
                if (record[0].flushing == 1) {
                    document.getElementById('flushing').value = "Ja";
                } else {
                    document.getElementById('flushing').value = "Nein";
                }
                if (record[0].hammer_change == 1) {
                    document.getElementById('hammer_change').value = "Ja";
                } else {
                    document.getElementById('hammer_change').value = "Nein";
                }
                if (record[0].impact_part_change == 1) {
                    document.getElementById('impact_part_change').value = "Ja";
                } else {
                    document.getElementById('impact_part_change').value = "Nein";
                }
                if (!record[0].drilling_assistant_1 || record[0].drilling_assistant_1 != "Nein") {
                    document.getElementById('assistant_1').value = record[0].drilling_assistant_1;
                } else {
                    document.getElementById('assistant_1').value = "Keiner";
                }
                if (!record[0].drilling_assistant_2 || record[0].drilling_assistant_2 != "Nein") {
                    document.getElementById('assistant_2').value = record[0].drilling_assistant_2;
                } else {
                    document.getElementById('assistant_2').value = "Keiner";
                }
                if (record[0].temporary) {
                    document.getElementById('temporary').value = record[0].temporary;
                } else {
                    document.getElementById('temporary').value = "";
                }
                if (record[0].hotel_night == 1) {
                    document.getElementById('hotel_night').value = "Ja";
                } else {
                    document.getElementById('hotel_night').value = "Nein";
                }
                document.getElementById('project').value = projects[0].project_number;
                document.getElementById('project_meter').value = projects[0].project_meter;
                if (projects[1]) {
                    document.getElementById('project2').value = projects[1].project_number;
                    document.getElementById('project_meter2').value = projects[1].project_meter;
                } else {
                    document.getElementById('project2').value = "";
                    document.getElementById('project_meter2').value = "";
                }
                for (i=0; i < descriptions.length; i++) {
                    if (descriptions[i].description_time == "Bemerkungen") {
                        document.getElementById('notes').value = descriptions[i].description;
                    } else {
                        field_name = "description_" + descriptions[i].description_time.substring(0, 2) + "_" + descriptions[i].description_time.substring(8, 10);
                        document.getElementById(field_name).value = descriptions[i].description;
                    }
                }
            } else {
                document.getElementById('drilling_meter').value = "";
                document.getElementById('deputy').value = "Nein";
                document.getElementById('flushing').value = "Nein";
                document.getElementById('hammer_change').value = "Nein";
                document.getElementById('impact_part_change').value = "Nein";
                document.getElementById('assistant_1').value = "Keiner";
                document.getElementById('assistant_2').value = "Keiner";
                document.getElementById('temporary').value = "";
                document.getElementById('hotel_night').value = "Nein";
                document.getElementById('project').value = "";
                document.getElementById('project_meter').value = "";
                document.getElementById('project2').value = "";
                document.getElementById('project_meter2').value = "";
                document.getElementById('project2').value = "";
                document.getElementById('project_meter2').value = "";
                document.getElementById('description_06_07').value = "";
                document.getElementById('description_07_08').value = "";
                document.getElementById('description_08_09').value = "";
                document.getElementById('description_09_10').value = "";
                document.getElementById('description_10_11').value = "";
                document.getElementById('description_11_12').value = "";
                document.getElementById('description_12_13').value = "";
                document.getElementById('description_13_14').value = "";
                document.getElementById('description_14_15').value = "";
                document.getElementById('description_15_16').value = "";
                document.getElementById('description_16_17').value = "";
                document.getElementById('description_17_18').value = "";
                document.getElementById('description_18_19').value = "";
                document.getElementById('description_19_20').value = "";
                document.getElementById('description_20_21').value = "";
                document.getElementById('description_21_22').value = "";
                document.getElementById('notes').value = "";
            }
            show_project_location("project", "location");
            show_project_location("project2", "location2");
        }
    });
}

function get_overview() {
    let drilling_team = document.getElementById('drilling_team').value
    let year = new Date().getFullYear()
    console.log(year);
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.get_overview',
        'args': {
            'drilling_team': drilling_team,
            'year': year
        },
        'callback': function(response) {
            //~ if (response.message) {
                //~ document.getElementById(location_field).value = response.message;
            //~ } else {
                //~ document.getElementById(location_field).value = null;
            //~ }
        }
    });
}

function insert_feedback(finished_document, key) {
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.insert_feedback',
        'args': {
            'drilling_team': document.getElementById('drilling_team').value,
            'deputy': document.getElementById('deputy').value,
            'date': document.getElementById('date').value,
            'project': document.getElementById('project').value,
            'project_meter': document.getElementById('project_meter').value,
            'project2': document.getElementById('project2').value,
            'project_meter2': document.getElementById('project_meter2').value,
            'drilling_meter': document.getElementById('drilling_meter').value,
            'flushing': document.getElementById('flushing').value,
            'hammer_change': document.getElementById('hammer_change').value,
            'impact_part_change': document.getElementById('impact_part_change').value,
            'assistant_1': document.getElementById('assistant_1').value,
            'assistant_2': document.getElementById('assistant_2').value,
            'temporary': document.getElementById('temporary').value,
            'hotel_night': document.getElementById('hotel_night').value,
            'description_06_07': document.getElementById('description_06_07').value,
            'description_07_08': document.getElementById('description_07_08').value,
            'description_08_09': document.getElementById('description_08_09').value,
            'description_09_10': document.getElementById('description_09_10').value,
            'description_10_11': document.getElementById('description_10_11').value,
            'description_11_12': document.getElementById('description_11_12').value,
            'description_12_13': document.getElementById('description_12_13').value,
            'description_13_14': document.getElementById('description_13_14').value,
            'description_14_15': document.getElementById('description_14_15').value,
            'description_15_16': document.getElementById('description_15_16').value,
            'description_16_17': document.getElementById('description_16_17').value,
            'description_17_18': document.getElementById('description_17_18').value,
            'description_18_19': document.getElementById('description_18_19').value,
            'description_19_20': document.getElementById('description_19_20').value,
            'description_20_21': document.getElementById('description_20_21').value,
            'description_21_22': document.getElementById('description_21_22').value,
            'notes': document.getElementById('notes').value,
            'finished_document': finished_document,
            'link_key': document.getElementById('key').value = key
        },
        'callback': function(r) {
            frappe.msgprint("<b>Daten erfolgreich übermittelt!</b>", "Info");
        }
    });
}

function calculate_impact_part_change(drilling_team) {
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.calculate_impact_part_change',
        'args': {
            'drilling_team': drilling_team
        },
        'callback': function(response) {
            var last_change = response.message[0]
            var next_change = response.message[1]
            var impact_part_change_calc = document.getElementById('impact_part_change_calc');
            if (next_change < 0) {
                impact_part_change_calc.textContent = " (Fällig seit " + next_change * -1 + "m!)"
                impact_part_change_calc.style.color = "red";
            } else {
                impact_part_change_calc.textContent = " (Vor " + last_change + "m, in " + next_change +"m)"
            }
        }
    });
}

function show_project_location(project_field, location_field) {
    let entered_project = document.getElementById(project_field).value
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.feedback_bohrmeter.get_project_location',
        'args': {
            'project': entered_project
        },
        'callback': function(response) {
            if (response.message) {
                document.getElementById(location_field).value = response.message;
            } else {
                document.getElementById(location_field).value = null;
            }
        }
    });
}
