frappe.ui.form.on('Contact', {
    before_save(frm) {
        // compile full name
        cur_frm.set_value("full_name", (frm.doc.first_name || "") + " " + (frm.doc.last_name || ""));
        // if hotel, set phone as primary
        var primary = false;
        if (frm.doc.phone_nos.length > 0) {
            for (const number of frm.doc.phone_nos) {
                if (number.is_primary_phone == 1) {
                    primary = true;
                }
            }
            if (primary == false) {
                frappe.call({
                    'method': 'frappe.client.get',
                    'args': {
                        'doctype': "Supplier"
                        'name': frm.doc.links[0].link_name
                    },
                    'async': false,
                    'callback': function(response) {
                        var supplier = response.message;
                        var link = frm.doc.name;
                        if (supplier.supplier_group == "Hotel") {
                            frappe.model.set_value(cur_frm.doc.phone_nos[0].doctype, cur_frm.doc.phone_nos[0].name, "is_primary_phone", 1);
                        }
                    }
                });
            }
        }
    }
});
