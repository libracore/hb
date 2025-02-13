# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		{"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Address"), "fieldname": "address", "fieldtype": "Data", "width": 200},
		{"label": _("Geology office name"), "fieldname": "geology_office_name", "fieldtype": "Data", "width": 150},
		{"label": _("Storage location"), "fieldname": "storage_location", "fieldtype": "Data", "width": 100},
		{"label": _("Drilling samples distance"), "fieldname": "drilling_samples_all", "fieldtype": "Data", "width": 100},
		{"label": _("Custom drilling depth"), "fieldname": "custom_drilling_depth", "fieldtype": "Data", "width": 50},
		{"label": _("Condition of drill material (drill bags)"), "fieldname": "condition_of_drill_material__drill_bags", "fieldtype": "Data", "width": 80},
		{"label": _("Drilling master"), "fieldname": "drilling_master", "fieldtype": "Data", "width": 100},
		{"label": _("Geological expert"), "fieldname": "geological_expert", "fieldtype": "Data", "width": 100}
	]
	return columns

def get_data(filters):
	sql_query = """SELECT `project`,
							`status`,
							`address`,
							`geology_office_name`,
							`storage_location`,
							`drilling_samples_all`,
							`custom_drilling_depth`,
							`condition_of_drill_material__drill_bags`,
							`drilling_master`,
							`geological_expert`
				FROM `tabDrilling Sample`
				WHERE `project` = '{project}'
				ORDER BY `creation` DESC""".format(project=filters.project)
	
	data = frappe.db.sql(sql_query, as_dict = True)
	return data
