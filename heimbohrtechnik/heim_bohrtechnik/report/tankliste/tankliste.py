# Copyright (c) 2024, libracore AG and contributors
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
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Link"), "fieldname": "name", "fieldtype": "Link", "options": "Gas Receipt", "width": 100},
        {"label": _("Drilling Team"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 150},
        {"label": _("Truck"), "fieldname": "truck", "fieldtype": "Link", "options": "Truck", "width": 90},
        {"label": _("Kilometer"), "fieldname": "kilometer", "fieldtype": "Int", "width": 80},
        {"label": _("Liter"), "fieldname": "liter", "fieldtype": "Float", "width": 80},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "options": "currency", "width": 80}
    ]

def get_data(filters):
    conditions = ""
    if filters.get("truck"):
        conditions += """ AND `tabGas Receipt`.`truck` = "{truck}" """.format(truck=filters.get("truck"))
    if filters.get("drilling_team"):
        conditions += """ AND `tabGas Receipt`.`drilling_team` = "{drilling_team}" """.format(drilling_team=filters.get("drilling_team"))
    
    # get matching gas receipts
    sql_query = """
        SELECT 
            `tabGas Receipt`.`date` AS `date`,
            `tabGas Receipt`.`name` AS `name`,
            `tabGas Receipt`.`drilling_team` AS `drilling_team`,
            `tabGas Receipt`.`truck` AS `truck`,
            `tabGas Receipt`.`kilometer` AS `kilometer`,
            `tabGas Receipt`.`liter` AS `liter`,
            `tabGas Receipt`.`amount` AS `amount`,
            `tabGas Receipt`.`currency` AS `currency`
        FROM `tabGas Receipt`
        WHERE `tabGas Receipt`.`date` BETWEEN "{from_date}" AND "{to_date}"
            {conditions}
        ORDER BY `tabGas Receipt`.`date`;
    """.format(from_date=filters.from_date, to_date=filters.to_date, conditions=conditions)
    data = frappe.db.sql(sql_query, as_dict=True)

    return data
