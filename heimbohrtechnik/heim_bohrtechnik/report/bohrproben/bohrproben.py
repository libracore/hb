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
		{"label": _("Project"), "fieldname": "name", "fieldtype": "Link", "options": "Project", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 80},
		{"label": _("Address"), "fieldname": "address", "fieldtype": "Data", "width": 200},
		{"label": _("Geology office"), "fieldname": "geology_office", "fieldtype": "Data", "width": 250},
		{"label": _("Storage location"), "fieldname": "storage_location", "fieldtype": "Data", "width": 100},
		{"label": _("Drilling samples distance"), "fieldname": "drilling_samples_all", "fieldtype": "Data", "width": 100},
		{"label": _("Custom drilling depth"), "fieldname": "custom_drilling_depth", "fieldtype": "Data", "width": 50},
		{"label": _("Condition of drill material (drill bags)"), "fieldname": "condition_of_drill_material__drill_bags", "fieldtype": "Data", "width": 80},
		{"label": _("Drilling master"), "fieldname": "drilling_master", "fieldtype": "Data", "width": 100},
		{"label": _("Geological expert"), "fieldname": "geological_expert", "fieldtype": "Data", "width": 100}
	]
	return columns

def get_data(filters):
    condition = """WHERE tabProject.expected_start_date <= '{end_date}' 
                   AND tabProject.expected_end_date >= '{start_date}'""".format(
                       start_date=filters.from_date, end_date=filters.to_date
                   )
    
    if filters.project:
        condition += """ AND `tabProject`.`name` = '{project}'""".format(project=filters.project)
    
    sql_query = """SELECT `tabProject`.`name`,
                          `tabDrilling Sample`.`status`,
                          (SELECT CONCAT(`tabObject`.`object_street`, ', ', `tabObject`.`plz`, ' ', `tabObject`.`city`)
                           FROM `tabObject`
                           WHERE `tabObject`.`name` = `tabProject`.`object`) AS `address`,
                          REPLACE(`tabObject Address`.`address_display`, '<br>', ', ') as `geology_office`,
                          `tabDrilling Sample`.`storage_location`,
                          `tabDrilling Sample`.`drilling_samples_all`,
                          `tabDrilling Sample`.`custom_drilling_depth`,
                          `tabDrilling Sample`.`condition_of_drill_material__drill_bags`,
                          `tabDrilling Sample`.`drilling_master`,
                          `tabDrilling Sample`.`geological_expert`
                   FROM `tabProject`
                   LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
                   LEFT JOIN `tabObject Address` ON `tabObject Address`.`parent` = `tabObject`.`name`
                   LEFT JOIN `tabDrilling Sample` ON `tabDrilling Sample`.`project` = `tabProject`.`name`
                   {condition}
                   AND `tabObject Address`.`address_type` = "Geologe"
                   ORDER BY `tabProject`.`creation` DESC""".format(condition=condition)
    
    data = frappe.db.sql(sql_query, as_dict=True)

    formatted_data = apply_styles(data)
    
    return formatted_data

def apply_styles(data):
    for row in data:
        if row['status'] == 'bestätigt':
            row['status'] = '<span style="color:green;">&#128994; ' + row['status'] + '</span>'
        elif row['status'] == 'erfasst':
            row['status'] = '<span style="color:orange;">&#128992; ' + row['status'] + '</span>'
    
    return data