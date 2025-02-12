var global = {
    status: null,
    project: null
};

$('document').ready(function(){
    make();
    run();
});

function make(){
    reset_fields();
    add_event_listeners();
    fetch_project_data();
}

function run(){
    display_correct_fields();
}

function reset_fields(){
    document.getElementById('custom_drilling_depth').style.display = 'none';
    document.getElementById('invalid-project').style.display = 'none';
    document.getElementById('valid-project').style.display = 'block';
    document.getElementById('benutzerdefiniert_num').value = '';
    document.getElementById('bohrmeister').value = '';
    document.getElementById('entgegennahme_durch').value = '';
    document.getElementById('geologische_fachperson').value = '';
    document.getElementById('ausgehaendigt_von').value = '';
    document.getElementById('bohrprobe_2m').checked = false;
    document.getElementById('bohrprobe_4m').checked = false;
    document.getElementById('bohrprobe_benutzerdefiniert').checked = false;
    document.getElementById('lagerort_magazin').checked = false;
    document.getElementById('lagerort_baustelle').checked = false;
    document.getElementById('zustand_OK').checked = false;
    document.getElementById('zustand_mittel').checked = false;
    document.getElementById('zustand_schlecht').checked = false;
}

function add_event_listeners(){
    // event listener for custom drilling depth
    document.getElementById('bohrprobe_benutzerdefiniert').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('custom_drilling_depth').style.display = 'block';
        }
    });
    document.getElementById('bohrprobe_2m').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('custom_drilling_depth').style.display = 'none';
        }
    });
    document.getElementById('bohrprobe_4m').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('custom_drilling_depth').style.display = 'none';
        }
    });


    // event listener for submission
    document.getElementById('submit').addEventListener('click', function() {
        var lagerortSelected = document.querySelector('input[name="lagerort"]:checked');
        var bohrprobeSelected = document.querySelector('input[name="bohrprobe_alle"]:checked');
        var zustandSelected = document.querySelector('input[name="zustand_bohrmaterial"]:checked');
        var bohrmeister = document.getElementById('bohrmeister').value;
        var entgegennahme_durch = document.getElementById('entgegennahme_durch').value;
        if (!lagerortSelected || !bohrprobeSelected || !zustandSelected || !bohrmeister || !entgegennahme_durch) {
            alert('Bitte füllen Sie alle Felder aus.');
            event.preventDefault();
        } else {
            if (global.status === "erfasst"){
                var geologische_fachperson = document.getElementById('geologische_fachperson').value;
                var ausgehaendigt_von = document.getElementById('ausgehaendigt_von').value;
                if (!geologische_fachperson || !ausgehaendigt_von) {
                    alert('Bitte füllen Sie alle Felder aus.');
                    event.preventDefault();
                } else {
                    submit_drilling_sample();
                }
            } else {
                submit_drilling_sample();
            }
        }
    });
}

function get_project() {
    const urlParams = new URLSearchParams(window.location.search);
    const project = urlParams.get('project');
    return project;
}

function fetch_project_data(){
    global.project = get_project();

    if (global.project) {
        frappe.call({
            method: 'heimbohrtechnik.heim_bohrtechnik.doctype.drilling_sample.drilling_sample.fetch_project_data',
            args: {
                "project_name": global.project
            },
            'callback': function(r) {
                let today = new Date();
                let todayPlus7 = new Date(today);
                todayPlus7.setDate(today.getDate() + 7);
                let todayMinus7 = new Date(today);
                todayMinus7.setDate(today.getDate() - 7)

                if (r.message && new Date(r.message.expected_start_date) <= todayPlus7 && new Date(r.message.expected_end_date) >= todayMinus7) {
                    document.getElementById('project').innerHTML = "Projekt: " + global.project;
                    document.getElementById('project').setAttribute('readonly', true);
                    document.getElementById('address').innerHTML = "Adresse: " + r.message.address;
                    document.getElementById('address').setAttribute('readonly', true);
                    document.getElementById('geologist_address').innerHTML = "Geologe Adresse: " + r.message.geology_office;
                    document.getElementById('geologist_address').setAttribute('readonly', true);
                    document.getElementById('geologist_name').innerHTML = "Geologe Name: " + r.message.geology_office_name;
                    document.getElementById('geologist_name').setAttribute('readonly', true);
                } else {
                    display_invalid();
                }
            }
        });
    } else {
        display_invalid();
    }
}

function display_correct_fields(){
    frappe.call({
        "method": "heimbohrtechnik.templates.pages.drilling_sample_controller.get_drilling_sample",
        "args": {
            "project": global.project
        },
        "callback": function(response) {
            if (response.message) {
                if (response.message.some(sample => sample.status === "erfasst")) {
                    var drilling_sample = response.message.find(sample => sample.status === "erfasst");
                    global.status = "erfasst";
                    display_geologist_form(drilling_sample);
                } else {
                    global.status = "neu";
                }
            }
        }
    });
}

function display_geologist_form(drilling_sample){
    //disable radio buttons
    document.getElementById('bohrprobe_2m').disabled = true;
    document.getElementById('bohrprobe_4m').disabled = true;
    document.getElementById('bohrprobe_benutzerdefiniert').disabled = true;
    document.getElementById('lagerort_magazin').disabled = true;
    document.getElementById('lagerort_baustelle').disabled = true;
    document.getElementById('zustand_OK').disabled = true;
    document.getElementById('zustand_mittel').disabled = true;
    document.getElementById('zustand_schlecht').disabled = true;

    // fill in the form with the drilling sample data
    if (drilling_sample.drilling_samples_all === 'benutzerdefiniert') {
        document.getElementById('bohrprobe_benutzerdefiniert').checked = true;
        document.getElementById('benutzerdefiniert_num').value = drilling_sample.custom_drilling_depth;
        document.getElementById('benutzerdefiniert_num').readOnly = true;
        document.getElementById('custom_drilling_depth').style.display = 'block';
    } else if (drilling_sample.drilling_samples_all === 'alle 2m') {
        document.getElementById('bohrprobe_2m').checked = true;
    } else if (drilling_sample.drilling_samples_all === 'alle 4m') {
        document.getElementById('bohrprobe_4m').checked = true;
    }
    
    if (drilling_sample.storage_location === 'Magazin') {
        document.getElementById('lagerort_magazin').checked = true;
    } else if (drilling_sample.storage_location === 'Baustelle/Bauherrschaft') {
        document.getElementById('lagerort_baustelle').checked = true;
    }
    
    if (drilling_sample.condition_of_drill_material__drill_bags === 'OK') {
        document.getElementById('zustand_OK').checked = true;
    } else if (drilling_sample.condition_of_drill_material__drill_bags === 'mittel') {
        document.getElementById('zustand_mittel').checked = true;
    } else if (drilling_sample.condition_of_drill_material__drill_bags === 'schlecht') {
        document.getElementById('zustand_schlecht').checked = true;
    }
    
    document.getElementById('bohrmeister').value = drilling_sample.drilling_master;
    document.getElementById('bohrmeister').readOnly = true;
    document.getElementById('entgegennahme_durch').value = drilling_sample.acceptance_by;
    document.getElementById('entgegennahme_durch').readOnly = true;

    // display the form
    document.getElementById('geologist-section').style.display = 'block';
}

function display_invalid(){
    document.getElementById("invalid-project").style.display = "block";
    document.getElementById("valid-project").style.display = "none";
}

function submit_drilling_sample(){
    var lagerort = document.querySelector('input[name="lagerort"]:checked')?.value || '';
    var bohrprobe_alle = document.querySelector('input[name="bohrprobe_alle"]:checked')?.value || '';
    var benutzerdefiniert_num = '';
    if (bohrprobe_alle === 'benutzerdefiniert') {
        benutzerdefiniert_num = document.getElementById('benutzerdefiniert_num').value || '';
    }
    var zustand_bohrmaterial = document.querySelector('input[name="zustand_bohrmaterial"]:checked')?.value || '';
    var bohrmeister = document.getElementById('bohrmeister').value || '';
    var entgegennahme_durch = document.getElementById('entgegennahme_durch').value || '';

    const userAgent = navigator.userAgent;

    if (global.status === "erfasst") {
        var geologische_fachperson = document.getElementById('geologische_fachperson').value || '';
        var ausgehaendigt_von = document.getElementById('ausgehaendigt_von').value || '';
        var geologist_browser = userAgent;
        var drilling_master_browser = '';
    } else {
        var geologische_fachperson = '';
        var ausgehaendigt_von = '';
        var geologist_browser = '';
        var drilling_master_browser = userAgent;
    }

    frappe.call({
        "method": "heimbohrtechnik.templates.pages.drilling_sample_controller.submit_drilling_sample",
        "args": {
            "project": global.project,
            "status": global.status,
            "lagerort": lagerort,
            "bohrprobe_alle": bohrprobe_alle,
            "benutzerdefiniert_num": benutzerdefiniert_num,
            "zustand_bohrmaterial": zustand_bohrmaterial,
            "bohrmeister": bohrmeister,
            "entgegennahme_durch": entgegennahme_durch,
            "geologische_fachperson": geologische_fachperson,
            "ausgehaendigt_von": ausgehaendigt_von,
            "geologist_browser": geologist_browser,
            "drilling_master_browser": drilling_master_browser
        },
        "callback": function(response) {
            if (response.message) {
                document.getElementById('end-section').style.display = 'block';
                document.getElementById('valid-project').style.display = 'none';
            } else {
                frappe.msgprint("Fehler beim Einreichen der Bohrprobe");
            }
        }
    });
}