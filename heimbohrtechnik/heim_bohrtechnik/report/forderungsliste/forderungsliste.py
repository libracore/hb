# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from datetime import datetime
from frappe import _
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {'fieldname': "party_name", 'label': _("Customer"), 'fieldtype': "Link", 'options': "Customer", 'width': 80},
        {'fieldname': "customer_name", 'label': _("Customer Name"), 'fieldtype': "Data", 'width': 150},
        {'fieldname': "document", 'label': _("Document"), 'fieldtype': "Data", 'width': 150},
        {'fieldname': "amount", 'label': _("Amount"), 'fieldtype': "Float", 'precision': 2, 'width': 80},
        {'fieldname': "outstanding", 'label': _("Outstanding Amount"), 'fieldtype': "Float", 'precision': 2, 'width': 80},
        {'fieldname': "currency", 'label': _("Currency"), 'fieldtype': "Data", 'width': 50},
        {'fieldname': "posting_date", 'label': _("Posting Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "due_date", 'label': _("Due Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "reminder_level", 'label': _("Reminder Level"), 'fieldtype': "Int", 'width': 50}
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
    
    return data
