$('document').ready(function(){
    make();
    run();
});


function make() {
    // embed QR code reader
    if (typeof Html5Qrcode === 'undefined') {
        const script = document.createElement('script');
        script.src = '/assets/heimbohrtechnik/js/html5-qrcode.min.js';
        script.onload = start_scanner;
        document.body.appendChild(script);
    } else {
        start_scanner();
    }
        
    // attach event listeners
    let pin_field = document.getElementById("pin");
    pin_field.addEventListener("keydown", pin_input);
    let item_field = document.getElementById("item_code");
    item_field.addEventListener("keydown", item_input);
    
    // attach button handlers
    $(".btn-submit").on('click', function() { 
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.kleidermagazin.kleidermagazin.insert_material_issue',
            'args': {
                'secret': document.getElementById('secret').value, 
                'user': document.getElementById('user').value, 
                'item': document.getElementById('item_code').value, 
                'qty': document.getElementById('qty').value, 
                'employee': document.getElementById('employee').value, 
                'remarks': document.getElementById('remarks').value || ""
            },
            'callback': function(r) {
                if (typeof r.message !== 'undefined') {
                    let btn_submit = document.getElementById('submit');
                    btn_submit.disabled = true;
                    btn_submit.style.visibility = "hidden";
                    document.getElementById('finalised-row').style.visibility = "visible";
                    document.getElementById('action-row').style.display = "none";
                } else {
                    console.log("Invalid response");
                }
            }
        });
        
    });
}
function run() {
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
        if (args['secret']) {
            document.getElementById('secret').value = args['secret'];
        }
        
        // get employees
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.kleidermagazin.kleidermagazin.get_employees',
            'args': {
                'secret': args['secret'] || null
            },
            'callback': function(r) {

                let select = document.getElementById('employee');
                if (r.message.employees) {
                    for (i = 0; i < r.message.employees.length; i++) {
                        select.innerHTML += "<option value=\"" + r.message.employees[i]['name'] 
                            + "\" >" + r.message.employees[i]['employee_name'] + "</option>";
                    }
                    
                    // enable content here
                    document.getElementById('body').style.visibility = "visible";
                } else {
                    frappe.msgprint("Ungültiger Zugang")
                }
            }
        });
        
    } else {
        // no arguments provided
        frappe.msgprint("Bitte Zugangslink verwenden")
    }


}

function pin_input(e) {
    if (e.keyCode == 13) {
        let pin = document.getElementById('pin');
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.kleidermagazin.kleidermagazin.check_pin',
            'args': {
                'secret': document.getElementById('secret').value || null,
                'pin': pin.value
            },
            'callback': function(r) {
                if (r.message.user) {
                    document.getElementById('user').value = r.message.user;
                    document.getElementById('action-row').style.visibility = "visible";
                    document.getElementById('item_code').value = "";
                    document.getElementById('remarks').value = "";
                    document.getElementById('qty').value = 1;
                    document.getElementById('pin-row').style.display = "none";
                } else {
                    frappe.msgprint("Ungültiger Zugang")
                }
            }
        });
    }
}

function item_input(e) {
    if ((e.keyCode == 13) && (document.getElementById('item_code').value)) {
        enable_submit();
    }
}

function enable_submit() {
    document.getElementById('submit').style.visibility = "visible";
    document.getElementById('submit').disabled = false;
}

function start_scanner() {
    const qr_code_scanner = new Html5Qrcode("reader");
    qr_code_scanner.start(
        { 
            'facingMode': "environment"
        },
        {
            'fps': 10, 
            'qrbox': 250
        },
        (decoded_text, decoded_result) => {
            document.getElementById('item_code').value = decoded_text;
            enable_submit();
            qr_code_scanner.stop();
        }
    ).catch(err => {
        show_alert({
            'message': __(`QR-Scanner konnte nicht gestartet werden: ${err}`), 
            'indicator': 'red'});
    });
}


