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
    columns = [
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"label": _("BKP"), "fieldname": "bkp_group", "fieldtype": "Link", "options": "BKP Group", "width": 50},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 300},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 300},
        {"label": _("Price List Rate"), "fieldname": "price_list_rate", "fieldtype": "Float", "precision": 2, "width": 75},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]
    return columns

def get_data(filters):
    conditions = ""
    if filters.item_group:
        conditions += """ AND `tabItem`.`item_Group` = "{item_group}" """.format(item_group=filters.item_group)
    if filters.item_code:
        conditions += """ AND `tabItem`.`item_code` LIKE "{item_code}%" """.format(item_code=filters.item_code)
    if filters.bkp_group:
        conditions += """ AND `tabItem`.`bkp` = "{bkp_group}" """.format(bkp_group=filters.bkp_group)
    sql_query = """SELECT 
            `tabItem`.`item_group` AS `item_group`,
            `tabItem`.`bkp` AS `bkp_group`,
            `tabItem`.`item_code` AS `item_code`,
            `tabItem`.`item_name` AS `item_name`,
            `tabItem Price`.`price_list_rate` AS `price_list_rate`
        FROM `tabItem`
        LEFT JOIN `tabItem Price` ON `tabItem`.`item_code` = `tabItem Price`.`item_code` AND
            `tabItem Price`.`price_list` = "{price_list}"
        WHERE 
            `tabItem`.`disabled` = 0
            AND `tabItem`.`is_sales_item` = 1
            {conditions}
        ORDER BY `tabItem`.`item_code` ASC;""".format(conditions=conditions, price_list=filters.price_list)      
    data = frappe.db.sql(sql_query, as_dict = True)
    return data
