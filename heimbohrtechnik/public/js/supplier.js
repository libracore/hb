frappe.ui.form.on('Supplier', {
    setup(frm) {
        frm.set_query('default_sales_taxes_and_charges', 'accounts', function(doc, cdt, cdn) {
            var d = locals[cdt][cdn];
            var filters = {
                'company': d.company
            }
            return {'filters': filters}
        });
        frm.set_query('default_purchase_taxes_and_charges', 'accounts', function(doc, cdt, cdn) {
            var d = locals[cdt][cdn];
            var filters = {
                'company': d.company
            }
            return {'filters': filters}
        });
    },
    before_save(frm) {
        if (!frm.doc.__islocal) {
            set_first_address(frm);
        }
        compile_remarks(frm);
    }
});

function set_first_address(frm) {
    frappe.call({
        'method': 'erpnextswiss.scripts.crm_tools.get_primary_supplier_address',
        'args': {
            'supplier': frm.doc.name
        },
        'async': false,
        'callback': function(response) {
            if (response.message) {
                var address = response.message;
                var adr_line = address.address_line1 + ", " + address.pincode + " " + address.city;
                cur_frm.set_value('hauptadresse', adr_line);
            }
        }
    });
}

function compile_remarks(frm) {
    if (frm.doc.capabilities) {
        var remarks = [];
        for (var i = 0; i < frm.doc.capabilities.length; i++) {
            if (frm.doc.capabilities[i].remarks) {
                remarks.push(frm.doc.capabilities[i].remarks);
            }
        }
        cur_frm.set_value("remarks", remarks.join(", "));
    }
}
