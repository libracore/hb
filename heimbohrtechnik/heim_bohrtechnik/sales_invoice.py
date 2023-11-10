# Copyright (c) 2019-2023, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()    
def validate_prices(invoice_name, objekt):
    
    #get all items of invoice
    items_query = """SELECT
    `tabSales Invoice Item`.`item_code`, 
    `tabSales Invoice Item`.`item_name`,
    `tabSales Order Item`.`rate`, 
    `tabSales Invoice Item`.`rate`,
    `tabSales Order Item`.`parent`
    FROM `tabSales Invoice Item` 
    LEFT JOIN `tabSales Order Item` ON `tabSales Order Item`.`name` = `tabSales Invoice Item`.`so_detail` 
    WHERE `tabSales Invoice Item`.`parent` = '{sales_invoice}'
    AND `tabSales Order Item`.`rate` != `tabSales Invoice Item`.`rate`;
    """.format(sales_invoice=invoice_name)
    items = frappe.db.sql(items_query, as_dict=True)
    
    if len(sales_order_data) == 0:
        return None
    frappe.log_error(items, "items")
    sales_order = sales_order_data[0]['name']
    
    item_codes = []
    item_names = []
    
    for invoice_item in invoice_data:
        for so_item in sales_order_data:
            if invoice_item['item_code'] == so_item['item_code'] and invoice_item['rate'] != so_item['rate']:
                if not invoice_item['item_code'] in item_codes:
                    item_codes.append(invoice_item['item_code'])
                    item_names.append(invoice_item['item_name'])
    
    return item_codes, item_names, sales_order


SELECT `tabSales Order Item`.`rate`, `tabSales Invoice Item`.`rate` FROM `tabSales Invoice Item` LEFT JOIN `tabSales Order Item` ON `tabSales Order Item`.`name` = `tabSales Invoice Item`.`so_detail` WHERE `tabSales Invoice Item`.`parent` = "{sales_invoice}";
