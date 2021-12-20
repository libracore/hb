frappe.ui.form.on('Item', {
    before_save(frm) {
        // weight is always kg
        cur_frm.set_value("weight_uom", "kg");
        if (frm.doc.gewicht) {
            cur_frm.set_value("weight_per_unit", frm.doc.gewicht);
        } else if (frm.doc.weight_per_unit) {
            cur_frm.set_value("gewicht", frm.doc.weight_per_unit);
        }
    }
});
