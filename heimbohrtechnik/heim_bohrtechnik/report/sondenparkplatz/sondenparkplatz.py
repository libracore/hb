# Copyright (c) 2022, libracore AG and contributors
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
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 80},
        {"label": _("Purchase Order"), "fieldname": "purchase_order", "fieldtype": "Link", "options": "Purchase Order", "width": 80},
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 500},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Float", "width": 50},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]
    return columns

def get_data(filters):
    parking_project = frappe.get_value("Heim Settings", "Heim Settings", "sondenparkplatz")
    
    sql_query = """
        SELECT
            `tabPurchase Order`.`transaction_date` AS `date`,
            `tabPurchase Order`.`name` AS `purchase_order`,
            `tabPurchase Order Item`.`item_code` AS `item_code`,
            `tabPurchase Order Item`.`item_name` AS `item_name`,
            `tabPurchase Order Item`.`qty` AS `qty`
        FROM `tabPurchase Order Item` 
        LEFT JOIN `tabPurchase Order` ON `tabPurchase Order Item`.`parent` = `tabPurchase Order`.`name`
        WHERE 
            `tabPurchase Order`.`docstatus` = 1
            AND `tabPurchase Order Item`.`project` = "{parking}"
        ORDER BY `tabPurchase Order`.`transaction_date` ASC, `tabPurchase Order Item`.`idx` ASC;
    """.format(parking=parking_project)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
    
