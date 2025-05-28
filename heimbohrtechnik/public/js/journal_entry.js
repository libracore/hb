frappe.ui.form.on('Journal Entry', {
    refresh(frm) {
        // filters
        cur_frm.fields_dict['tax_type'].get_query = function(frm) {
            return {
                filters: [
                    ["name", "IN", ["Sales Taxes and Charges Template", "Purchase Taxes and Charges Template"]]
                ]
            }
        };
        cur_frm.fields_dict['taxes_and_charges'].get_query = function(doc) {
            return {
                filters: {
                    "company": doc.company
                }
            }
        };
    }
});
