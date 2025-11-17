# Copyright (c) 2022-2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
import json

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 80},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 250},
        {"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 80},
        {"label": _("Sales Order"), "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 80},
        {"label": _("Net Amount"), "fieldname": "net_amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 150},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
        {"label": _("Expected End Date"), "fieldname": "expected_end_date", "fieldtype": "Date", "width": 80},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]
    return columns

def get_data(filters):
    conditions = ""
    if filters.get('sales_order'):
        conditions = """AND `tabSales Invoice Item`.`sales_order` = "{0}" """.format(filters.get('sales_order'))
    
    sql_query = """
        SELECT
            `tabSales Invoice`.`posting_date` AS `date`,
            `tabSales Invoice`.`customer` AS `customer`,
            `tabSales Invoice`.`customer_name` AS `customer_name`,
            `tabSales Invoice`.`name` AS `sales_invoice`,
            `tabSales Invoice`.`base_net_total` AS `net_amount`,
            `tabSales Invoice`.`base_grand_total` AS `amount`,
            `tabSales Invoice`.`status` AS `status`,
            /*`tabSales Invoice`.`currency`*/ "CHF" AS `currency`,
            `tabSales Invoice Item`.`sales_order` AS `sales_order`,
            `tabSales Invoice Item`.`name` AS `reference`,
            `tabProject`.`name` AS `project`,
            `tabProject`.`expected_end_date` AS `expected_end_date`
        FROM `tabSales Invoice` 
        LEFT JOIN `tabSales Invoice Item` ON `tabSales Invoice Item`.`parent` = `tabSales Invoice`.`name`
        LEFT JOIN 
            (SELECT `tabDiscount Position`.`name`, `tabDiscount Position`.`akonto_invoice_item`, `tUse`.`posting_date`
             FROM `tabDiscount Position`
             LEFT JOIN `tabSales Invoice` AS `tUse` on `tUse`.`name` = `tabDiscount Position`.`parent`
             WHERE
                `tabDiscount Position`.`docstatus` < 2
                AND `tUse`.`posting_date` <= %(date)s
            ) AS `tAllocation Invoice`
            ON `tAllocation Invoice`.`akonto_invoice_item` = `tabSales Invoice Item`.`name`
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabSales Invoice`.`project`
        WHERE 
            `tabSales Invoice`.`docstatus` = 1
            AND `tabSales Invoice Item`.`item_code` = %(akonto_item)s
            AND `tAllocation Invoice`.`name` IS NULL
            AND `tabSales Invoice`.`posting_date` <= %(date)s
            {conditions}
        GROUP BY `tabSales Invoice`.`name`
        ORDER BY `tabSales Invoice`.`posting_date` ASC;
    """.format(conditions=conditions)
    
    data = frappe.db.sql(sql_query, 
        {
            'akonto_item': frappe.get_value("Heim Settings", "Heim Settings", "akonto_item"),
            'date': filters.get('date')
        },
        as_dict=True
    )
    
    return data
    
@frappe.whitelist()
def create_accrual(accrual_date, resolution_date, accrual_account, revenue_account, amount, currency, invoices):
    if type(invoices) == str:
        invoices = json.loads(invoices)
    
    accrual_jv = frappe.get_doc({
        'doctype': "Journal Entry",
        'posting_date': accrual_date,
        'company': frappe.defaults.get_defaults()['company'],
        'accounts': [
            {
                'account': accrual_account,
                'debit_in_account_currency': flt(amount),
                'debit': flt(amount)
            },
            {
                'account': revenue_account,
                'credit_in_account_currency': flt(amount),
                'credit': flt(amount)
            }
        ],
        'user_remark': "Abgrenzungsbuchung Akonto",
        'remark': "Abgrenzungsbuchung Akonto"
    })
    accrual_jv.insert(ignore_permissions=True)
    accrual_jv.submit()
    
    resolution_jv = frappe.get_doc({
        'doctype': "Journal Entry",
        'posting_date': resolution_date,
        'company': frappe.defaults.get_defaults()['company'],
        'accounts': [
            {
                'account': revenue_account,
                'debit_in_account_currency': flt(amount),
                'debit': flt(amount)
            },
            {
                'account': accrual_account,
                'credit_in_account_currency': flt(amount),
                'credit': flt(amount)
            }
        ],
        'user_remark': "Auflösung Abgrenzungsbuchung Akonto" ,
        'remark': "Auflösung Abgrenzungsbuchung Akonto" 
    })
    resolution_jv.insert(ignore_permissions=True)
    resolution_jv.submit()
        
    accrual_information = frappe.get_doc({
        'doctype': "Akonto Abgrenzung",
        'accrual_date': accrual_date,
        'resolution_date': resolution_date,
        'revenue_account': revenue_account,
        'wip_account': accrual_account,
        'accrual_booking': accrual_jv.name,
        'resolution_booking': resolution_jv.name,
        'currency': currency,
        'amount': flt(amount)
    })
    for i in invoices:
        accrual_information.append("invoices", i)
    accrual_information.insert(ignore_permissions=True)
    
    frappe.db.commit()
    
    return accrual_information.name
    
