# Copyright (c) 2019-2023, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()    
def validate_prices(invoice_name):
    
    #get all items which have different prices
    items = frappe.db.sql("""SELECT
    `tabSales Invoice Item`.`item_code`, 
    `tabSales Invoice Item`.`item_name`,
    `tabSales Invoice Item`.`sales_order`,
    `tabSales Order Item`.`rate`
    FROM `tabSales Invoice Item` 
    LEFT JOIN `tabSales Order Item` ON `tabSales Order Item`.`name` = `tabSales Invoice Item`.`so_detail` 
    WHERE `tabSales Invoice Item`.`parent` = '{sales_invoice}'
    AND `tabSales Order Item`.`rate` != `tabSales Invoice Item`.`rate`;
    """.format(sales_invoice=invoice_name), as_dict=True)
    
    return items
