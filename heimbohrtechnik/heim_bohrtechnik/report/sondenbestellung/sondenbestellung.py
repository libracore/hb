# Copyright (c) 2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {"label": _("Projekt"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 85},
        {"label": _("Objekt"), "fieldname": "project", "fieldtype": "Link", "options": "Object", "width": 75},
        {"label": _("Kundenauftrag"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 90},
        {"label": _("Bestellung"), "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 90},
        {"label": _("Bohrteam"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 150},
        {"label": _("Objektname"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Bohrdatum"), "fieldname": "drilling_date", "fieldtype": "Date", "width": 90},
        {"label": _("Sonden"), "fieldname": "probes", "fieldtype": "Data", "width": 300}

    ]

def get_data(filters):
    conditions = ""
    if cint(filters.show_all) == 0:
        conditions = """ AND `tabPurchase Order Item`.`name` IS NULL """
        
    # get all projects wihout probe purchase orders
    sql_query = """SELECT
            `tabProject`.`name` AS `project`,
            `tabSales Order`.`name` AS `sales_order`,
            `tabPurchase Order`.`name` AS `purchase_order`,
            `tabObject`.`name` AS `object`,
            `tabProject`.`drilling_team` AS `drilling_team`,
            `tabObject`.`object_name` AS `object_name`,
            `tabProject`.`expected_start_date` AS `drilling_date`,
            0 AS `indent`,
            IF(`tabPurchase Order Item`.`name` IS NULL, "bestellen", "") AS `probes`
        FROM `tabProject`
        LEFT JOIN `tabSales Order` ON `tabSales Order`.`name` = `tabProject`.`sales_order`
        LEFT JOIN `tabPurchase Order` ON `tabPurchase Order`.`object` = `tabProject`.`object`
        LEFT JOIN `tabPurchase Order Item` ON 
            (`tabPurchase Order Item`.`parent` = `tabPurchase Order`.`name`
             AND `tabPurchase Order Item`.`item_code` LIKE "1.02.01.01%")
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
        WHERE 
            `tabProject`.`expected_start_date` >= "{from_date}"
            AND `tabProject`.`expected_start_date` <= "{to_date}"
            {conditions}
        GROUP BY `tabProject`.`name`
        ORDER BY `tabProject`.`drilling_team` ASC, `tabProject`.`expected_start_date` ASC, `tabProject`.`name` ASC
    ;""".format(from_date=filters.from_date, to_date=filters.to_date, conditions=conditions)
    data = frappe.db.sql(sql_query, as_dict=True)
    
    # add drill-down for probes
    output = []
    for d in data:
        output.append(d)
        sql_query = """
            SELECT
                `ews_count`,
                `ews_depth`,
                `ews_wall_strength`,
                `ews_diameter`,
                `ews_diameter_unit`,
                `pressure_level`,
                `probe_type`,
                `ews_material`
            FROM `tabObject EWS`
            WHERE `parent` = "{object}";
        """.format(object=d['object'])
        probes = frappe.db.sql(sql_query, as_dict=True)
        for p in probes:
            output.append({
                'indent': 1,
                'probes': "{count}x {depth}m {diameter}x{wall_strength} {unit} ({pressure_level}, {material})".format(
                    count=p['ews_count'],
                    depth=p['ews_depth'],
                    diameter=p['ews_diameter'],
                    wall_strength=p['ews_wall_strength'],
                    unit=p['ews_diameter_unit'],
                    pressure_level=p['pressure_level'],
                    material=p['ews_material'])
            })
            
    return output
