// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Drilling Sample', {
	refresh: function(frm) {
		toggle_drilling_depth(frm);
	},
	"project": function(frm) {
		fetch_project_data(frm);
	},
	"drilling_samples_all": function(frm) {
		toggle_drilling_depth(frm);
	}
});

function fetch_project_data(frm) {
	frappe.call({
		method: 'heimbohrtechnik.heim_bohrtechnik.doctype.drilling_sample.drilling_sample.fetch_project_data',
		args: {
			"project_name": frm.doc.project
		},
		callback: function(response) {
			var project_data = response.message;
			if (project_data) {
				console.log(project_data);
				frm.set_value('object', project_data.object);
				frm.set_value('address', project_data.address);
				frm.set_value('geology_office_name', project_data.geology_office_name);
				frm.set_value('geology_office', project_data.geology_office);
			}
		}
	});
}

function toggle_drilling_depth(frm) {
	if (frm.doc.drilling_samples_all == "benutzerdefiniert") {
		frm.set_df_property('custom_drilling_depth', 'hidden', false);
	} else {
		frm.set_df_property('custom_drilling_depth', 'hidden', true);
	}
}