# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Data", "width": 100},
        {"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Data", "width": 100},
        {"label": _("Start Half Day"), "fieldname": "start_half_day", "fieldtype": "Data", "width": 100},
        {"label": _("End Date"), "fieldname": "end_date", "fieldtype": "Data", "width": 100},
        {"label": _("End Half Day"), "fieldname": "end_half_day", "fieldtype": "Data", "width": 100},
        {"label": _("Meters"), "fieldname": "meters", "fieldtype": "Data", "width": 100}
    ]
    return columns

def get_data(filters):
    sql_query = """
        SELECT
            `name` AS `project`,
            `expected_start_date` AS `start_date`,
            `start_half_day`,
            `expected_end_date` AS `end_date`,
            `end_half_day`
        FROM `tabProject`
        WHERE `object` = "P-231027"
    """.format()
   
    data = frappe.db.sql(sql_query, as_dict=True)
   
    return data
