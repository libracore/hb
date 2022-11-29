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
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 250},
        {"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 80},
        {"label": _("Sales Order"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 80},
        {"label": _("Net Amount"), "fieldname": "net_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 150},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]
    return columns

def get_data(filters):
    conditions = ""
    if filters.get('sales_order'):
        conditions = """AND `tabSales Invoice Item`.`sales_order` = "{0}" """.format(filters.get('sales_order'))
    
    sql_query = """
        SELECT
            `tabSales Invoice`.`posting_date` AS `date`,
            `tabSales Invoice`.`customer` AS `customer`,
            `tabSales Invoice`.`customer_name` AS `customer_name`,
            `tabSales Invoice`.`name` AS `sales_invoice`,
            `tabSales Invoice`.`net_total` AS `net_amount`,
            `tabSales Invoice`.`grand_total` AS `amount`,
            `tabSales Invoice`.`status` AS `status`,
            `tabSales Invoice Item`.`sales_order` AS `sales_order`,
            `tabSales Invoice Item`.`name` AS `reference`
        FROM `tabSales Invoice` 
        LEFT JOIN `tabSales Invoice Item` ON `tabSales Invoice Item`.`parent` = `tabSales Invoice`.`name`
        LEFT JOIN `tabDiscount Position` ON (
            `tabDiscount Position`.`akonto_invoice_item` = `tabSales Invoice Item`.`name`
            AND `tabDiscount Position`.`docstatus` < 2
        )
        WHERE 
            `tabSales Invoice`.`docstatus` = 1
            AND `tabSales Invoice Item`.`item_code` = "{akonto_item}"
            AND `tabDiscount Position`.`name` IS NULL
            {conditions}
        GROUP BY `tabSales Invoice`.`name`
        ORDER BY `tabSales Invoice`.`posting_date` ASC;
    """.format(akonto_item=frappe.get_value("Heim Settings", "Heim Settings", "akonto_item"), conditions=conditions)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
    
