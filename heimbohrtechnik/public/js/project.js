frappe.ui.form.on('Project', {
    refresh(frm) {
        // filter suppliers by activity
        frm.fields_dict.checklist.grid.get_field('supplier').get_query =   
            function(doc, cdt, cdn) {    
                var row = locals[cdt][cdn];
                return {
                    filters: {'capability': row.activity},
                    query: "heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability"
                };
        };
        // check if mud can be invoiced
        frappe.call({
            'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.truck_delivery.truck_delivery.has_invoiceable_mud',
            'args': {'object': frm.doc.name},
            'callback': function(response) {
                if (response.message) {
                    frm.add_custom_button( __("Abrechnen"), function() {
                        create_mud_invoice(frm);
                    }, "MudEX");
                }
            }
        });
    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
    }
});
