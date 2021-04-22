// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Checklist Activity', {
    refresh: function(frm) {
        cur_frm.fields_dict['party_type'].get_query = function(doc) {
            return {
                filters: [
                    ["name", "IN", ['Customer', 'Supplier']]
                ]
            }
        }
    }
});
