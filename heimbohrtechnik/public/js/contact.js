frappe.ui.form.on('Contact', {
    before_save(frm) {
        // compile full name
        cur_frm.set_value("full_name", (frm.doc.first_name || "") + " " + (frm.doc.last_name || ""));
        // set first phone number as primary
        var has_primary = false;
        if ((frm.doc.phone_nos) && (frm.doc.phone_nos.length > 0)) {
            for (var i = 0; i < frm.doc.phone_nos.length; i++) {
                if (frm.doc.phone_nos[i].is_primary_phone === 1) {
                    has_primary = true;
                }
            }
            if (has_primary === false) {
                frappe.model.set_value(cur_frm.doc.phone_nos[0].doctype, cur_frm.doc.phone_nos[0].name, "is_primary_phone", 1);
            }
        }
    }
});
