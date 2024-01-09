# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100},
        {"label": _("Week"), "fieldname": "cw", "fieldtype": "Int", "width": 60},
        {"label": _("From"), "fieldname": "from", "fieldtype": "Date", "width": 80},
        {"label": _("To"), "fieldname": "to", "fieldtype": "Date", "width": 80},
        {"label": _("Monday"), "fieldname": "monday", "fieldtype": "Int", "width": 80},
        {"label": _("Tuesday"), "fieldname": "tuesday", "fieldtype": "Int", "width": 80},
        {"label": _("Wednesday"), "fieldname": "wednesday", "fieldtype": "Int", "width": 80},
        {"label": _("Thursday"), "fieldname": "thursday", "fieldtype": "Int", "width": 80},
        {"label": _("Friday"), "fieldname": "friday", "fieldtype": "Int", "width": 80},
        {"label": _("Week"), "fieldname": "week", "fieldtype": "Int", "width": 80},
        {"label": _("Remark"), "fieldname": "remark", "fieldtype": "Int", "width": 80}
    ]
    return columns

def get_data(filters):
    return
