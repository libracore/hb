# Copyright (c) 2019-2022, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()    
def validate_prices(objekt):

    #get all items of invoice
    invoice_query = """SELECT
        `sinvitem`.`item_code`,
        `sinvitem`.`item_name`,
        `sinvitem`.`rate`
        FROM `tabSales Invoice Item` AS `sinvitem`
        LEFT JOIN `tabSales Invoice` AS `sinv` ON `sinvitem`.`parent` = `sinv`.`name`
        WHERE `sinv`.`object` = '{objekt}'
        AND `sinv`.`status` NOT IN ("Cancelled");
    """.format(objekt=objekt)
    invoice_data = frappe.db.sql(invoice_query, as_dict=True)

    #get all items of related sales order
    sales_order_query = """SELECT
        `sinvitem`.`item_code`,
        `sinvitem`.`rate`,
        `sinv`.`name`
        FROM `tabSales Order Item` AS `sinvitem`
        LEFT JOIN `tabSales Order` AS `sinv` ON `sinvitem`.`parent` = `sinv`.`name`
        WHERE `sinv`.`object` = '{objekt}'
        AND `sinv`.`status` NOT IN ("Cancelled");
    """.format(objekt=objekt)
    sales_order_data = frappe.db.sql(sales_order_query, as_dict=True)
    frappe.log_error(sales_order_data, "sales_order_data")
    sales_order = sales_order_data[0]['name']
    
    item_codes = []
    item_names = []
    
    for invoice_item in invoice_data:
        for so_item in sales_order_data:
            if invoice_item['item_code'] == so_item['item_code'] and invoice_item['rate'] != so_item['rate']:
                item_codes.append(invoice_item['item_code'])
                item_names.append(invoice_item['item_name'])
    
    frappe.log_error(item_codes, "item_codes")
    frappe.log_error(item_names, "item_names")
    return item_codes, item_names, sales_order
