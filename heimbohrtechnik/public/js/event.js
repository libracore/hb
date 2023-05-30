frappe.ui.form.on('Event', {
    refresh(frm) {
        if (frm.doc.__islocal) {
            // fresh document, check if routed from project
            if (localStorage.getItem("project")) {
                cur_frm.set_value("project", localStorage.getItem("project"));
                cur_frm.set_value("subject", "Besuchstermin " + localStorage.getItem("project"));
                frappe.call({
                    "method": "frappe.client.get",
                    "args": {
                        "doctype": "Project",
                        "name": localStorage.getItem("project")
                    },
                    "callback": function(response) {
                        var project = response.message;
                        var description = (project.object_name || "") + "<br>"
                            + (project.object_street || "") + "<br>"
                            + (project.object_location || "") + "<br>"
                            + "Kunde: " + (project.customer_name || "") + "<br>"
                            + "Auftrag: " + (project.sales_order || "") + "<br>";
                        cur_frm.set_value("description", description);
                    }
                });
            }
            if (localStorage.getItem("project_manager")) {
                cur_frm.set_value("project_manager", localStorage.getItem("project_manager"));
                var child = cur_frm.add_child('event_participants');
                frappe.model.set_value(child.doctype, child.name, 'reference_doctype', "User");
                frappe.model.set_value(child.doctype, child.name, 'reference_docname', localStorage.getItem("project_manager"));
                cur_frm.refresh_field('event_participants');
            }
        }
    }
});
