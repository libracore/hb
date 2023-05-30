# Copyright (c) 2023, libracore AG and contributors
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
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
        {"label": _("Address"), "fieldname": "address", "fieldtype": "Data", "width": 250},
        {"label": _("Quotations"), "fieldname": "qtns", "fieldtype": "Int", "width": 100},
        {"label": _("Quotation Volume"), "fieldname": "qtn_volume", "fieldtype": "Currency", "width": 120},
        {"label": _("Sales Orders"), "fieldname": "sos", "fieldtype": "Int", "width": 100},
        {"label": _("Sales Order Volume"), "fieldname": "so_volume", "fieldtype": "Currency", "width": 120},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]
    return columns

def get_data(filters):
    sql_query = """
        SELECT
            `raw`.`customer`,
            `raw`.`customer_name`,
            `raw`.`address`,
            COUNT(`raw`.`quotation`) AS `qtns`,
            SUM(`raw`.`qtn_base_net_total`) AS `qtn_volume`,
            COUNT(`raw`.`sales_order`) AS `sos`,
            SUM(`raw`.`so_base_net_total`) AS `so_volume`
        FROM (
            SELECT
                `tabCustomer`.`name` AS `customer`,
                `tabCustomer`.`customer_name` AS `customer_name`,
                (SELECT CONCAT(`tabAddress`.`address_line1`, ", ", `tabAddress`.`pincode`, " ", `tabAddress`.`city`)
                 FROM `tabDynamic Link` 
                 LEFT JOIN `tabAddress` ON `tabAddress`.`name` = `tabDynamic Link`.`parent`
                 WHERE  `tabDynamic Link`.`link_doctype` = "Customer"
                       AND `tabDynamic Link`.`link_name` = `tabCustomer`.`name`
                       AND `tabDynamic Link`.`parenttype` = "Address"
                ORDER BY `tabAddress`.`is_primary_address` DESC
                LIMIT 1
                ) AS `address`,
                `tabQuotation`.`name` AS `quotation`,
                `tabQuotation`.`base_net_total` AS `qtn_base_net_total`,
                `tabSales Order`.`name` AS `sales_order`,
                `tabSales Order`.`base_net_total` AS `so_base_net_total`
            FROM `tabCustomer` 
            LEFT JOIN `tabQuotation` ON (`tabQuotation`.`party_name` = `tabCustomer`.`name` 
                AND `tabQuotation`.`docstatus` = 1)
            LEFT JOIN `tabSales Order` ON (`tabSales Order`.`customer` = `tabCustomer`.`name` 
                AND `tabSales Order`.`docstatus` = 1)
            WHERE 
                `tabCustomer`.`disabled` = 0
        ) AS `raw`
        GROUP BY `raw`.`customer`
        ORDER BY `so_volume` DESC;
    """
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
