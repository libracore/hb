# Copyright (c) 2023-2024, libracore AG and contributors
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
        {"label": _("Verlängerungsauftrag"), "fieldname": "subcontracting_order", "fieldtype": "Link", "options": "Subcontracting Order", "width": 90},
        {"label": _("Bohrteam"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 150},
        {"label": _("Objektname"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Strasse"), "fieldname": "street", "fieldtype": "Data", "width": 150},
        {"label": _("Ortschaft"), "fieldname": "location", "fieldtype": "Data", "width": 150},
        {"label": _("Bohrdatum Start"), "fieldname": "drilling_from_date", "fieldtype": "Date", "width": 90},
        {"label": _("Bohrdatum Ende"), "fieldname": "drilling_to_date", "fieldtype": "Date", "width": 90},
        {"label": _("Verlängerungsauftrag Start"), "fieldname": "subcontracting_from_date", "fieldtype": "Data", "width": 90},
        {"label": _("Verlängerungsauftrag Ende"), "fieldname": "subcontracting_to_date", "fieldtype": "Data", "width": 90}
    ]

def get_data(filters):
    
    # get all subcontracting orders
    sql_query = """SELECT
            `tabProject`.`name` AS `project`,
            `tabProject`.`sales_order` AS `sales_order`,
            `tabSubcontracting Order`.`name` AS `subcontracting_order`,
            `tabSubcontracting Order`.`drilling_team` AS `drilling_team`,
            `tabObject`.`object_name` AS `object_name`,
            `tabObject`.`object_street` AS `street`,
            `tabObject`.`object_location` AS `location`,
            `tabProject`.`expected_start_date` AS `drilling_from_date`,
            `tabProject`.`expected_end_date` AS `drilling_to_date`,
            `tabSubcontracting Order`.`from_date` AS `subcontracting_from_date`,
            `tabSubcontracting Order`.`to_date` AS `subcontracting_to_date`
        FROM `tabSubcontracting Order`
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabSubcontracting Order`.`project`
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
        WHERE 
            (`tabSubcontracting Order`.`from_date` BETWEEN "{from_date}" AND "{to_date}"
            OR `tabSubcontracting Order`.`to_date` BETWEEN "{from_date}" AND "{to_date}")
        /* GROUP BY `tabProject`.`name` */
        ORDER BY `tabProject`.`expected_start_date` ASC, `tabProject`.`start_half_day` DESC,`tabProject`.`drilling_team` ASC
    ;""".format(from_date=filters.from_date, to_date=filters.to_date)
    data = frappe.db.sql(sql_query, as_dict=True)

    # color issues
    for d in data:
        # mark subcontracting before drilling red
        subcontracting_from_str = d['subcontracting_from_date'].strftime("%d.%m.%Y") if d['subcontracting_from_date'] else ""
        if d['drilling_to_date'] and d['subcontracting_from_date'] and d['drilling_to_date'] > d['subcontracting_from_date']:
            d['subcontracting_from_date'] = "<span style='color: red; '>{0}</span>".format(subcontracting_from_str)
        else:
            d['subcontracting_from_date'] = "<span style='color: darkgreen; '>{0}</span>".format(subcontracting_from_str)
        
        subcontracting_to_str = d['subcontracting_to_date'].strftime("%d.%m.%Y") if d['subcontracting_to_date'] else ""
        d['subcontracting_to_date'] = "<span>{0}</span>".format(subcontracting_to_str)
    return data
