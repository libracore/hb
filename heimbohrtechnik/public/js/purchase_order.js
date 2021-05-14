// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Order', {
    object: function(frm) {
        get_object_address(frm);
    }
});
