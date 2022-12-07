frappe.pages['object-overview'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Object Overview'),
        single_column: true
    });
    
    frappe.object_overview.make(page);
    frappe.object_overview.run();
    
    // add the application reference
    frappe.breadcrumbs.add("Heim Bohrtechnik");
}

frappe.object_overview = {
    start: 0,
    make: function(page) {
        var me = frappe.object_overview;
        me.page = page;
        me.body = $('<div></div>').appendTo(me.page.main);
        var data = "";
        $(frappe.render_template('object_overview', data)).appendTo(me.body);
        
        // load leaflet
        var cssId = 'leafletCss'; 
        if (!document.getElementById(cssId))
        {
            var head  = document.getElementsByTagName('head')[0];
            var link  = document.createElement('link');
            link.id   = cssId;
            link.rel  = 'stylesheet';
            link.type = 'text/css';
            link.href = '/assets/heimbohrtechnik/css/leaflet.css';
            link.media = 'all';
            head.appendChild(link);
        }

        frappe.object_overview.start_wait();
        
    },
    run: function() {
        // fetch object
        var object_name = frappe.object_overview.get_arguments();
        var gps_lat = 47.37767;
        var gps_long = 9.56121;
        var initial_zoom = 13;
        var geo = null;
        var radius = 0.1;
        if (!object_name) {
            radius = 10;    // no object: load full map
        }
        
        // prepare various icons
        var green_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-green.png'});
        var red_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-red.png'});
        var grey_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-grey.png'});
        var blue_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon.png'});
        
        // create map        
        var map = L.map('map').setView([gps_lat, gps_long], initial_zoom);
        // create layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        // hack: issue a resize event
        window.dispatchEvent(new Event('resize')); 
        
        document.getElementById("overlay-text").innerHTML = "<p>Objekte suchen...</p>";
        
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.utils.get_object_geographic_environment',
            'args': { 
                'object_name': object_name,
                'radius': radius
            },
            'callback': function(r) {
                if (r.message) {
                    geo = r.message;
                    gps_lat = geo.gps_lat;
                    gps_long = geo.gps_long;
                    map.panTo(new L.LatLng(gps_lat, gps_long));
                }
                
                document.getElementById("overlay-text").innerHTML = "<p>" + geo.environment.length + " Objekte platzieren...</p>";
                
                // add marker for the reference object
                L.marker([gps_lat, gps_long], {'icon': red_icon}).addTo(map)
                    .bindPopup(get_popup_str(object_name));
                // add other markers
                if (geo) {
                    console.log(geo);
                    for (var i = 0; i < geo.environment.length; i++) {
                        
                        // set icon color
                        var icon = grey_icon;
                        if (geo.environment[i].sales_order) {
                            icon = green_icon;
                        } else if (geo.environment[i].rate) {
                            icon = blue_icon;
                        }
                        L.marker([geo.environment[i].gps_lat, geo.environment[i].gps_long],
                            {'icon': icon}).addTo(map)
                            .bindPopup(get_popup_str(geo.environment[i].object, 
                                rate=geo.environment[i].rate,
                                sales_order=geo.environment[i].sales_order));

                    }
                }
                
                // hack: issue a resize event
                window.dispatchEvent(new Event('resize')); 
                frappe.object_overview.end_wait();
                frappe.show_alert(geo.environment.length + " Objekte geladen");
            }
        }); 
    },
    get_arguments: function() {
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
            if (args['object']) {
                return args['object'];
            }
        } 
    },
    start_wait: function() {
        document.getElementById("waitingScreen").style.display = "block";
    },
    end_wait: function() {
        document.getElementById("waitingScreen").style.display = "none";
    }
}

function get_popup_str(object_name, rate=null, sales_order=null) {
    html = "<b><a href=\"/desk#Form/Object/" 
        + (object_name || "HB-AG") + "\">" 
        + (object_name || "HB-AG") + "</a></b>";
    if (rate) {
        html += "<br>CHF " + parseFloat(rate).toFixed(2);
    }
    if (sales_order) {
        html += "<br><a href=\"/desk#Form/Sales Order/" 
        + sales_order + "\">" 
        + sales_order + "</a>";
    }
    return html;
}
