// extend dashboard
try {
    cur_frm.dashboard.add_transactions([
        {
            'label': 'Drilling',
            'items': ['Construction Site Description', 'Bohranzeige', 'Construction Site Delivery', 'Subcontracting Order']
        }
    ]);
} catch { /* do nothing for older versions */ }

frappe.ui.form.on('Project', {
    refresh(frm) {
        // show permits & checklist (in case coming from another record where it was hidden)
        var checklists = document.querySelectorAll("[data-fieldname='checklist']");
        try {
            for (var i = 0; i < checklists.length; i++) {
                checklists[i].parentElement.parentElement.parentElement.parentElement.style.display = "Block";
            }
        } catch { /* do nothing */ }
        // filter suppliers by activity
        frm.fields_dict.checklist.grid.get_field('supplier').get_query =   
            function(doc, cdt, cdn) {    
                var row = locals[cdt][cdn];
                return {
                    query: "heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability",
                    filters: {
                        'capability': row.activity,
                        'disabled': 0
                    }
                };
        };
        // check if mud can be invoiced
        if (!frm.doc.__islocal) {
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
                frappe.route_options = {"from": cur_frm.doc.expected_start_date, "project_name": cur_frm.doc.name}
                frappe.set_route("bohrplaner");
            });
            // add button to open construction site description
            add_construction_site_description_button(frm, frm.doc.name);
            // show insurance information
            show_insurance_information(frm.doc.name);
        }
        
    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
    }
});
