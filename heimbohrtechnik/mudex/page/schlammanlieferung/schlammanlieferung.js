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
    
    console.log(window.location);
}

frappe.schlammanlieferung = {
    start: 0,
    make: function(page) {
        var me = frappe.schlammanlieferung;
        me.page = page;
        me.body = $('<div></div>').appendTo(me.page.main);
        var data = "";
        $(frappe.render_template('schlammanlieferung', data)).appendTo(me.body);

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
            }
            if (args['customer']) {
                document.getElementById('customer').value = args['customer'];
            }
            if (args['object']) {
                var object_field = document.getElementById('object');
                object_field.value = args['object'];
                object_field.setAttribute('readonly', true);
                // fetch object data
                frappe.schlammanlieferung.get_object_details(args['object'], args['truck'], args['customer']);
            }
            
        } else {
            // no arguments provided
            
        }
    },
    get_object_details: function(object, truck, customer) {
        // fetch object details
        frappe.call({
            'method': 'heimbohrtechnik.mudex.page.schlammanlieferung.schlammanlieferung.get_object_details',
            'args': {
                'object_name': object,
                'truck': truck,
                'customer': customer
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
}
