frappe.ui.form.on('Payment Entry', {
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
        if (!frm.doc.tax_type) {
            set_tax_type(frm);
        }
    },
    party_type(frm) {
        set_tax_type(frm);
    }
});

function set_tax_type(frm) {
    if (frm.doc.party_type) {
        if (frm.doc.party_type === "Customer") {
            cur_frm.set_value("tax_type", "Sales Taxes and Charges Template");
        } else if (frm.doc.party_type === "Supplier") {
            cur_frm.set_value("tax_type", "Purchase Taxes and Charges Template");
        }
    }
}
