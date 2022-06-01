// extend dashboard
try {
    cur_frm.dashboard.add_transactions([
        {
            'label': 'Drilling',
            'items': ['Construction Site Description', 'Bohranzeige']
        }
    ]);
} catch { /* do nothing for older versions */ }

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
            'method': 'heimbohrtechnik.mudex.doctype.truck_delivery.truck_delivery.has_invoiceable_mud',
            'args': {'object': frm.doc.name},
            'callback': function(response) {
                if (response.message) {
                    frm.add_custom_button( __("Abrechnen"), function() {
                        create_mud_invoice(frm.doc.name);
                    }, "MudEX");
                }
            }
        });
        // add link-button to drillplanner
        frm.add_custom_button(__("Öffne Bohrplaner"), function() {
            //window.location = '/desk#bohrplaner';
            frappe.route_options = {"from": cur_frm.doc.expected_start_date, "project_name": cur_frm.doc.name}
            frappe.set_route("bohrplaner");
        });
        // show insurance information
        if (!frm.doc.__islocal) {
            show_insurance_information(frm.doc.name);
        }
    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
    }
});
