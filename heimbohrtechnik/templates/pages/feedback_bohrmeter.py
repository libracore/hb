# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import datetime
from frappe.utils.data import getdate

@frappe.whitelist(allow_guest=True)
def insert_feedback(drilling_team, drilling_meter, date, project, project2, flushing, hammer_change, impact_part_change, link_key):
    #check key
    team_key = frappe.db.get_value("Drilling Team", drilling_team, "team_key")
    if link_key != team_key:
        frappe.msgprint("Invalid or missing Key!")
        return
    else:
        #Translate checkboxes
        if flushing == "Ja":
            flushing_check = 1
        else:
            flushing_check = 0
        if hammer_change == "Ja":
            hammer_change_check = 1
        else:
            hammer_change_check = 0
        if impact_part_change == "Ja":
            impact_part_change_check = 1
        else:
            impact_part_change_check = 0
        # create new record
        if not project2:
            feedback = frappe.get_doc({
                'doctype': 'Feedback Drilling Meter',
                'drilling_team': drilling_team,
                'drilling_meter': drilling_meter,
                'date': date,
                'flushing': flushing_check,
                'hammer_change': hammer_change_check,
                'impact_part_change': impact_part_change_check,
                #Create subtable "layers"
                "project": [{
                "reference_doctype": "Feedback Drilling Meter Project",
                "project_number": project
                    }]
            })
        else:
            feedback = frappe.get_doc({
                'doctype': 'Feedback Drilling Meter',
                'drilling_team': drilling_team,
                'drilling_meter': drilling_meter,
                'date': date,
                'flushing': flushing_check,
                'hammer_change': hammer_change_check,
                'impact_part_change': impact_part_change_check,
                #Create subtable "layers"
                "project": [{
                "reference_doctype": "Feedback Drilling Meter Project",
                "project_number": project
                },
                {
                "reference_doctype": "Feedback Drilling Meter Project",
                "project_number": project2
                }]
            })
        feedback = feedback.insert(ignore_permissions=True)
        feedback.submit()
        return {'feedback': feedback.name}

@frappe.whitelist(allow_guest=True)
def check_key(link_key, team):
    
    #get Team Key
    team_key = frappe.db.get_value("Drilling Team", team, "team_key")
    
    #validate key and prepare response
    if link_key == team_key:
        response = True
        projects = get_projects(team)
        projects_html = frappe.render_template("heimbohrtechnik/templates/pages/projects_template.html", {'projects': projects})
    else:
        response = False  
        frappe.msgprint("Invalid or missing Key!")
    
    
    return response, projects_html

def get_projects(team):
    #get today and calculate start and end date of period
    today = getdate()
    period_start = frappe.utils.add_days(today, -5)
    period_end = frappe.utils.add_days(today, 2)
    
    #get projects in period
    data = frappe.db.sql("""
        SELECT `name`
        FROM `tabProject`
        WHERE ((`expected_start_date` >= '{ps}' AND `expected_start_date` <= '{pe}')
        OR (`expected_end_date` >= '{ps}' AND `expected_end_date` <= '{pe}')
        OR (`expected_start_date` < '{ps}' AND `expected_end_date` > '{pe}'))
        AND `drilling_team` = '{team}'
        AND `status` IN ("Open", "Completed")
        """.format(team=team, ps=period_start, pe=period_end), as_dict=True)
        
    #get a list with the projects as values
    projects = []
    for project in data:
          projects.append(project['name'])
        
    return projects
