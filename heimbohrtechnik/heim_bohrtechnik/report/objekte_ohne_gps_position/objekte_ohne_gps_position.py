# Copyright (c) 2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {"label": _("Object"), "fieldname": "object", "fieldtype": "Link", "options": "Object", "width": 100},
        {"label": _("Object name"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("CH Coordinates"), "fieldname": "ch_coords", "fieldtype": "Data", "width": 120},
        {"label": _("GPS Coordinates"), "fieldname": "gps_ccord", "fieldtype": "Data", "width": 120},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]

def get_data(filters):       
    sql_query = """SELECT 
        `name` AS `object`,
        `object_name` AS `object_name`,
        `ch_coordinates` AS `ch_coord`,
        `gps_coordinates` AS `gps_coord`
        FROM `tabObject`
        WHERE `gps_coordinates` IS NULL
           OR `gps_coordinates` = ""
        ORDER BY `modified` DESC;"""
    data = frappe.db.sql(sql_query, as_dict=True)

    return data
