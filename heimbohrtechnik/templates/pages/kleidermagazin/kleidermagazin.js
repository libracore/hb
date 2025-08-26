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
        let items = [];
        let cart = document.getElementById("cart");
        for (let i = 0; i < cart.children.length; i++) {
            items.push(cart.children[i].innerHTML.split("&nbsp;")[0]);
        }
        console.log(items);
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.kleidermagazin.kleidermagazin.insert_material_issue',
            'args': {
                'secret': document.getElementById('secret').value, 
                'user': document.getElementById('user').value, 
                'items': items,
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
                    document.getElementById('pin-row').style.display = "none";
                    document.getElementById('item_code').value = "";
                    document.getElementById('remarks').value = "";
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
            // only accept scan if it is 3 seconds after last or different code (prevent double reads)
            if ((decoded_text != document.getElementById('item_code').value) ||
                (Date.now() > (parseInt(document.getElementById('last_scan').value) + 3000))) {
                    var now = Date.now();
                    document.getElementById('item_code').value = decoded_text;
                    document.getElementById('cart').innerHTML += "<p id='item_" + now + "'>" + decoded_text + "&nbsp;&nbsp;<span onclick='remove_item(`item_" + now + "`);' style='cursor: pointer; '><i class='fa fa-trash'></i></span></p>";
                    document.getElementById('last_scan').value = Date.now();
                    enable_submit();
            }
        }
    ).catch(err => {
        show_alert({
            'message': __(`QR-Scanner konnte nicht gestartet werden: ${err}`), 
            'indicator': 'red'});
    });
}

function remove_item(item_name) {
    document.getElementById(item_name).remove();
}
