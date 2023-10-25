# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    frappe.log_error(filters, "filters")
    data = get_data(filters)
    message = "Based on Sales Orders"
    chart = get_chart(filters, data)
    frappe.log_error("{0}".format(chart), "chart")
    return columns, data, message, chart

    
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
            `customer` AS `customer`,
            `customer_name` AS `customer_name`
        FROM `tabSales Order`
        WHERE `customer` = '{customer}'
            AND `docstatus` = 1
            AND `company` = "{company}"
        GROUP BY `year`
        ORDER BY `year` DESC
    """.format(customer=filters.customer, company=filters.company)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    
    for i in range(0, (len(data) - 1)):
        data[i]['comparison'] = 100 * flt(data[i]['net_amount']) / flt(data[i+1]['net_amount'])
    
    return data

def get_chart(filters, data):
    datasets = []
    values = []
    labels = []
    for i in range(len(data), 0, -1):
        labels.append("{0}".format(data[i-1]['year']))
        values.append(data[i-1]['net_amount'])
        
    datasets = [{
        'name': [frappe.get_value("Customer", filters.customer, "customer_name")],
        'values': values
    }]
    
    chart = {
        'data': {
            'labels': labels,
            'datasets': datasets,
        },
        'type': "bar"
    }
    return chart
