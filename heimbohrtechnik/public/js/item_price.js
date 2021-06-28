frappe.ui.form.on('Item Price', {
    refresh(frm) {
        if (!frm.doc.base_rate) {
            cur_frm.set_value("base_rate", frm.doc.price_list_rate);
        }
    },
    base_rate(frm) {
        update_price_list_rate(frm);
    },
    cost_markup(frm) {
        update_price_list_rate(frm);
    }
});

function update_price_list_rate(frm) {
    if (frm.doc.base_rate) {
        var rate = frm.doc.base_rate * (((frm.doc.cost_markup || 0) + 100) / 100);
        cur_frm.set_value("price_list_rate", rate);
    }
}
