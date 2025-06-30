# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextswiss.erpnextswiss.utils import get_first_day_of_first_cw
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_days
import datetime


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": _("Period"), "fieldname": "period", "fieldtype": "Data", "width": 200},
        {"label": _("Bentonite"), "fieldname": "bentonite", "fieldtype": "Int", "width": 100},
        {"label": _("Zement"), "fieldname": "zement", "fieldtype": "Int", "width": 100},
        {"label": _("Thermozement"), "fieldname": "thermozement", "fieldtype": "Int", "width": 100},
        {"label": _("Antisol"), "fieldname": "antisol", "fieldtype": "Int", "width": 100},
        {"label": _("Total Drilling Meter"), "fieldname": "drilling_meter", "fieldtype": "Int", "width": 130},
        {"label": _("Total Consumables"), "fieldname": "total", "fieldtype": "Int", "width": 130},
        {"label": _("Per Meter"), "fieldname": "total_per_meter", "fieldtype": "Float", "width": 100}
    ]
    
    return columns

def get_data(filters):
    rows = get_rows(filters)
    
    for row in rows:
        #prepate conditions for sql
        if filters.drilling_team_filter:
            drilling_team_condition = """AND `drilling_team` = '{0}'""".format(filters.drilling_team_filter)
        else:
            drilling_team_condition = ""
            
        if filters.period_filter == "Pro Tag":
            date_condition = """`date` = '{0}'""".format(datetime.datetime.strptime(row.get('period'), "%d.%m.%Y").date())
        else:
            date_condition = """`date` BETWEEN '{0}' AND '{1}'""".format(row.get('from'), row.get('to'))
        
        #get data for row
        data = frappe.db.sql("""
                            SELECT
                                SUM(`bentonite`) as `bentonite`,
                                SUM(`zement`) as `zement`,
                                SUM(`thermozement`) as `thermozement`,
                                SUM(`antisol`) as `antisol`,
                                SUM(`drilling_meter`) as `drilling_meter`
                            FROM
                                `tabFeedback Drilling Meter`
                            WHERE
                                {date_condition}
                                {drilling_team_condition}
                            AND
                                `finished_document` = 1""".format(date_condition=date_condition, drilling_team_condition=drilling_team_condition), as_dict=True)
        
        row['bentonite'] = data[0].get('bentonite') or 0
        row['zement'] = data[0].get('zement') or 0
        row['thermozement'] = data[0].get('thermozement') or 0
        row['antisol'] = data[0].get('antisol') or 0
        row['total'] = row.get('bentonite') + row.get('zement') + row.get('thermozement') + row.get('antisol')
        row['drilling_meter'] = data[0].get('drilling_meter') or 0
        if row.get('drilling_meter') > 0:
            row['total_per_meter'] = row.get('total') / row.get('drilling_meter')
    
    return rows

def get_rows(filters):
    #get today and preapre rows
    rows = []
    today = datetime.date.today()
    
    #Add rows for "Per Day"
    if filters.period_filter == "Pro Tag":
        current_date = datetime.date(filters.year_filter, 1, 1)
        _, weekend_days, _, _ ,_ = get_days(current_date, today)
        
        while current_date < today:
            if current_date.strftime("%d.%m.%Y") not in weekend_days:
                rows.append({'period': current_date.strftime("%d.%m.%Y")})
            current_date = frappe.utils.add_days(current_date, 1)
    #Add rows for "Per Week"
    elif filters.period_filter == "Pro Woche":
        #get first day of cw1
        first_day_of_cw = get_first_day_of_first_cw(filters.year_filter).date()
        
        while first_day_of_cw < today:
            #get last day of cw
            last_day_of_cw = frappe.utils.add_days(first_day_of_cw, 6)
            
            #create a new dict for the actual week
            rows.append({
                'period': "{0} - {1}".format(first_day_of_cw.strftime("%d.%m.%Y"), last_day_of_cw.strftime("%d.%m.%Y")),
                'from': first_day_of_cw,
                'to': last_day_of_cw
            })
            
            #Update First Day of CW
            first_day_of_cw = frappe.utils.add_days(first_day_of_cw, 7)
    elif filters.period_filter == "Pro Monat":
        #Get the first of january
        first_day_of_month = datetime.date(filters.year_filter, 1, 1)
        
        while first_day_of_month < today:
            #get last day of the month
            last_day_of_month = frappe.utils.add_days(frappe.utils.add_months(first_day_of_month, 1), -1)
            
            #create a new dict for the actual week
            rows.append({
                'period': "{0} - {1}".format(first_day_of_month.strftime("%d.%m.%Y"), last_day_of_month.strftime("%d.%m.%Y")),
                'from': first_day_of_month,
                'to': last_day_of_month
            })
            
            #Update First Day of CW
            first_day_of_month = frappe.utils.add_months(first_day_of_month, 1)
        
    return rows
        
