frappe.pages['schlammanlieferung'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Schlammanlieferung',
        single_column: true
    });
    
    frappe.schlammanlieferung.make(page);
    frappe.schlammanlieferung.run();
    
    // add the application reference
    frappe.breadcrumbs.add("MudEx");
}

frappe.schlammanlieferung = {
    start: 0,
    make: function(page) {
        var me = frappe.schlammanlieferung;
        me.page = page;
        me.body = $('<div></div>').appendTo(me.page.main);
        var data = "";
        $(frappe.render_template('schlammanlieferung', data)).appendTo(me.body);
        
        // attach button handlers
        this.page.main.find(".btn-weigh").on('click', function() { 
            var full_weight = document.getElementById('full_weight').value;
            var target = 'full_weight';
            if ((full_weight) && (full_weight > 0)) {
                target = 'empty_weight';
            }
            frappe.call({
                'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.truck_scale.truck_scale.get_weight',
                'args': {
                    'truck_scale': document.getElementById('scale').value
                },
                'callback': function(r) {
                    if (typeof r.message !== 'undefined') {
                        document.getElementById(target).value = r.message.weight;
                        if (target == "full_weight") {
                            document.getElementById('full_time').value = frappe.datetime.now();
                            document.getElementById('full_process_id').value = r.message.process_id;
                        } else {
                            document.getElementById('empty_time').value = frappe.datetime.now();
                            document.getElementById('empty_process_id').value = r.message.process_id;
                        }
                        frappe.schlammanlieferung.compute_net();
                    } else {
                        console.log("Invalid response");
                    }
                }
            });
        });
        this.page.main.find(".btn-submit").on('click', function() { 
            
        });
    },
    run: function() {
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
                frappe.schlammanlieferung.get_truck_weight(args['truck']);
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
                frappe.schlammanlieferung.get_object_details(args['object'], args['truck'], args['customer'], args['key']);
            }
            
        } else {
            // no arguments provided
            
        }
        // get scale 
        frappe.call({
            'method': 'heimbohrtechnik.mudex.page.schlammanlieferung.schlammanlieferung.get_default_scale',
            'callback': function(r) {
                document.getElementById('scale').value  = r.message
            }
        });
    },
    get_object_details: function(object, truck, customer, key) {
        // fetch object details
        frappe.call({
            'method': 'heimbohrtechnik.mudex.page.schlammanlieferung.schlammanlieferung.get_object_details',
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
    },
    get_truck_weight: function(truck) {
        // fetch object details
        frappe.call({
            'method': 'heimbohrtechnik.mudex.page.schlammanlieferung.schlammanlieferung.get_truck_weight',
            'args': {
                'truck': truck
            },
            'callback': function(r) {
                if (r.message.weight) {
                    var empty_field = document.getElementById('empty_weight');
                    empty_field.value = r.message.weight;
                }
            }
        });
    },
    compute_net: function() {
        var full_weight = document.getElementById('full_weight').value;
        var empty_weight = document.getElementById('empty_weight').value;
        if ((full_weight) && (empty_weight)) {
            var net_weight = full_weight - empty_weight;
            document.getElementById('net_weight').value = net_weight;
            var btn_weigh = document.getElementById('weigh');
            btn_weigh.classList.add("disabled");
            var btn_submit = document.getElementById('submit');
            btn_submit.classList.remove("disabled");
        }
    }
}
