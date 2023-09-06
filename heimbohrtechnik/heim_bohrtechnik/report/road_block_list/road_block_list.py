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
        {"label": _("Strassensperrung"), "fieldname": "road_block", "fieldtype": "Link", "options": "Request for Public Area Use", "width": 90},
        {"label": _("Bohrteam"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 150},
        {"label": _("Objektname"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Strasse"), "fieldname": "street", "fieldtype": "Data", "width": 150},
        {"label": _("Ortschaft"), "fieldname": "location", "fieldtype": "Data", "width": 150},
        {"label": _("Bohrdatum Start"), "fieldname": "drilling_from_date", "fieldtype": "Date", "width": 90},
        {"label": _("Bohrdatum Ende"), "fieldname": "drilling_to_date", "fieldtype": "Date", "width": 90},
        {"label": _("Strassensperrung Start"), "fieldname": "road_block_from_date", "fieldtype": "Data", "width": 90},
        {"label": _("Strassensperrung Ende"), "fieldname": "road_block_to_date", "fieldtype": "Data", "width": 90}
    ]

def get_data(filters):
    
    # get all projects that have a road block in their checklist
    sql_query = """SELECT
            `tabProject`.`name` AS `project`,
            `tabProject`.`sales_order` AS `sales_order`,
            `tabRequest for Public Area Use`.`name` AS `road_block`,
            `tabProject`.`drilling_team` AS `drilling_team`,
            `tabObject`.`object_name` AS `object_name`,
            `tabObject`.`object_street` AS `street`,
            `tabObject`.`object_location` AS `location`,
            `tabProject`.`expected_start_date` AS `drilling_from_date`,
            `tabProject`.`expected_end_date` AS `drilling_to_date`,
            `tabRequest for Public Area Use`.`from_date` AS `road_block_from_date`,
            `tabRequest for Public Area Use`.`to_date` AS `road_block_to_date`
        FROM `tabProject Permit`
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabProject Permit`.`parent`
        LEFT JOIN `tabRelated Project` ON 
            (`tabRelated Project`.`project` = `tabProject`.`name` 
            AND `tabRelated Project`.`parenttype` = "Request for Public Area Use")
        LEFT JOIN `tabRequest for Public Area Use` ON 
            (`tabRequest for Public Area Use`.`project` = `tabProject`.`name`
            OR `tabRequest for Public Area Use`.`name` = `tabRelated Project`.`parent`) 
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
        WHERE 
            `tabProject Permit`.`permit` = "Strassensperrung"
            AND `tabProject`.`expected_start_date` >= "{from_date}"
        GROUP BY `tabProject`.`name`
        ORDER BY `tabProject`.`expected_start_date` ASC, `tabProject`.`start_half_day` DESC,`tabProject`.`drilling_team` ASC
    ;""".format(from_date=filters.from_date, project=filters.project)
    data = frappe.db.sql(sql_query, as_dict=True)

    #remove projects without Request for Public Area Use
    data = [d for d in data if not (d.get('road_block') == None)]

    # color issues
    for d in data:
        # mark drilling before permit red
        road_block_from_str = d['road_block_from_date'].strftime("%d.%m.%Y") if d['road_block_from_date'] else ""
        if d['drilling_from_date'] and d['road_block_from_date'] and d['drilling_from_date'] < d['road_block_from_date']:
            d['road_block_from_date'] = "<span style='color: red; '>{0}</span>".format(road_block_from_str)
        else:
            d['road_block_from_date'] = "<span style='color: darkgreen; '>{0}</span>".format(road_block_from_str)
        # mark drilling after permit
        road_block_to_str = d['road_block_to_date'].strftime("%d.%m.%Y") if d['road_block_to_date'] else ""
        if d['drilling_to_date'] and d['road_block_to_date'] and d['drilling_to_date'] > d['road_block_to_date']:
            d['road_block_to_date'] = "<span style='color: red; '>{0}</span>".format(road_block_to_str)
        else:
            d['road_block_to_date'] = "<span style='color: darkgreen; '>{0}</span>".format(road_block_to_str)
            
    return data
