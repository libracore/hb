frappe.ui.form.on('Contact', {
    //~ refresh(frm) {
        //~ //
        //~ if (frm.doc.phone_nos) {
            //~ console.log("Hoi")
            //~ cur_frm.set_value('contact_phone.is_primary_phone', 1);
        //~ }
    //~ },
    before_save(frm) {
        // compile full name
        cur_frm.set_value("full_name", (frm.doc.first_name || "") + " " + (frm.doc.last_name || ""));
        // if hotel, set phone as primary
        'async'
        if (frm.doc.phone_nos.length > 0) {
            console.log(frm.doc.phone_nos.length);
            for (let i = 0; i < frm.doc.phone_nos.length; i++) {
                console.log("Maschineliiiiii");
            }
        }
    }
});
