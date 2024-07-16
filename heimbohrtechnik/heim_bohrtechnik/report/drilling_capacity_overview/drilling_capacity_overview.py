# Copyright (c) 2013, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_working_days, get_content
from datetime import datetime, timedelta
from frappe.utils.data import getdate
from heimbohrtechnik.heim_bohrtechnik.date_controller import get_holidays
from erpnextswiss.erpnextswiss.utils import get_first_day_of_first_cw
from frappe.utils.data import getdate, date_diff

def execute(filters=None):
    data, weekend = get_data(filters)
    columns = get_columns(data, weekend)
    return columns, data

def get_columns(data, weekend):
    columns = []
    for key, value in data[0].items():
        width = 80
        if key == "Bohrteam":
            width = 150
            columns.append({"label": _(key), "fieldname": key, "fieldtype": "Link", "options": "Drilling Team", "width": width})
        else:
            if key in weekend:
                width = 20
            columns.append({"label": _(key), "fieldname": key, "fieldtype": "Data", "width": width})
    
    return columns

def get_data(filters): 
    data = []
    date_matrix = {}
    
    #get the lists of days, weekends and drilling teams for period
    content = get_content(filters.from_date, filters.to_date)
    
    #get all projects for period per drilling team 
    for drilling_team in content['drilling_teams']:
        if drilling_team['team_id'] == "BT-Parkplatz":
            break
        else:
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
            
            #initilize each day for drilling team
            date_matrix[drilling_team['team_id']] = {}
            for key in content['day_list']:
               date_matrix[drilling_team['team_id']][key] = 0
            
            #add working days and meter per half day to each project
            for project in projects:
                if project['meters']:
                    project['working_days'] = get_working_days(project['start_date'], project['start_half_day'], project['end_date'], project['end_half_day'])
                    project['m_per_halfday'] = project['meters'] / project['working_days'] / 2
                else:
                    project['working_days'] = get_working_days(project['start_date'], project['start_half_day'], project['end_date'], project['end_half_day'])
                    project['m_per_halfday'] = None
                    
                #cut projects to period
                if project['start_date'] < datetime.strptime(filters.from_date, "%Y-%m-%d").date():
                    project['start_date'] = datetime.strptime(filters.from_date, "%Y-%m-%d").date()
                    project['start_half_day'] = "VM"
                if project['end_date'] > datetime.strptime(filters.to_date, "%Y-%m-%d").date():
                    project['end_date'] = datetime.strptime(filters.to_date, "%Y-%m-%d").date()
                    project['end_half_day'] = "NM"
                   
                # get affected half days
                affected_half_days = []
                current_day = project['start_date']
                while current_day <= project['end_date']:
                    if current_day.strftime("%d.%m.%Y") in content['weekend']:
                        current_day += timedelta(days=1)
                    else:
                        if (current_day == project['start_date'] and project['start_half_day'] == "NM") or (current_day == project['end_date'] and project['end_half_day'] == "VM"):
                            affected_half_days.append(current_day.strftime("%d.%m.%Y"))
                            current_day += timedelta(days=1)
                        else:
                            affected_half_days.append(current_day.strftime("%d.%m.%Y"))
                            affected_half_days.append(current_day.strftime("%d.%m.%Y"))
                            current_day += timedelta(days=1)
                #ad project meters of each half day to each day of drilling team
                for half_day in affected_half_days:
                    if project['m_per_halfday'] is not None:
                        date_matrix[drilling_team['team_id']][half_day] += project['m_per_halfday']
                    elif project['project_type'] == "Internal":
                        date_matrix[drilling_team['team_id']][half_day] = -1
                for weekend in content['weekend']:
                    date_matrix[drilling_team['team_id']][weekend] = -2
        
            dt_data = {}
            dt_data['Bohrteam'] = drilling_team['team_id']
            dt_data['Capacity'] = 0
            for key, value in date_matrix[drilling_team['team_id']].items():
                dt_data[key] = int(value)
                if value == 0:
                    dt_data['Capacity'] += 1
            data.append(dt_data)
            
    weekend = content['weekend']
    
    return data, weekend

@frappe.whitelist()   
# ~ """
# ~ Parameters:
# ~ drilling_type: should be the fieldname of the drilling team checkbox
# ~ """
def get_free_date(drilling_type, label):    
    #get non working days
    holidays = get_holidays()
    
    #get all drilling teams with needed ability
    drilling_teams = frappe.db.sql("""
    SELECT `name`
    FROM `tabDrilling Team`
    WHERE `{dt}` = 1
    """.format(dt=drilling_type), as_dict=True)
    
    #give feedback, if no team has the needed ability
    if len(drilling_teams) == 0:
        frappe.msgprint("Kein Bohrteam mit dieser Fähigkeit gefunden!")
        return
        
    hits = []
    for team in  drilling_teams:
        dt_hits = []
        #get today
        date = getdate()
        actual_hit = None
        actual_hit_list = []
        #check for the dates, where teams are free
        while len(dt_hits) <= 4:
            if actual_hit_list and len(actual_hit_list) > 20:
                actual_hit_list.append("end")
                dt_hits.append({
                    'date': actual_hit_list
                })
                break
            date = frappe.utils.add_days(date, 1)
            possible_hit = []
            possible_hit = frappe.db.sql("""
                SELECT `drilling_team`
                FROM `tabProject`
                WHERE `expected_start_date` <= '{date}'
                AND `expected_end_date` >= '{date}'
                AND `drilling_team` = '{team}'
                AND `status` IN ("Open", "Completed")
                """.format(date=date, team=team['name']), as_dict=True)
            if len(possible_hit) == 0:
                if not actual_hit:
                    if date.strftime("%Y-%m-%d") in holidays:
                        actual_hit = date
                        actual_hit_list = []
                    else:
                        actual_hit = date
                        actual_hit_list.append(date.strftime("%d.%m.%Y"))
                else:
                    if date_diff(date, actual_hit) == 1:
                        if date.strftime("%Y-%m-%d") in holidays:
                            actual_hit = date
                        else:
                            actual_hit = date
                            actual_hit_list.append(date.strftime("%d.%m.%Y"))
                    else:
                        if len(actual_hit_list) > 0:
                            dt_hits.append({
                                'date': actual_hit_list
                            })
                            actual_hit = None
                            actual_hit_list = []
                        if date.strftime("%Y-%m-%d") in holidays:
                            actual_hit = date
                            actual_hit_list = []
                        else:
                            actual_hit = date
                            actual_hit_list.append(date.strftime("%d.%m.%Y"))
        hits.append({
            'drilling_team': team.name,
            'dates': dt_hits
        })
        
    frappe.log_error(hits, "hits")
                
    html = frappe.render_template("heimbohrtechnik/heim_bohrtechnik/report/drilling_capacity_overview/free_days.html", {'hits': hits})
                
    frappe.msgprint(html, title='Freie Tage für {0}'.format(label), indicator='green')
            
    return "Done"

@frappe.whitelist()
def get_filter_dates(calendar_week, year, start_check=False):
    frappe.log_error(start_check)
    monday_cw1 = get_first_day_of_first_cw(int(year))
    if start_check == "1":
        from_date = frappe.utils.add_days(monday_cw1, (int(calendar_week) - 1) * 7)
    else:
        from_date = getdate()
    diff = (int(calendar_week) - 1) * 7 + 4
    to_date = frappe.utils.add_days(monday_cw1, diff)
    return from_date, to_date
