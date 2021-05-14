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

    }
});

frappe.ui.form.on('Project Checklist', {
    supplier: function(frm, dt, dn) {
        get_required_activities(frm, dt, dn);
    }
});
