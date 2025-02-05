# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {'fieldname': 'date', 'label': _("Date"), 'fieldtype': 'Date', 'width': 100},
        {'fieldname': 'item_code', 'label': _("Item"), 'fieldtype': 'Link', 'options': 'Item', 'width': 300},
        {'fieldname': 'item_name', 'label': _("Item Name"), 'fieldtype': 'Data', 'width': 300},
        {'fieldname': 'qty', 'label': _("Qty"), 'fieldtype': 'Float', 'width': 100}
    ]
    
def get_data(filters):
    sql_query = """
        SELECT
            `tabStock Entry`.`posting_date` AS `date`,
            `tabStock Entry Detail`.`item_code` AS `item_code`,
            `tabStock Entry Detail`.`item_name` AS `item_name`,
            `tabStock Entry Detail`.`qty` AS `qty`
        FROM `tabStock Entry Detail`
        LEFT JOIN `tabStock Entry` ON `tabStock Entry`.`name` = `tabStock Entry Detail`.`parent`
        WHERE 
            `tabStock Entry`.`employee` = "{employee}"
            AND `tabStock Entry`.`docstatus` = 1
            AND `tabStock Entry`.`stock_entry_type` = "Material Issue"
        """.format(employee=filters.get("employee"))
        
    data = frappe.db.sql(sql_query, as_dict=True)
    
    return data
