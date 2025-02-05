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
        
        var red_icon = new L.Icon({'iconUrl': '/assets/heimbohrtechnik/images/marker-icon-orange.png'});
        
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
                        for (var i = 0; i < geo.length; i++) {
                            var icon = red_icon;
                            if (geo[i].gps_coordinates){
                                L.marker([geo[i].gps_coordinates.split(",")[0], geo[i].gps_coordinates.split(",")[1]],
                                    {'icon': icon}).addTo(map)
                                    .bindPopup(get_popup_str(geo[i].team_name, geo[i].project_name, geo[i].object_street, geo[i].object_location));
                            }
                        }
                    }
                }
                // hack: issue a resize event
                window.dispatchEvent(new Event('resize')); 
                frappe.teams_standorte.end_wait();
                frappe.show_alert(geo.length + " Objekte geladen");
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

function get_popup_str(team_name, project_name=null, object_street=null, object_location=null) {
    html = "<b>" + team_name + "</b>";
    if (project_name) {
        html += "<br>Projekt: <a href=\"/desk#Form/Project/" + project_name + "\" target=\"_blank\">" + project_name + "</a>";
    }
    if (object_street) {
        html += "<br>Adresse: " + object_street;
    }
    if (object_location) {
        html += "<br>Ort: " + object_location;
    }
    return html;
}