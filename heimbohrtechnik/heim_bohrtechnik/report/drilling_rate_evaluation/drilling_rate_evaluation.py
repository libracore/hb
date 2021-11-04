# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": _("Object"), "fieldname": "object", "fieldtype": "Link", "options": "Object", "width": 100},
        {"label": _("Object Name"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Street"), "fieldname": "object_street", "fieldtype": "Data", "width": 150},
        {"label": _("Location"), "fieldname": "object_location", "fieldtype": "Data", "width": 150},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 150},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Overall Rate"), "fieldname": "overall_rate", "fieldtype": "Currency", "width": 100}
    ]
    return columns

def get_data(filters):
    item = frappe.get_value("Heim Settings", "Heim Settings", "drilling_item")
    conditions = ""
    if filters.object:
        conditions += """ AND `tabObject`.`name` = "{object}" """.format(object=filters.object)
    if filters.street:
        conditions += """ AND `tabObject`.`object_street` LIKE "%{street}%" """.format(street=filters.street)
    if filters.location:
        conditions += """ AND `tabObject`.`object_location` LIKE "%{location}%" """.format(location=filters.location)
    sql_query = """SELECT 
            `tabQuotation`.`object` AS `object`,
            `tabObject`.`object_name` AS `object_name`,
            `tabObject`.`object_street` AS `object_street`,
            `tabObject`.`object_location` AS `object_location`,
            `tabQuotation`.`transaction_date` AS `date`,
            `tabQuotation Item`.`rate` AS `rate`,
            (`tabQuotation`.`conditional_net_total` / `tabQuotation Item`.`qty`) AS `overall_rate`
        FROM `tabQuotation Item`
        LEFT JOIN `tabQuotation` ON `tabQuotation Item`.`parent` = `tabQuotation`.`name`
        LEFT JOIN `tabObject` ON `tabQuotation`.`object` = `tabObject`.`name`
        WHERE 
            `tabQuotation Item`.`item_code` = "{item}"
            AND `tabQuotation`.`docstatus` = 1
            {conditions};""".format(item=item, conditions=conditions)      
    data = frappe.db.sql(sql_query, as_dict = True)
    return data
