# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextswiss.erpnextswiss.utils import get_first_day_of_first_cw
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_days
from frappe.utils.data import getdate
from datetime import datetime
from frappe.utils import get_url_to_form


def execute(filters=None):
    columns, days = get_columns(filters)
    data = get_data(filters, days)
    return columns, data

def get_columns(filters):
    if filters.drilling_team_filter:
        columns = [
            {"label": _("Drilling Team"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 100},
            {"label": _("Week"), "fieldname": "cw", "fieldtype": "Int", "width": 50},
            {"label": _("From"), "fieldname": "from", "fieldtype": "Date", "width": 80},
            {"label": _("To"), "fieldname": "to", "fieldtype": "Date", "width": 80},
            {"label": _("Monday"), "fieldname": "monday", "fieldtype": "Data", "width": 70},
            {"label": _("Tuesday"), "fieldname": "tuesday", "fieldtype": "Data", "width": 70},
            {"label": _("Wednesday"), "fieldname": "wednesday", "fieldtype": "Data", "width": 70},
            {"label": _("Thursday"), "fieldname": "thursday", "fieldtype": "Data", "width": 70},
            {"label": _("Friday"), "fieldname": "friday", "fieldtype": "Data", "width": 70},
            {"label": _("Week"), "fieldname": "week", "fieldtype": "Data", "width": 60},
            {"label": _("Remark"), "fieldname": "remark", "fieldtype": "Data", "width": 300}
        ]
        days = None
    else:
        days = get_related_days()
        columns = [
            {"label": _("Drilling Team"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 100}
        ]
        
        for index, day in enumerate(days):
            columns.append({"label": _("{0}".format(day)), "fieldname": "day_{0}".format(index), "fieldtype": "Data", "width": 150})
            
        columns.append({"label": _("Remark"), "fieldname": "remark", "fieldtype": "Data", "width": 300})
    return columns, days

def get_data(filters, days):
    if filters.drilling_team_filter:
        data = []
        year_total = 0
        
        #get first day of cw1
        first_day = get_first_day_of_first_cw(filters.year_filter)
        
        for i in range(1, 53):
            #create a new dict for the actual week
            new_week = {
                'drilling_team': filters.drilling_team_filter,
                'from': first_day.date(),
                'to': frappe.utils.add_days(first_day, 6).date()
            }
            
            #get entrys for every calendar week
            sql_query = """SELECT
                `name`,
                `date`,
                `drilling_meter`,
                `day`,
                `flushing`,
                `hammer_change`,
                `impact_part_change`
                FROM `tabFeedback Drilling Meter`
                WHERE `drilling_team` = '{team}'
                AND `docstatus` =  1
                AND `date` BETWEEN '{week_start}' AND '{week_end}'
                """.format(team=filters.drilling_team_filter, week_start=new_week['from'], week_end=new_week['to'])
                
            entrys = frappe.db.sql(sql_query, as_dict=True)
            
            week_total = 0
            remark = []
            
            #loop through every entry of the actual week
            for entry in entrys:
                frappe.log_error(entry, "entry")
                #add amount of drilling meters for each entry to the week total
                week_total += entry.drilling_meter
                
                #create the day of the entry in the week or add the meter to the existing day
                # ~ if entry.day.lower() in new_week:
                    # ~ new_week[entry.day.lower()] += entry.drilling_meter
                # ~ else:
                    # ~ new_week[entry.day.lower()] = entry.drilling_meter
                    
                #prepare html for meters entry
                style = "style='color: black;'"
                if entry.flushing == 1:
                    style = "style='color: red;'"
                url = get_url_to_form("Feedback Drilling Meter", entry.name)
                html = "<a href='{0}' {1}>{2}</a>".format(url, style, entry.drilling_meter)
                frappe.log_error(html, "html")
                #add html to entry
                frappe.log_error(entry.day.lower(), "entry.day.lower()")
                new_week[entry.day.lower()] = html
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
        frappe.log_error(data, "data")
    else:
        #get today and create variable for data
        today = getdate()
        data = []
        #get all drilling teams
        drilling_teams = frappe.db.sql("""
                                        SELECT
                                            `name`
                                        FROM
                                            `tabDrilling Team`
                                        WHERE
                                            `drilling_team_type` = 'Bohrteam'""", as_dict=True)
        
        for drilling_team in drilling_teams:
            #get affected entries for related drilling team
            entries = frappe.db.sql("""
                                        SELECT
                                            `name`,
                                            `drilling_meter`,
                                            `date`,
                                            `flushing`,
                                            `hammer_change`,
                                            `impact_part_change`
                                        FROM 
                                            `tabFeedback Drilling Meter`
                                        WHERE
                                            `date` BETWEEN '{start}' AND '{end}'
                                        AND
                                            `drilling_team` = '{dt}'
                                        AND
                                            `docstatus` =  1
                                        ORDER BY
                                            `date` DESC
                                        """.format(start=frappe.utils.add_days(today, -7), end=frappe.utils.add_days(today, -1), dt=drilling_team.get('name')), as_dict=True)
            #prepare line for report and add it do data
            remarks = ""
            line = {
                    'drilling_team': drilling_team.get('name')
                    }
            loop_index = 0
            for day in days:
                for entry in entries:
                    if datetime.strptime(day[-10:], "%d.%m.%Y").date() == entry.get('date'):
                        style = "style='color: black;'"
                        if entry.get('flushing') == 1:
                            style = "style='color: red;'"
                        url = get_url_to_form("Feedback Drilling Meter", entry.get('name'))
                        line['day_{0}'.format(loop_index)] = "<a href='{0}' {1}>{2}</a>".format(url, style, entry.get('drilling_meter'))
                        if entry.get('hammer_change') == 1:
                            remarks += "Neuer Hammer, "
                        if entry.get('impact_part_change') == 1:
                            remarks += "Neues Schlagteil, "
                loop_index += 1
            line['remark'] = remarks[:-2]
            data.append(line)
    return data

def get_related_days():
    today = getdate()
    days = get_days(frappe.utils.add_days(today, -7), frappe.utils.add_days(today, -1))
    related_days = []
    for key, value in days[3].items():
        if value != "Sat" and value != "Sun":
            related_days.append("{0} {1}".format(value, key))
    return related_days
