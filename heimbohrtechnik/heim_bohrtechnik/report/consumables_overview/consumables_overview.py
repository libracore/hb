# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnextswiss.erpnextswiss.utils import get_first_day_of_first_cw
# ~ from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_days
# ~ from frappe.utils.data import getdate
import datetime
# ~ from frappe.utils import get_url_to_form


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": _("Period"), "fieldname": "period", "fieldtype": "Data", "width": 200},
        {"label": _("Bentonite"), "fieldname": "bentonite", "fieldtype": "Int", "width": 100},
        # ~ {"label": _("Per Meter"), "fieldname": "bentonite_per_meter", "fieldtype": "Int", "width": 100},
        {"label": _("Zement"), "fieldname": "zement", "fieldtype": "Int", "width": 100},
        # ~ {"label": _("Per Meter"), "fieldname": "zement_per_meter", "fieldtype": "Int", "width": 100},
        {"label": _("Thermozement"), "fieldname": "thermozement", "fieldtype": "Int", "width": 100},
        # ~ {"label": _("Per Meter"), "fieldname": "thermozement_per_meter", "fieldtype": "Int", "width": 100},
        {"label": _("Antisol"), "fieldname": "antisol", "fieldtype": "Int", "width": 100},
        # ~ {"label": _("Per Meter"), "fieldname": "antisol_per_meter", "fieldtype": "Int", "width": 100},
        {"label": _("Total Consumables"), "fieldname": "total", "fieldtype": "Int", "width": 100},
        {"label": _("Total Drilling Meter"), "fieldname": "drilling_meter", "fieldtype": "Int", "width": 100},
        {"label": _("Per Meter"), "fieldname": "total_per_meter", "fieldtype": "Int", "width": 100}
    ]
    
    return columns

def get_data(filters):
    year_total = 0
    rows = get_rows(filters)
    
    for row in rows:
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
                                `finished_document` = 1""".format(date_condition=date_condition, drilling_team_condition=drilling_team_condition)
    return rows

def get_rows(filters):
    #get today and preapre rows
    rows = []
    today = datetime.date.today() 
    
    #Add rows for "Per Day"
    if filters.period_filter == "Per Day":
        current_date = datetime.date(filters.year_filter, 1, 1)
        while current_date < today:
            rows.append({'period': current_date.strftime("%d.%m.%Y")})
            current_date = frappe.utils.add_days(current_date, 1)
    #Add rows for "Per Week"
    elif filters.period_filter == "Per Week":
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
    elif filters.period_filter == "Per Month":
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
        
