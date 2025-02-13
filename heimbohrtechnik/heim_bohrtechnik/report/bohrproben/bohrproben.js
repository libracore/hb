// Copyright (c) 2025, libracore AG and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bohrproben"] = {
	"filters": [
		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project"
		}
	]		
};
