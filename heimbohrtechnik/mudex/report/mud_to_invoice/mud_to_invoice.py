# Copyright (c) 2021, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()

    data = get_data()
    return columns, data

def get_columns():
    return [
        {"label": _("Object"), "fieldname": "object", "fieldtype": "Link", "options": "Object", "width": 120},
        {"label": _("Object name"), "fieldname": "object_name", "fieldtype": "Data", "width": 200},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 100},
        #{"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 100},
        #{"label": _("Customer name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": _("Expected End Date"), "fieldname": "expected_end_date", "fieldtype": "Date", "width": 250},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def get_data():
    sql_query = """
        SELECT 
            `tabTruck Delivery Object`.`object` AS `object`,
            `tabProject`.`name` AS `project`,
            SUM(`tabTruck Delivery Object`.`weight`) AS `qty`,
            `tabProject`.`expected_end_date` AS `expected_end_date`,
            `tabObject`.`object_name` AS `object_name`
        FROM `tabTruck Delivery Object`
        LEFT JOIN `tabTruck Delivery` ON `tabTruck Delivery`.`name` = `tabTruck Delivery Object`.`parent`
        LEFT JOIN `tabSales Invoice Item` ON 
            (`tabTruck Delivery Object`.`name` = `tabSales Invoice Item`.`truck_delivery_detail`
             AND `tabSales Invoice Item`.`docstatus` = 1)
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabTruck Delivery Object`.`object`
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabTruck Delivery Object`.`object`
        WHERE `tabTruck Delivery`.`docstatus` = 1
          AND `tabSales Invoice Item`.`name` IS NULL
        GROUP BY `tabTruck Delivery Object`.`object`
        ORDER BY `tabProject`.`expected_end_date` ASC;""" 
    data = frappe.db.sql(sql_query, as_dict = True)
    
    return data
