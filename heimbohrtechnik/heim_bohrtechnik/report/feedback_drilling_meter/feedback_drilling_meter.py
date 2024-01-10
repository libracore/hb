# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        # ~ {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100},
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
    # ~ start = datetime(int(filters.year_filter), 1, 1).date()
    # ~ end = datetime(int(filters.year_filter), 12, 31).date()
    
    data =
    
    for i in range(1, 53):
        sql_query = """SELECT 
            `date`,
            `drilling_meter`,
            `week`,
            `day`,
            `flushing`,
            `hammer_change`,
            `impact_part_change`
            FROM `tabFeedback Drilling Meter`
            WHERE `drilling_team` = '{team}'
            AND `week` = '{i}'
            """.format(i=i)
            
            entrys = frappe.db.sql(sql_query, as_dict=True)
            
            new_week = {
                'cw' : i,
                'from': xxx,
                'to': xxx,
                
                

    
    # ~ sql_query = """SELECT 
        # ~ `date`,
        # ~ `drilling_meter`,
        # ~ `week`,
        # ~ `day`,
        # ~ `flushing`,
        # ~ `hammer_change`,
        # ~ `impact_part_change`
        # ~ FROM `tabFeedback Drilling Meter`
        # ~ WHERE `drilling_team` = '{team}'
        # ~ AND `date` BETWEEN '{start}' AND '{end}'
        # ~ """.format(team=filters.drilling_team_filter, start=start, end=end)
        
    # ~ raw_data = frappe.db.sql(sql_query, as_dict=True)
    
    
    
    # ~ frappe.log_error(weeks_in_year, "weeks_in_year")
        
    return
