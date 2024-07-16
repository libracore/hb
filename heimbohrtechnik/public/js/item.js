frappe.ui.form.on('Item', {
    before_save(frm) {
        // weight is always kg
        cur_frm.set_value("weight_uom", "kg");
        if (frm.doc.gewicht) {
            cur_frm.set_value("weight_per_unit", frm.doc.gewicht);
        } else if (frm.doc.weight_per_unit) {
            cur_frm.set_value("gewicht", frm.doc.weight_per_unit);
        }
    },
    refresh: function(frm) {
        frm.add_custom_button(__("Klein"), function() {
            create_label(frm, "small");
        },__("Etikette erstellen")); 
        frm.add_custom_button(__("Gross"), function() {
            create_label(frm, "big");
        },__("Etikette erstellen"));  
    }
});

function create_label(frm, label_type) {
    // html-content of the label - price label
    var url = "/api/method/heim_bohrtechnik.heim_bohrtechnik.labels.get_labels"  
            + "?item=" + encodeURIComponent(frm.doc.name) + "?label_type=" + label_type;
    var w = window.open(
            frappe.urllib.get_full_url(url)
    );
    if (!w) {
        frappe.msgprint(__("Please enable pop-ups"));
        return;  
    }
}
