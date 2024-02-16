# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime, timedelta
from frappe import _
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {'fieldname': "party", 'label': _("Customer"), 'fieldtype': "Link", 'options': "Customer", 'width': 80},
        {'fieldname': "customer_name", 'label': _("Customer Name"), 'fieldtype': "Data", 'width': 150},
        {'fieldname': "voucher_no", 'label': _("Document"), 'fieldtype': "Dynamic Link", 'options': 'voucher_type', 'width': 150},
        {'fieldname': "invoiced", 'label': _("Amount"), 'fieldtype': "Float", 'precision': 2, 'width': 80},
        {'fieldname': "outstanding", 'label': _("Outstanding Amount"), 'fieldtype': "Float", 'precision': 2, 'width': 80},
        {'fieldname': "currency", 'label': _("Currency"), 'fieldtype': "Data", 'width': 50},
        {'fieldname': "posting_date", 'label': _("Posting Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "due_date", 'label': _("Due Date"), 'fieldtype': "Data", 'width': 80},
        {'fieldname': "reminder_level", 'label': _("Reminder Level"), 'fieldtype': "Int", 'width': 80},
        {'fieldname': "handwerkerpfand", 'label': _("HWP"), 'fieldtype': "Check", 'width': 80}
    ]
    
def get_data(filters):
    args = {
        'party_type': "Customer",
        'naming_by': ["Selling Settings", "customer_master_name"]
    }
    filters.update({
        'range1': 60,
        'range2': 120,
        'range3': 180,
        'range4': 240
    })
    
    columns, data, more, chart = ReceivablePayableReport(filters).run(args)
    
    for d in data:
        if d['voucher_type'] == "Sales Invoice":
            d['reminder_level'] = frappe.get_value(d['voucher_type'], d['voucher_no'], "payment_reminder_level")
            d['handwerkerpfand'] = frappe.get_value(d['voucher_type'], d['voucher_no'], "handwerkerpfand_eingetragen")
            if d['due_date'] < (datetime.today() - timedelta(days=45)).date():
                d['due_date'] = "<span style=\"color: red; \">{0}</span>".format(d['due_date'].strftime("%d.%m.%Y"))
            else:
                d['due_date'] = "{0}".format(d['due_date'].strftime("%d.%m.%Y"))
                
    return data
