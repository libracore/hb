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
            `raw`.`qtns`,
            `raw`.`qtn_volume`,
            `raw`.`sos`,
            `raw`.`so_volume`
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
                (SELECT COUNT(`tQ1`.`name`) 
                 FROM `tabQuotation` AS `tQ1`
                 WHERE `tQ1`.`party_name` = `tabCustomer`.`name` 
                   AND `tQ1`.`docstatus` = 1
                   AND `tQ1`.`transaction_date` BETWEEN "{from_date}" AND "{to_date}") AS `qtns`,
                (SELECT SUM(`tQ2`.`base_net_total`) 
                 FROM `tabQuotation` AS `tQ2`
                 WHERE `tQ2`.`party_name` = `tabCustomer`.`name` 
                   AND `tQ2`.`docstatus` = 1
                   AND `tQ2`.`transaction_date` BETWEEN "{from_date}" AND "{to_date}") AS `qtn_volume`,
                (SELECT COUNT(`tS1`.`name`) 
                 FROM `tabSales Order` AS `tS1`
                 WHERE `tS1`.`customer` = `tabCustomer`.`name` 
                   AND `tS1`.`docstatus` = 1
                   AND `tS1`.`transaction_date` BETWEEN "{from_date}" AND "{to_date}") AS `sos`,
                (SELECT SUM(`tS2`.`base_net_total`) 
                 FROM `tabSales Order` AS `tS2`
                 WHERE `tS2`.`customer` = `tabCustomer`.`name` 
                   AND `tS2`.`docstatus` = 1
                   AND `tS2`.`transaction_date` BETWEEN "{from_date}" AND "{to_date}") AS `so_volume`
            FROM `tabCustomer` 
            WHERE 
                `tabCustomer`.`disabled` = 0
            GROUP BY `tabCustomer`.`name`
        ) AS `raw`
        GROUP BY `raw`.`customer`
        ORDER BY `so_volume` DESC;
    """.format(from_date=filters.from_date, to_date=filters.to_date)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
