frappe.pages['object-overview'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Object Overview',
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
            link.href = '/assets/heimbohrtechnik/leaflet.css';
            link.media = 'all';
            head.appendChild(link);
        }

        /*// add menu button
        this.page.add_menu_item(__("Match payments"), function() {
            // navigate to bank import tool
            window.location.href="/desk#match_payments";
        });
        this.page.add_menu_item(__("Debug Template"), function() {
            // navigate to bank import tool
            $('.btn-parse-file').trigger('click', [true]);
        });*/

    },
    run: function() {
        // populate bank accounts

    }
}
