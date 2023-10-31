# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_working_days, get_content
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Data", "width": 100},
        {"label": _("Drilling Team"), "fieldname": "drilling_team", "fieldtype": "Data", "width": 100},
        {"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Data", "width": 100},
        {"label": _("Start Half Day"), "fieldname": "start_half_day", "fieldtype": "Data", "width": 100},
        {"label": _("End Date"), "fieldname": "end_date", "fieldtype": "Data", "width": 100},
        {"label": _("End Half Day"), "fieldname": "end_half_day", "fieldtype": "Data", "width": 100},
        {"label": _("Meters"), "fieldname": "meters", "fieldtype": "Data", "width": 100},
        {"label": _("Project Type"), "fieldname": "project_type", "fieldtype": "Data", "width": 100}
    ]
    return columns

def get_data(filters):   
    date_matrix = {}
    content = get_content(filters.from_date, filters.to_date)
    
    days = {}
    for date in content['day_list']:
        days[date] = 0
    
    for drilling_team in content['drilling_teams']:

        sql_query = """
        SELECT
            `name` AS `project`,
            `drilling_team`,
            `expected_start_date` AS `start_date`,
            `start_half_day`,
            `expected_end_date` AS `end_date`,
            `end_half_day`,
            (SELECT SUM(`ews_count` * `ews_depth`)
            FROM `tabObject EWS`
            WHERE `parent` = `tabProject`.`object`) AS `meters`,
            `project_type`
        FROM `tabProject`
        WHERE ((`expected_start_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_end_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_start_date` < '{from_date}' AND `expected_end_date` > '{to_date}')
            )
        AND `drilling_team` = '{drill_team}'
    """.format(from_date=filters.from_date, to_date=filters.to_date, drill_team=drilling_team.team_id)
        
        projects = frappe.db.sql(sql_query, as_dict=True)
        
        frappe.log_error(projects, "projects")
        
        #initilize each day for drilling team
        date_matrix['drilling_team'] = drilling_team['team_id']
        date_matrix['days'] = days
        
        for project in projects:
            if project['meters']:
                project['working_days'] = get_working_days(project['start_date'], project['start_half_day'], project['end_date'], project['end_half_day'])
                project['m_per_halfday'] = project['meters'] / project['working_days'] / 2
            if project['start_date'] < filters.from_date:
                project['start_date'] = filters.from_date
                project['start_half_day'] = "VM"
            if project['end_date'] > filters.end_date:
                project['end_date'] = filters.end_date
                project['start_half_day'] = "NM"
                
                # get affected half days
                affected_half_days = []
                current_day = project['start_date']
                while current_day <= project['end_date']:
                    if current_day.strftime("%d.%m.%Y") in content['weekend']:
                        current_day += timedelta(days=1)
                    else:
                        if current_day == project['start_date'] and project['start_half_day'] == "NM" or current_day == project['end_date'] and project['end_half_day'] == "VM":
                            affected_half_days.append(current_day.strftime("%d.%m.%Y"))
                            current_day += timedelta(days=1)
                        else:
                            affected_half_days.append(current_day.strftime("%d.%m.%Y"))
                            affected_half_days.append(current_day.strftime("%d.%m.%Y"))
                            current_day += timedelta(days=1)
            frappe.log_error(affected_half_days, "affected_half_days")    
            for half_day in affected_half_days:
                date_matrix['days'][half_day] += project['m_per_halfday']
            # ~ date_matrix[drilling_team][half_day] += project['project_type']
                    
        # ~ frappe.log_error(date_matrix, "date_matrix")
        
                
            
        # ~ actual_team = []
        # ~ actual_team.append({drilling_team.team_id: days})
        # ~ data.append(actual_team)
        
        
    

    # ~ data = [
        # ~ [{'bohrteam': 0
    
    
    return projects
