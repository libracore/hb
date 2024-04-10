$('document').ready(function(){
    make();
    run();
});


function make() {
    // reset values
    document.getElementById('full_weight').value = null;
    // rebrand
    var brands = document.getElementsByClassName('navbar-brand');
    for (var e = 0; e < brands.length; e++) {
        brands[e].innerHTML = "<span>MudEX AG</span>";
    }
    // attach button handlers
    $(".btn-weigh").on('click', function() { 
        var full_weight = document.getElementById('full_weight').value;
        var target = 'full_weight';
        if ((full_weight) && (full_weight > 0)) {
            target = 'empty_weight';
        }
        frappe.call({
            'method': 'heimbohrtechnik.mudex.doctype.truck_scale.truck_scale.get_weight',
            'args': {
                'truck_scale': document.getElementById('scale').value
            },
            'callback': function(r) {
                if (typeof r.message !== 'undefined') {
                    document.getElementById(target).value = r.message.weight;
                    if (target == "full_weight") {
                        document.getElementById('full_time').value = get_now();
                        document.getElementById('full_process_id').value = r.message.process_id;
                    } else {
                        document.getElementById('empty_time').value = get_now();
                        document.getElementById('empty_process_id').value = r.message.process_id;
                    }
                    compute_net();
                } else {
                    console.log("Invalid response");
                }
            }
        });
    });
    $(".btn-submit").on('click', function() { 
        frappe.call({
            'method': 'heimbohrtechnik.templates.pages.schlammanlieferung.insert_delivery',
            'args': {
                'truck': document.getElementById('truck').value, 
                'customer': document.getElementById('customer').value, 
                'object': document.getElementById('object').value, 
                'full_weight': document.getElementById('full_weight').value, 
                'empty_weight': document.getElementById('empty_weight').value, 
                'net_weight': document.getElementById('net_weight').value, 
                'traces': [{
                    'date': document.getElementById('full_time').value,
                    'scale': document.getElementById('scale').value,
                    'weight': document.getElementById('full_weight').value,
                    'process_id': document.getElementById('full_process_id').value
                },
                {
                    'date': document.getElementById('empty_time').value,
                    'scale': document.getElementById('empty_scale').value,
                    'weight': document.getElementById('empty_weight').value,
                    'process_id': document.getElementById('empty_process_id').value
                }],
                'load_type': document.getElementById('load_type').value,
                'ph': document.getElementById('ph').value
            },
            'callback': function(r) {
                if (typeof r.message !== 'undefined') {
                    var btn_submit = document.getElementById('submit');
                    btn_submit.disabled = true;
                    btn_submit.style.visibility = "hidden";
                    var row_success = document.getElementById('finalised-row');
                    row_success.style.visibility = "visible";
                    var txt_success = document.getElementById('result-doc');
                    txt_success.innerHTML = r.message.delivery;
                    document.getElementById('load_type').disabled = true;
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
        if (args['truck']) {
            document.getElementById('truck').value = args['truck'];
            get_truck_weight(args['truck']);
        }
        if (args['customer']) {
            document.getElementById('customer').value = args['customer'];
        }
        if (args['key']) {
            document.getElementById('key').value = args['key'];
        }
        if (args['object']) {
            var object_field = document.getElementById('object');
            object_field.value = args['object'];
            object_field.setAttribute('readonly', true);
            // fetch object data
            get_object_details(args['object'], args['truck'], args['customer'], args['key']);
        }
        
    } else {
        // no arguments provided
        
    }
    // get scale 
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.schlammanlieferung.get_default_scale',
        'callback': function(r) {
            document.getElementById('scale').value  = r.message
        }
    });
    // get load types
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.schlammanlieferung.get_load_types',
        'args': {
            'object': args['object'] || null
        },
        'callback': function(r) {
            console.log(r);
            var select = document.getElementById('load_type');
            if (r.message.types) {
                var selector = "";
                for (i = 0; i < r.message.types.length; i++) {
                    if (r.message.types[i]['name'] === r.message.object_load_type) {
                        selector = "selected";
                    } else {
                        selector = "";
                    }
                    select.innerHTML += "<option value=\"" + r.message.types[i]['name'] 
                        + "\" " + selector + ">" + r.message.types[i]['name'] + "</option>";
                }
            }
        }
    });
}

function get_object_details(object, truck, customer, key) {
    // fetch object details
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.schlammanlieferung.get_object_details',
        'args': {
            'object_name': object,
            'truck': truck,
            'customer': customer,
            'key': key
        },
        'callback': function(r) {
            if (r.message.address) {
                var object_text = document.getElementById('object_text');
                object_text.innerHTML = r.message.address
            } else {
                console.log(r.message);
            }
        }
    });
}

function get_truck_weight(truck) {
    // fetch object details
    frappe.call({
        'method': 'heimbohrtechnik.templates.pages.schlammanlieferung.get_truck_weight',
        'args': {
            'truck': truck
        },
        'callback': function(r) {
            if (r.message.weight) {
                document.getElementById('empty_weight').value = r.message.weight;
                document.getElementById('empty_time').value = get_now();
                document.getElementById('empty_process_id').value = ":" + truck;
                document.getElementById('empty_scale').value = null;
            }
        }
    });
}

function compute_net() {
    var full_weight = document.getElementById('full_weight').value;
    var empty_weight = document.getElementById('empty_weight').value;
    if ((full_weight) && (empty_weight)) {
        var net_weight = full_weight - empty_weight;
        document.getElementById('net_weight').value = net_weight;
        if (net_weight > 0) {
            var btn_weigh = document.getElementById('weigh');
            btn_weigh.disabled = true;
            btn_weigh.style.visibility = "hidden";
            var btn_submit = document.getElementById('submit');
            btn_submit.disabled = false;
            btn_submit.style.visibility = "visible";
        }
    }
}

function get_now() {
    var now = new Date();
    var timestamp = now.getFullYear() + "-" + (now.getMonth() + 1) + "-" + now.getDate() + " " + now.getHours() + ":" + now.getMinutes() + ":" + now.getSeconds();
    return timestamp;
}
