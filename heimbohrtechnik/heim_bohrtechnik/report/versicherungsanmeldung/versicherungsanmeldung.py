# Copyright (c) 2022, libracore AG and contributors
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
        {"label": _("Projekt"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 75},
        {"label": _("Kundenauftrag"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 90},
        {"label": _("Objektname"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Strasse"), "fieldname": "street", "fieldtype": "Data", "width": 150},
        {"label": _("PLZ, Ort"), "fieldname": "location", "fieldtype": "Data", "width": 150},
        {"label": _("Kunde"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Strasse"), "fieldname": "customer_street", "fieldtype": "Data", "width": 150},
        {"label": _("Kunden-PLZ, Ort"), "fieldname": "customer_location", "fieldtype": "Data", "width": 150},
        {"label": _("Land"), "fieldname": "country", "fieldtype": "Data", "width": 70},
        {"label": _("Bohrdatum"), "fieldname": "drilling_date", "fieldtype": "Date", "width": 90},
        {"label": _("Anzahlungen Bohrungen"), "fieldname": "drill_count", "fieldtype": "Int", "width": 150},
        {"label": _("Anzahl Bohrungen < 250m"), "fieldname": "drill_count_light", "fieldtype": "Int", "width": 150},
        {"label": _("Anzahl Bohrungen > 250m"), "fieldname": "drill_count_deep", "fieldtype": "Int", "width": 150},
        {"label": _("Versicherungen"), "fieldname": "insurances", "fieldtype": "Data", "width": 500}
    ]

def get_data(filters):
        
    sql_query = """SELECT
            `tabProject`.`name` AS `project`,
            `tabSales Order`.`name` AS `sales_order`,
            `tabProject`.`expected_start_date` AS `drilling_date`,
            GROUP_CONCAT(`tabSales Order Item`.`item_name`) AS `insurances`,
            `tabObject`.`object_name` AS `object_name`,
            `tabObject`.`object_street` AS `street`,
            `tabObject`.`object_location` AS `location`,
            `tabSales Order`.`customer_name` AS `customer_name`,
            `tabAddress`.`address_line1` AS `customer_street`,
            CONCAT(`tabAddress`.`pincode`, " ", `tabAddress`.`city`) AS `customer_location`,
            `tabAddress`.`country` AS `country`,
            (SELECT IFNULL(SUM(`tabObject EWS`.`ews_count`), 0)
             FROM `tabObject EWS` 
             WHERE `tabObject EWS`.`parent` = `tabObject`.`name`) AS `drill_count`,
            (SELECT IFNULL(SUM(`tabObject EWS`.`ews_count`), 0)
             FROM `tabObject EWS` 
             WHERE `tabObject EWS`.`parent` = `tabObject`.`name`
               AND `tabObject EWS`.`ews_depth` <= 250) AS `drill_count_light`,
            (SELECT IFNULL(SUM(`tabObject EWS`.`ews_count`), 0)
             FROM `tabObject EWS` 
             WHERE `tabObject EWS`.`parent` = `tabObject`.`name`
               AND `tabObject EWS`.`ews_depth` > 250) AS `drill_count_deep`
        FROM `tabProject`
        LEFT JOIN `tabSales Order` ON `tabSales Order`.`name` = `tabProject`.`sales_order`
        LEFT JOIN `tabSales Order Item` ON 
            (`tabSales Order Item`.`parent` = `tabSales Order`.`name`
             AND `tabSales Order Item`.`item_name` LIKE "%Versicherung%")
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
        LEFT JOIN `tabAddress` ON `tabAddress`.`name` = `tabSales Order`.`customer_address`
        WHERE 
            `tabProject`.`expected_start_date` >= "{from_date}"
            AND `tabProject`.`expected_start_date` <= "{to_date}"
            AND `tabSales Order Item`.`name` IS NOT NULL
        GROUP BY `tabProject`.`name`
        ORDER BY `tabProject`.`expected_start_date` ASC, `tabProject`.`name` ASC
    ;""".format(from_date=filters.from_date, to_date=filters.to_date)
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
