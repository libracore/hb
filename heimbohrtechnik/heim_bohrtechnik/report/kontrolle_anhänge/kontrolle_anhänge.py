# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
import ast

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Eingangsrechnung-Nr.:"), "fieldname": "pinv_number", "fieldtype": "Link", "options": "Purchase Invoice", "width": 200},
        {"label": _("Lieferant:"), "fieldname": "lieferant", "fieldtype": "Link", "options": "Supplier", "width": 200},
        {"label": _("Datum:"), "fieldname": "due_date", "fieldtype": "Date", "width": 200},
        {"label": _("Gesamtbetrag:"), "fieldname": "gross_amount", "fieldtype": "Float", "precision": 2, "width": 200},
        {"label": _("Anzahl Anhänge"), "fieldname": "number_of_attachments", "fieldtype": "Data", "width": 130},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 140},
    ]

def get_data(filters):
    if type(filters) is str:
        filters = ast.literal_eval(filters)
    else:
        filters = dict(filters)
    
    conditions = ""
    if 'supplier' in filters:
        conditions = """ AND `tabPurchase Invoice`.`supplier` = "{supplier}" """.format(supplier=filters['supplier'])
    if 'from_date' in filters and filters['from_date']:
        conditions += """ AND (`tabPurchase Invoice`.`due_date` >= '{from_date}' OR `tabPurchase Invoice`.`due_date` IS NULL)""".format(from_date=filters['from_date'])
    if 'to_date' in filters and filters['to_date']:
        conditions += """ AND (`tabPurchase Invoice`.`due_date` <= '{to_date}' OR `tabPurchase Invoice`.`due_date` IS NULL)""".format(to_date=filters['to_date'])
        
    # prepare query
    sql_query = """
            SELECT
				`tabPurchase Invoice`.`name` AS `pinv_number`,
				`tabPurchase Invoice`.`supplier` AS `lieferant`,
				`tabPurchase Invoice`.`due_date` AS `due_date`,
				`tabPurchase Invoice`.`grand_total` AS `gross_amount`,
				(SELECT COUNT(*) FROM `tabFile` WHERE `tabFile`.`attached_to_doctype` = 'Purchase Invoice' AND `tabFile`.`attached_to_name` = `tabPurchase Invoice`.`name`) AS `number_of_attachments`,
				`tabPurchase Invoice`.`status` AS `status`
			FROM `tabPurchase Invoice`
			WHERE `tabPurchase Invoice`.`docstatus` = 1
			{conditions}
			ORDER BY `tabPurchase Invoice`.`due_date` ASC
      """.format(conditions=conditions)
    #frappe.throw(sql_query)
    _data = frappe.db.sql(sql_query, as_dict=1)
    
    return _data
