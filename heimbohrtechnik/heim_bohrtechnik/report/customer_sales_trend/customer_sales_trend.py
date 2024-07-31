# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    
    data = get_data(filters)
    
    message = "Based on Sales Orders"
    chart = get_chart(filters, data)
    
    return columns, data, message, chart

    
def get_columns():
    columns = [
        {"label": _("Year"), "fieldname": "year", "fieldtype": "Data", "width": 60},
        {"label": _("Net amount"), "fieldname": "net_amount", "fieldtype": "Currency", "width": 160},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 100},
        {"label": _("Comparison"), "fieldname": "comparison", "fieldtype": "Percent", "width": 160}
    ]
    return columns
    
def get_data(filters):
    if filters.base == "Sales Order":
        date_field = "transaction_date"
    else:
        date_field = "posting_date"
    
    conditions = ""
    if filters.from_date:
        conditions += """ AND `{date_field}` >= "{from_date}" """.format(date_field=date_field, from_date=filters.from_date)
    if filters.to_date:
        conditions += """ AND `{date_field}` <= "{to_date}" """.format(date_field=date_field, to_date=filters.to_date)
        
    if filters.aggregation == "Quarterly":
        sql_query = """
            SELECT
                CONCAT(
                    YEAR(`{date_field}`),
                    CASE
                        WHEN SUBSTRING(`{date_field}`, 6, 2) BETWEEN "01" AND "03" THEN "-Q1"
                        WHEN SUBSTRING(`{date_field}`, 6, 2) BETWEEN "04" AND "06" THEN "-Q2"
                        WHEN SUBSTRING(`{date_field}`, 6, 2) BETWEEN "07" AND "09" THEN "-Q3"
                        ELSE "-Q4"
                    END
                ) AS `year`,
                SUM(`base_net_total`) AS `net_amount`,
                `customer` AS `customer`,
                `customer_name` AS `customer_name`
            FROM `tab{base}`
            WHERE `customer` = '{customer}'
                AND `docstatus` = 1
                AND `company` = "{company}"
                {conditions}
            GROUP BY `year`
            ORDER BY `year` DESC
        """.format(customer=filters.customer, company=filters.company, base=filters.base, date_field=date_field, conditions=conditions)
        
    elif filters.aggregation == "Monthly":
        sql_query = """
            SELECT
                SUBSTRING(`{date_field}`, 1, 7) AS `year`,
                SUM(`base_net_total`) AS `net_amount`,
                `customer` AS `customer`,
                `customer_name` AS `customer_name`
            FROM `tab{base}`
            WHERE `customer` = '{customer}'
                AND `docstatus` = 1
                AND `company` = "{company}"
                {conditions}
            GROUP BY `year`
            ORDER BY `year` DESC
        """.format(customer=filters.customer, company=filters.company, base=filters.base, date_field=date_field, conditions=conditions)
        
    else:
        sql_query = """
            SELECT
                YEAR(`{date_field}`) AS `year`,
                SUM(`base_net_total`) AS `net_amount`,
                `customer` AS `customer`,
                `customer_name` AS `customer_name`
            FROM `tab{base}`
            WHERE `customer` = '{customer}'
                AND `docstatus` = 1
                AND `company` = "{company}"
                {conditions}
            GROUP BY `year`
            ORDER BY `year` DESC
        """.format(customer=filters.customer, company=filters.company, base=filters.base, date_field=date_field, conditions=conditions)
    
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
        'type': "line"
    }
    return chart
