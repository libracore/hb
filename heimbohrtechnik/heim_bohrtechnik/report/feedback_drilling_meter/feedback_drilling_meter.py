# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextswiss.erpnextswiss.utils import get_first_day_of_first_cw


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
    year_total = 0
    
    #get first day of cw1
    first_day = get_first_day_of_first_cw(filters.year_filter)
    
    for i in range(1, 53):
        #create a new dict for the actual week
        new_week = {
            'from': first_day,
            'to': frappe.utils.add_days(first_day, 6),
            'flushing': []
        }
        
        #get entrys for every calendar week
        sql_query = """SELECT 
            `date`,
            `drilling_meter`,
            `day`,
            `flushing`,
            `hammer_change`,
            `impact_part_change`
            FROM `tabFeedback Drilling Meter`
            WHERE `drilling_team` = '{team}'
            AND `date` BETWEEN '{week_start}' AND '{week_end}'
            """.format(team=filters.drilling_team_filter, week_start=new_week['from'], week_end=new_week['to'])
            
        entrys = frappe.db.sql(sql_query, as_dict=True)
        
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
        
        #add cw
        new_week['cw'] = i
        
        #add remarks
        if remark:
            new_week['remark'] = ', '.join(remark)
        else:
            new_week['remark'] = "-"
        
        #ad from and to date
        first_day = frappe.utils.add_days(first_day, 7)
        
        #add week to data    
        data.append(new_week)
        
        #add week total to year total
        year_total += week_total
    
    #create year total entry and add it to data
    year_entry = {
        'week': year_total,
        'remark': "(Total {year})".format(year=filters.year_filter)
    }
    data.append(year_entry)
        
    return data
            
    
