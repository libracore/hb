// Copyright (c) 2021-2022, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Invoice', {
    before_save: function(frm) {
        if (frm.doc.object) {
            set_project(frm);
        }
    }
});

function set_project(frm) {
    // check if there is a project for this object and set it
    console.log("set project");
    frappe.call({
        'method': 'frappe.client.get_list',
        'args': {
            'doctype': 'Project',
            'filters': [
                ['name', '=', frm.doc.object]
            ],
            'fields': ['name'],
        },
        'async': false,
        'callback': function(response) {
            if ((response.message) && (response.message.length > 0)) {
                var project = response.message[0]['name'];
                for (var i = 0; i < frm.doc.items.length; i++) {
                    console.log("set " + i + ": " + project);
                    frappe.model.set_value(frm.doc.items[i].doctype, frm.doc.items[i].name, 'project', project);
                }
            }
        }
    });
}
