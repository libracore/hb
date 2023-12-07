# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {"label": _("Projekt"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 85},
        {"label": _("Auftrag"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 90},
        {"label": _("Bohrteam"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 150},
        {"label": _("Objektname"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Strasse"), "fieldname": "street", "fieldtype": "Data", "width": 150},
        {"label": _("Ortschaft"), "fieldname": "location", "fieldtype": "Data", "width": 150},
        {"label": _("Bohrdatum Start"), "fieldname": "drilling_from_date", "fieldtype": "Date", "width": 90},
        {"label": _("Bohrdatum Ende"), "fieldname": "drilling_to_date", "fieldtype": "Date", "width": 90},
        {"label": _("Materialauftrag"), "fieldname": "material_order", "fieldtype": "Link", "options": "Road Block Material Order", "width": 90},
        {"label": _("Materialdatum"), "fieldname": "material_date", "fieldtype": "Date", "width": 90}
    ]

def get_data(filters):
    
    # get all projects that require road block material
    sql_query = """SELECT
            `tabProject`.`name` AS `project`,
            `tabProject`.`sales_order` AS `sales_order`,
            `tabProject`.`drilling_team` AS `drilling_team`,
            `tabObject`.`object_name` AS `object_name`,
            `tabObject`.`object_street` AS `street`,
            `tabObject`.`object_location` AS `location`,
            `tabProject`.`expected_start_date` AS `drilling_from_date`,
            `tabProject`.`expected_end_date` AS `drilling_to_date`,
            `tabRoad Block Material Order`.`name` AS `material_order`,
            `tabRoad Block Material Order`.`from_date` AS `material_date`
        FROM `tabConstruction Site Description`
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabConstruction Site Description`.`project`
        LEFT JOIN `tabRelated Project` ON 
            (`tabRelated Project`.`project` = `tabProject`.`name` 
            AND `tabRelated Project`.`parenttype` = "Request for Public Area Use")
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
        LEFT JOIN `tabRoad Block Material Order` ON 
            `tabRoad Block Material Order`.`project` = `tabProject`.`name`
        WHERE 
            `tabConstruction Site Description`.`road_block_required` = 1
            AND `tabProject`.`expected_start_date` >= "{from_date}"
        GROUP BY `tabProject`.`name`
        ORDER BY `tabProject`.`expected_start_date` ASC, `tabProject`.`start_half_day` DESC,`tabProject`.`drilling_team` ASC
    ;""".format(from_date=filters.from_date)
    data = frappe.db.sql(sql_query, as_dict=True)
            
    return data
