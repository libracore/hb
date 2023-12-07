# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnextswiss.erpnextswiss.finance import get_customer_ledger, get_debit_accounts
from datetime import datetime
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {'fieldname': "customer", 'label': _("Customer"), 'fieldtype': "Link", 'options': "Customer", 'width': 80},
        {'fieldname': "customer_name", 'label': _("Customer Name"), 'fieldtype': "Data", 'width': 150},
        {'fieldname': "amount", 'label': _("Amount"), 'fieldtype': "Float", 'precision': 2, 'width': 80},
        {'fieldname': "outstanding", 'label': _("Outstanding Amount"), 'fieldtype': "Float", 'precision': 2, 'width': 80},
        {'fieldname': "currency", 'label': _("Currency"), 'fieldtype': "Data", 'width': 50},
        {'fieldname': "posting_date", 'label': _("Posting Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "due_date", 'label': _("Due Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "reminder_level", 'label': _("Reminder Level"), 'fieldtype': "Int", 'width': 50}
    ]
    
def get_data(filters):
    customers = frappe.db.sql("""SELECT `customer` 
            FROM `tabSales Invoice` 
            WHERE `outstanding_amount` > 0 
              AND `docstatus` = 1
              AND (`due_date` < CURDATE())
              AND `enable_lsv` = 0
              AND ((`exclude_from_payment_reminder_until` IS NULL) OR (`exclude_from_payment_reminder_until` < CURDATE()))
              AND `company` = "{company}"
            GROUP BY `customer`;""".format(company=filters.company), as_dict=True)
    # find maximum reminder level
    sql_query = ("""SELECT MAX(`reminder_level`) AS `max` FROM `tabERPNextSwiss Settings Payment Reminder Charge`;""")
    try:
        max_level = frappe.db.sql(sql_query, as_dict=True)[0]['max']
        if not max_level:
            max_level = 3
    except:
        max_level = 3
    # get all sales invoices that are overdue
    data = []
    for customer in (customers or []):
        if filters.customer and customer.customer != filters.customer:
            continue
        open_invoices = frappe.db.sql("""SELECT 
                    `name`, 
                    `due_date`, 
                    `posting_date`, 
                    `payment_reminder_level`, 
                    `grand_total`, 
                    `outstanding_amount` , 
                    `currency`,
                    `contact_email`
                FROM `tabSales Invoice` 
                WHERE `outstanding_amount` > 0 AND `customer` = "{customer}"
                  AND `docstatus` = 1
                  AND `enable_lsv` = 0
                  AND (`due_date` < CURDATE())
                  AND `company` = "{company}"
                  AND ((`exclude_from_payment_reminder_until` IS NULL) OR (`exclude_from_payment_reminder_until` < CURDATE()));
                """.format(customer=customer.customer, company=filters.company), as_dict=True)
        email = None
        if open_invoices:
            # check if this customer has an overall credit balance
            if frappe.get_value("ERPNextSwiss Settings", "ERPNextSwiss Settings", "no_reminder_on_credit_balance"):
                # get customer credit balance
                debit_accounts = get_debit_accounts(company)
                gl_records = get_customer_ledger(debit_accounts, customer)
                if len(gl_records) > 0 and gl_records[-1]['balance'] >= 0:
                    continue        # skip on balance
                    
            now = datetime.now()
            invoices = []
            highest_level = 0
            total_before_charges = 0
            invoice_total = 0
            currency = None
            for invoice in open_invoices:
                level = invoice.payment_reminder_level + 1
                if level > max_level:
                    level = max_level
                new_invoice = { 
                    'sales_invoice': invoice.name,
                    'amount': invoice.grand_total,
                    'outstanding_amount': invoice.outstanding_amount,
                    'posting_date': invoice.posting_date,
                    'due_date': invoice.due_date,
                    'reminder_level': level
                }
                if level > highest_level:
                    highest_level = level
                total_before_charges += invoice.outstanding_amount
                invoice_total += invoice.grand_total
                invoices.append(new_invoice)
                currency = invoice.currency
                if invoice.contact_email:
                    email = invoice.contact_email
            # find reminder charge
            charge_matches = frappe.get_all("ERPNextSwiss Settings Payment Reminder Charge", 
                filters={ 'reminder_level': highest_level },
                fields=['reminder_charge'])
            reminder_charge = 0
            if charge_matches:
                reminder_charge = charge_matches[0]['reminder_charge']
            
            # extend row
            customer_name = frappe.get_value("Customer", customer.customer, "customer_name")
            data.append({
                'customer': customer.customer,
                'customer_name': customer_name,
                'outstanding': total_before_charges,
                'amount': invoice_total,
                'currency': currency,
                'indent': 0
            })
            # and append each invoice indented
            for invoice in invoices:
                data.append({
                    'customer': customer.customer,
                    'customer_name': customer_name,
                    'outstanding': invoice.get('outstanding_amount'),
                    'amount': invoice.get('amount'),
                    'posting_date': invoice.get('posting_date'),
                    'due_date': invoice.get('due_date'),
                    'reminder_level': invoice.get('reminder_level'),
                    'currency': currency,
                    'indent': 1
                })
    return data
