frappe.ui.form.on('Contact', {
    before_save(frm) {
        // compile full name
        cur_frm.set_value("full_name", (frm.doc.first_name || "") + " " + (frm.doc.last_name || ""));
        // if hotel, set phone as primary
        'async'
        let primary = false;
        if (frm.doc.phone_nos.length > 0) {
            for (const number of frm.doc.phone_nos) {
                if (number.is_primary_phone == 1) {
                    primary = true;
                }
            }
            if (primary == false) {
                frappe.call({
                    'method': 'heimbohrtechnik.heim_bohrtechnik.contact.get_supplier',
                    'args': {
                        'supplier': frm.doc.links[0].link_name
                    },
                    'callback': function(response) {
                        var supplier_dict = response.message;
                        var link = frm.doc.name;
                        if (supplier_dict.supplier_group == "Hotel") {
                            frappe.model.set_value(cur_frm.doc.phone_nos[0].doctype, cur_frm.doc.phone_nos[0].name, "is_primary_phone", 1);
                        }
                    }
                });
            }
        }
    }
});
