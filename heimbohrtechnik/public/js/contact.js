frappe.ui.form.on('Contact', {
    before_save(frm) {
        // compile full name
        cur_frm.set_value("full_name", (frm.doc.first_name || "") + " " + (frm.doc.last_name || ""));
    }
});
