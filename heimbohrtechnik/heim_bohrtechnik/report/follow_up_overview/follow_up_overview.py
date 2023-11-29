# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data
    
def get_columns(filters):
    columns = [
        {"label": _("Quotation"), "fieldname": "quotation", "fieldtype": "Link", "options": "Quotation", "width": 100},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Volume"), "fieldname": "volume", "fieldtype": "Currency", "width": 120},
        {"label": _("Object"), "fieldname": "object", "fieldtype": "Link", "options": "Object", "width": 80},
        {"label": _("Object name"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Angebot seit"), "fieldname": "days_since_quotation", "fieldtype": "Int", "width": 80},
        {"label": _("Nachgefasst seit"), "fieldname": "days_since_fup", "fieldtype": "Int", "width": 80},
        {"label": _("Notes"), "fieldname": "notes", "fieldtype": "Data", "width": 300}
    ]
    return columns
    
def get_data(filters):
    conditions = ""
    if filters.volume_from:
        conditions += """ AND `tabQuotation`.`base_net_total` >= {vol} """.format(vol=filters.volume_from)
    if filters.volume_to:
        conditions += """ AND `tabQuotation`.`base_net_total` <= {vol} """.format(vol=filters.volume_to)
        
    data = frappe.db.sql("""
        SELECT
            `tabQuotation`.`name` AS `quotation`,
            `tabQuotation`.`party_name` AS `customer`,
            `tabQuotation`.`customer_name` AS `customer_name`,
            `tabQuotation`.`object` AS `object`,
            `tabQuotation`.`object_name` AS `object_name`,
            `tabQuotation`.`base_net_total` AS `volume`,
            `tabQuotation`.`transaction_date` AS `transaction_date`,
            `tabQuotation`.`valid_till` AS `valid_until_date`,
            (SELECT `tabFollow Up Note`.`name`
             FROM `tabFollow Up Note`
             WHERE `tabFollow Up Note`.`quotation` = `tabQuotation`.`name`
             ORDER BY `tabFollow Up Note`.`date` DESC
             LIMIT 1) AS `follow_up_note`
        FROM `tabQuotation`
        WHERE
            `tabQuotation`.`status` = "Open"
            {conditions}
            AND `tabQuotation`.`valid_till` >= CURDATE()
        ORDER BY `tabQuotation`.`base_net_total` DESC;
    """.format(conditions=conditions),
        as_dict=True)
    
    for d in data:
        d['days_since_quotation'] = (datetime.now().date() - d['transaction_date']).days
        if d.get("follow_up_note"):
            note = frappe.get_doc("Follow Up Note", d.get("follow_up_note"))
            d['notes'] = note.notes
            d['days_since_fup'] = (datetime.now().date() - note.date).days
            
    return data
