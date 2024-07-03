# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, get_url_to_form
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_content

def execute(filters=None):
    columns, content = get_columns(filters)
    data = get_data(filters, content)
    return columns, data

def get_columns(filters):
    content = get_content(filters.from_date, filters.to_date, only_teams=True)
    
    columns = [
        {'fieldname': 'drilling_team', 'label': _("Drilling Team"), 'fieldtype': 'Data', 'width': 120}
    ]
    
    for day in content.get('days'):
        if not day in content.get('weekend'):
            columns.append({
                'fieldname': day.replace(".", "_"), 
                'label': day, 
                'fieldtype': 'Data', 
                'width': 80
            })
    
    return columns, content
    
def get_data(filters, content):
    data = []
    
    for drilling_team in content.get('drilling_teams'):
        row = {
            'drilling_team': drilling_team.get('title')
        }
        for day in content.get('days'):
            if day in content.get('weekend'):
                display = ""
            else:
                display = get_display_per_day(drilling_team.get('team_id'), "{0}-{1}-{2}".format(day[6:10], day[3:5], day[0:2]))
            row[day.replace(".", "_")] = display
        
        data.append(row)
        
    return data

def get_project_gps_per_day(drilling_team, date):
    # get projects on a specific day
    projects = frappe.db.sql("""
        SELECT 
            `tabProject`.`name` AS `project`,
            `tabObject`.`gps_lat` AS `gps_lat`,
            `tabObject`.`gps_long` AS `gps_long`,
            `tabObject`.`object_location` AS `object_location`
        FROM `tabProject`
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
        WHERE 
            `tabProject`.`object` IS NOT NULL
            AND `tabProject`.`project_type` = "External"
            AND `tabProject`.`expected_start_date` <= "{date}"
            AND `tabProject`.`expected_end_date` >= "{date}"
            AND `tabProject`.`drilling_team` = "{drilling_team}"
        ;""".format(drilling_team=drilling_team, date=date), as_dict=True)
        
    return projects
        
def get_display_per_day(drilling_team, date):
    projects = get_project_gps_per_day(drilling_team, date)
    display = ""
    if len(projects) > 0:
        for project in projects:
            display += "<a href='{2}' target='_blank' title='{0}, {3}'>{0}</a> ({1}) ".format(
                project.get('project'), 
                (project.get('object_location') or "")[0:4],
                get_url_to_form("Project", project.get('project')),
                project.get('object_location') or ""
            )
        
        r, g = get_gps_color(project.get('gps_lat') or 0, project.get('gps_long') or 0)
        
        display = "<span style='background-color: rgb({r}, {g}, {r}); '>{d}</span>".format(
            r=r, g=g, d=display)
    
    return display
    
def get_gps_color(gps_lat, gps_long):
    g = cint((gps_lat - 46.3)/(1.6/255))
    if g < 0:
        g = 0
    elif g > 255:
        g = 255
    r = cint((gps_long - 6.9)/(3.6/255))
    if r < 0:
        r = 0
    elif r > 255:
        r = 255
    return r, g
    
