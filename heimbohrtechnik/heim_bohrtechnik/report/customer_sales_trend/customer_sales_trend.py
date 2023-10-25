# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    frappe.log_error(filters, "filters")
    data = get_data(filters)
    return columns, data

    
def get_columns():
    columns = [
        {"label": _("Year"), "fieldname": "year", "fieldtype": "Int", "width": 60},
        {"label": _("Net amount"), "fieldname": "net_amount", "fieldtype": "Currency", "width": 160},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 100},
        {"label": _("Comparison"), "fieldname": "comparison", "fieldtype": "Percent", "width": 160}
    ]
    return columns
    
def get_data(filters):
    sql_query = """
        SELECT
            YEAR(`transaction_date`) AS `year`,
            SUM(`base_net_total`) AS `net_amount`,
            `customer`,
            `customer_name`,
            NULL AS `comparison`
        FROM `tabSales Order`
        WHERE `customer` = '{cust}'
            AND `docstatus` = 1
        GROUP BY `year`
        ORDER BY `year` DESC
    """.format(cust=filters.customer)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    for i in range(0, len(data)-1):
        data[i]['comparison'] = 100*flt(data[i]['net_amount'])/flt(data[i+1]['net_amount'])
    
    return data
