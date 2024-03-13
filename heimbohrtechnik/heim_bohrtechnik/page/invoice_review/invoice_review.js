frappe.pages['invoice-review'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Invoice Review'),
        single_column: true
    });

    frappe.invoice_review.make(page);
    frappe.invoice_review.run();
    
    // add the application reference
    frappe.breadcrumbs.add("Heim Bohrtechnik");

}

frappe.invoice_review = {
    start: 0,
    make: function(page) {
        var me = frappe.invoice_review;
        me.page = page;
        me.body = $('<div></div>').appendTo(me.page.main);
        var data = "";
        $(frappe.render_template('invoice_review', data)).appendTo(me.body);
    },
    run: function() {
        // check for url parameters
        var url = location.href;
        var payment_proposal = null;
        if (url.indexOf("?payment_proposal=") >= 0) {
            payment_proposal = url.split('=')[1].split('&')[0];
        }
        
        frappe.invoice_review.get_invoices_for_review(payment_proposal);
    },
    get_invoices_for_review: function(payment_proposal, show_all) {
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.page.invoice_review.invoice_review.get_invoices_for_review',
            'args': {
                'user': frappe.session.user,
                'payment_proposal': payment_proposal
            },
            'callback': function(r) {
                var invoices = r.message;
                frappe.invoice_review.display_invoices(invoices);
            }
        });
    },
    display_invoices: function(invoices) {
        // create rows
        var html = "";
        document.getElementById("invoices_view").innerHTML = "";
        for (var i = 0; i < invoices.length; i++) {
            html += invoices[i].html;
        }
        
        // insert content
        document.getElementById("invoices_view").innerHTML = html;
        
        // attach button handlers
        for (var i = 0; i < invoices.length; i++) {
            var btn_reviewed = document.getElementById("btn_reviewed_" + invoices[i].name);
            btn_reviewed.onclick = frappe.invoice_review.reviewed.bind(this, invoices[i].name);
        }
    },
    reviewed: function(pinv) {
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.page.invoice_review.invoice_review.reviewed',
            'args': {
                'pinv': pinv,
                'user': frappe.session.user
            },
            'callback': function(r) {
                document.getElementById("row_" + pinv).style.display = "none";
            }
        });
    }
}
