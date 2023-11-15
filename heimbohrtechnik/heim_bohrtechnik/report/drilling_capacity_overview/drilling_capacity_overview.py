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
        elif key in weekend:
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
def get_free_date(drilling_type):
    #convert drilling type to field name
    def get_convertet_dt(dt):
        try:
            mapper = {
                'Spühlbohrung': 'flushing_drilling',
                'Hammerbohrung': 'hammer_drilling',
                'Brunnenbohrung': 'well_drilling',
                'Kleinbohrgerät auf Bohrteam': 'small_drilling_rig'
            }
            return mapper[dt]
        except Exception as err:
            frappe.throw("{0} wurde nicht gefunden".format(err))
    
    # create table-rows for each hit
    def get_table_rows(hits):
        html = ''
        for hit in hits:
            html += '''<tr><td>{0}</td><td>{1}</td></tr>'''.format(\
                hit['drilling_team'], \
                hit['date'].strftime("%d.%m.%Y"))
        return html
    
    #get non working days
    holidays = get_holidays()

    #get all drilling teams with needed ability
    drilling_teams = frappe.db.sql("""
    SELECT `name`
    FROM `tabDrilling Team`
    WHERE `{dt}` = 1
    """.format(dt=get_convertet_dt(drilling_type)), as_dict=True)
    
    #give feedback, if no team has the needed ability
    if len(drilling_teams) == 0:
        frappe.msgprint("Kein Bohrteam mit dieser Fähigkeit gefunden!")
        return
    
    hits = []
    date = getdate()
    
    #check for the dates, where teams are free
    while len(hits) <= 9:
        date = frappe.utils.add_days(date, 1)
        if not date.strftime("%Y-%m-%d") in holidays:
            for team in drilling_teams:
                possible_hit = None
                possible_hit = frappe.db.sql("""
                    SELECT `drilling_team`
                    FROM `tabProject`
                    WHERE `expected_start_date` <= '{date}'
                    AND `expected_end_date` >= '{date}'
                    AND `drilling_team` = '{team}'
                    """.format(date=date, team=team['name']), as_dict=True)
                if len(possible_hit) == 0:
                    hits.append({
                        'drilling_team': team.name,
                        'date': date
                    })
                    
    msg_html = '''
        <table style="width: 70%">
            <tr>
                <th>Bohrteam</th>
                <th>Datum</th>
            </tr>
            {0}
        </table>'''.format(get_table_rows(hits))
    frappe.msgprint(msg_html, title='Freie Tage für {0}'.format(drilling_type), indicator='green')
                
    return
