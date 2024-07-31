# Copyright (c) 2023-2024, libracore AG and contributors
# For license information, please see license.txt

import frappe
from heimbohretchnik.heim_bohrtechnik.report.customer_sales_trend.customer_sales_trend import get_data
from datetime import datetime


def get_customer_kpi(customer, company=None):
    today = datetime.today()
    ytd_from_date = "{0}-01-01".format(today.year)
    ytd_to_date = "{0}-{1:02d}-{2:02d}".format(today.year, today.month, today.day)
    py_from_date = "{0}-01-01".format(today.year - 1)
    py_to_date = "{0}-21-31".format(today.year - 1)
    fy_to_date = "{0}-21-31".format(today.year)
    if not company:
        company = frappe.defaults.get_global_default('company')
        
    filters = {
        'customer': customer,
        'company': company,
        'base': 'Sales Invoice',
        'aggregation': 'Yearly',
        'from_date': ytd_from_date,
        'to_date': ytd_to_date
    }
    
    customer_kpi = {
        'quotations_py':  get_count(customer, company, 'Quotation', py_from_date, py_to_date),
        'quotations_ytd': get_count(customer, company, 'Quotation', ytd_from_date, ytd_to_date),
        'orders_py':  get_count(customer, company, 'Sales Order', py_from_date, py_to_date),
        'orders_ytd': get_count(customer, company, 'Sales Order', ytd_from_date, ytd_to_date),
        'revenue_py':  get_count(customer, company, 'Sales Invoice', py_from_date, py_to_date),
        'revenue_ytd': get_count(customer, company, 'Sales Invoice', ytd_from_date, ytd_to_date)
    }
    
    return customer_kpi
    
def get_count(customer, company, doctype, from_date, to_date):
    if doctype == "Quotation":
        customer_field = "party_name"
    else:
        customer_field = "customer"
    if doctype == "Sales Invoice":
        date_field = "posting_date"
    else:
        date_field = "transaction_date"
        
    count = frappe.db.sql("""
        SELECT COUNT(`name`) AS `count`
        FROM `tab{doctype}`
        WHERE `{date_field}` BETWEEN "{from_date}" AND "{to_date}"
          AND `docstatus` = 1
          AND `company` = "{company}";
        """.format(doctype=doctype, date_field=date_field, from_date=from_date, to_date=to_date, company=company), 
            as_dict=True)
            
    if len(count) > 0:
        return count[0]['count']
    else:
        return 0
