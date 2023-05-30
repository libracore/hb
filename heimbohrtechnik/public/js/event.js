frappe.ui.form.on('Event', {
    refresh(frm) {
        if (frm.doc.__islocal) {
            // fresh document, check if routed from project
            if (localStorage.getItem("project")) {
                cur_frm.set_value("project", localStorage.getItem("project"));
            }
            if (localStorage.getItem("project_manager")) {
                cur_frm.set_value("project_manager", localStorage.getItem("project_manager"));
            }
        }
    }
});
