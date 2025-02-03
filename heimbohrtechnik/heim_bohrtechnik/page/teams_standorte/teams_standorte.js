frappe.pages['teams-standorte'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Teams & Standorte',
        single_column: true
    });

    frappe.teams_standorte.make(page);
    frappe.teams_standorte.render_map();

    frappe.breadcrumbs.add("Heim Bohrtechnik");
}

frappe.teams_standorte = {
    start: 0,
    make: function(page) {
        var me = frappe.teams_standorte;
        me.page = page;
        me.body = $('<div></div>').appendTo(me.page.main);
    
        
        var data = "";
        $(frappe.render_template('teams_standorte', data)).appendTo(me.body);

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

        frappe.teams_standorte.start_wait();
        
    },
    render_map: function() {
        // fetch object
        var gps_lat = 47.37767;
        var gps_long = 9.56121;
        var initial_zoom = 13;
        var geo = null;
        var radius = 10;
        
        // prepare various icons
        var green_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-green.png'});
        var red_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/BG_blau_48x48.png'});
        var grey_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-grey.png'});
        var blue_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon.png'});
        var orange_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-orange.png'});
        var grey_icon_active = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-grey_active.png'});
        var green_icon_active = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-green_active.png'});
        var orange_icon_active = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-orange_active.png'});
        var blue_icon_active = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon_active.png'});
        var green_icon_warning = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-green_warning.png'});
        
        // create map     
        document.getElementById('map-container').innerHTML = "<div id='map' style='width: 100%; height: 800px;'></div>";
        var map = L.map('map').setView([gps_lat, gps_long], initial_zoom);
        // create layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(map);
        // hack: issue a resize event
        window.dispatchEvent(new Event('resize')); 
        
        document.getElementById("overlay-text").innerHTML = "<p>Objekte suchen...</p>";

        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.page.teams_standorte.teams_standorte.get_teams_and_locations',
            'callback': function(r) {
                if (r.message) {
                    geo = r.message;
                    if (geo) {
                        console.log(geo);
                        for (var i = 0; i < geo.environment.length; i++) {
                            var icon = red_icon;
                            L.marker([geo.environment[i].gps_lat, geo.environment[i].gps_long],
                                {'icon': icon}).addTo(map)
                                .bindPopup(get_popup_str(geo.environment[i].object, 
                                    rate=geo.environment[i].rate,
                                    sales_order=geo.environment[i].sales_order,
                                    cloud_url=geo.environment[i].cloud_url,
                                    sv=geo.environment[i].sv,
                                    quotation=geo.environment[i].quotation,
                                    to_depth=geo.environment[i].to_depth,
                                    drilling_method=geo.environment[i].drilling_method,
                                    arteser=geo.environment[i].arteser));

                        }
                    }
                }
                // hack: issue a resize event
                window.dispatchEvent(new Event('resize')); 
                frappe.teams_standorte.end_wait();
                frappe.show_alert(geo.environment.length + " Objekte geladen");
            }
        });
    },
    start_wait: function() {
        document.getElementById("waitingScreen").style.display = "block";
    },
    end_wait: function() {
        document.getElementById("waitingScreen").style.display = "none";
    }   
}     

function get_popup_str(object_name, rate=null, sales_order=null, cloud_url=null, sv=null, quotation=null, 
    to_depth=null, drilling_method=null, arteser=null) {
    html = "<b><a href=\"/desk#Form/Object/" 
        + (object_name || "HB-AG") + "\" target=\"_blank\">" 
        + (object_name || "HB-AG") + "</a></b>";
    if (rate) {
        html += "<br>CHF " + parseFloat(rate).toFixed(2);
    }
    if (quotation) {
        html += "<br><a href=\"/desk#Form/Quotation/" 
        + quotation + "\" target=\"_blank\">" 
        + quotation + "</a>";
    }
    if (sales_order) {
        html += "<br><a href=\"/desk#Form/Sales Order/" 
        + sales_order + "\" target=\"_blank\">" 
        + sales_order + "</a>";
    }
    if (cloud_url) {
        html += "<br><a href=\"" + cloud_url + "\" target=\"_blank\"><i class=\"fa fa-cloud\"></i> Cloud</a>&nbsp;";
    }
    if (sv) {
        html += "&nbsp;&middot;&nbsp;&nbsp;<a href=\"/desk#Form/Layer Directory/" 
        + sv + "\" target=\"_blank\">SV</a>";
    }
    if (to_depth) {
        html += "<br>Verrohrung bis " + to_depth + " m";
    }
    if (drilling_method) {
        html += "<br>" + drilling_method;
    }
    if (arteser === 1) {
        html += "<br><b>Vorsicht Arteser!</b>";
    }
    return html;
}

function find_gps(address) {
    if (!locals.gps_location_pending) {
        locals.gps_location_pending = true;     // prevent multiple calls from plz/city change events
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_gps',
            'args': {
                'street': address,
                'location': ""
            },
            'callback': function(response) {
                locals.gps_location_pending = false;
                if (response.message) {
                    if (response.message === "queued") {
                        // the request has been sent, check back in a second
                        setTimeout( function() {
                            find_gps(address);
                        }, 1000);
                    } else {
                        frappe.object_overview.render_map(address);
                    }
                } else {
                    frappe.msgprint( __("Addresse nicht gefunden") , __("Geolocation") );
                    frappe.object_overview.render_map();
                }
            }
        });
    }
}

function highlight_legend_item(class_name, weight) {
    var legends = document.getElementsByClassName(class_name);
    for (var i = 0; i < legends.length; i++) {
        legends[i].style.fontWeight = weight;
    }
}