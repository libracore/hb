# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime, timedelta
import datetime

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        # ~ {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100},
        {"label": _("Week"), "fieldname": "cw", "fieldtype": "Int", "width": 50},
        {"label": _("From"), "fieldname": "from", "fieldtype": "Date", "width": 80},
        {"label": _("To"), "fieldname": "to", "fieldtype": "Date", "width": 80},
        {"label": _("Monday"), "fieldname": "monday", "fieldtype": "Int", "width": 70},
        {"label": _("Tuesday"), "fieldname": "tuesday", "fieldtype": "Int", "width": 70},
        {"label": _("Wednesday"), "fieldname": "wednesday", "fieldtype": "Int", "width": 70},
        {"label": _("Thursday"), "fieldname": "thursday", "fieldtype": "Int", "width": 70},
        {"label": _("Friday"), "fieldname": "friday", "fieldtype": "Int", "width": 70},
        {"label": _("Week"), "fieldname": "week", "fieldtype": "Int", "width": 60},
        {"label": _("Remark"), "fieldname": "remark", "fieldtype": "Data", "width": 300}
    ]
    return columns

def get_data(filters):
    
    data = []
    
    #get entrys for every calendar week
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
            """.format(team=filters.drilling_team_filter, i=i)
            
        entrys = frappe.db.sql(sql_query, as_dict=True)
        
        #create a new dict for the actual week
        new_week = {
            'cw': i,
            'flushing': []
        }
        
        week_total = 0
        remark = []
        
        #loop through every entry of the actual week
        for entry in entrys:
            #add amount of drilling meters for each entry to the week total
            week_total += entry.drilling_meter
            #create the day of the entry in the week or add the meter to the existing day
            if entry.day.lower() in new_week:
                new_week[entry.day.lower()] += entry.drilling_meter
            else:
                new_week[entry.day.lower()] = entry.drilling_meter
            #mark days with flushing
            if entry.flushing == 1:
                new_week['flushing'].append(entry.day.lower())
            #check for remarks
            if entry.hammer_change == 1:
                remark.append("Neuer Hammer")
            if entry.impact_part_change == 1:
                remark.append("Neues Schlagteil")
        
        #add the week total to actual week dict
        new_week['week'] = week_total
        
        #add remarks
        if remark:
            new_week['remark'] = ', '.join(remark)
        else:
            new_week['remark'] = "-"
        
        #ad from and to date
        new_week['from'] = datetime.date.fromisocalendar(int(filters.year_filter), i, 1)
        new_week['to'] = frappe.utils.add_days(new_week['from'], 6)
        
        #add week to data    
        data.append(new_week)
        
    return data
