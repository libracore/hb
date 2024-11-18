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
def insert_feedback(drilling_team, deputy, date, project, project_meter, project2, project_meter2, drilling_meter, flushing, hammer_change, impact_part_change, assistant_1, assistant_2, temporary, hotel_night, description_06_07, description_07_08, description_08_09, description_09_10, description_10_11, description_11_12, description_12_13, description_13_14, description_14_15, description_15_16, description_16_17, description_17_18, description_18_19,  description_19_20,  description_20_21,  description_21_22,  notes, finished_document, link_key):
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
        if hotel_night == "Ja":
            hotel_night_check = 1
        else:
            hotel_night_check = 0
        # create new record
        if not project2:
            create_document(drilling_team, deputy, date, project, project_meter, project2, project_meter2, drilling_meter, flushing_check, hammer_change_check, impact_part_change_check, assistant_1, assistant_2, temporary, hotel_night_check, description_06_07, description_07_08, description_08_09, description_09_10, description_10_11, description_11_12, description_12_13, description_13_14, description_14_15, description_15_16, description_16_17, description_17_18, description_18_19,  description_19_20,  description_20_21,  description_21_22,  notes, finished_document, second_project_row=False)
        else:
            create_document(drilling_team, deputy, date, project, project_meter, project2, project_meter2, drilling_meter, flushing_check, hammer_change_check, impact_part_change_check, assistant_1, assistant_2, temporary, hotel_night_check, description_06_07, description_07_08, description_08_09, description_09_10, description_10_11, description_11_12, description_12_13, description_13_14, description_14_15, description_15_16, description_16_17, description_17_18, description_18_19,  description_19_20,  description_20_21,  description_21_22,  notes, finished_document, second_project_row=True)
        return

@frappe.whitelist(allow_guest=True)
def check_key(link_key, team):
    
    #get Team Key
    team_key = frappe.db.get_value("Drilling Team", team, "team_key")
    
    #validate key and prepare response
    is_valid = False 
    if link_key == team_key:
        is_valid = True
        projects = get_projects(team)
        projects_html = frappe.render_template("heimbohrtechnik/templates/pages/projects_template.html", {'projects': projects})
        descriptions = get_descriptions()
        descriptions_html = frappe.render_template("heimbohrtechnik/templates/pages/descriptions_template.html", {'descriptions': descriptions})
    else:
        frappe.msgprint("Invalid or missing Key!")
    
    
    return {'is_valid': is_valid, 'projects_html': projects_html, 'descriptions_html': descriptions_html}

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
    
def get_descriptions():
#get projects in period
    data = frappe.db.sql("""
        SELECT `value`
        FROM `tabDaily Feedback Description`""", as_dict=True)
    
    #get a list with the descriptions as values
    descriptions = []
    for description in data:
          descriptions.append(description['value'])

    return descriptions
    
@frappe.whitelist(allow_guest=True)
def get_deputy_list():
    deputys = frappe.db.sql("""
        SELECT 
            `name`
        FROM 
            `tabDrilling Team`
        WHERE 
            `drilling_team_type` = 'Bohrteam'""", as_dict=True)
    
    employees = frappe.db.sql("""
        SELECT 
            `employee_name`
        FROM 
            `tabEmployee`
        WHERE 
            `is_drilling_team_deputy` = 1""", as_dict=True)
    
    deputy_list = []
    for deputy in deputys:
        deputy_list.append(deputy.name)
    
    for employee in employees:
        deputy_list.append("M - " + employee.employee_name)
    
    return deputy_list

def create_document(drilling_team, deputy, date, project, project_meter, project2, project_meter2, drilling_meter, flushing_check, hammer_change_check, impact_part_change_check, assistant_1, assistant_2, temporary, hotel_night_check, description_06_07, description_07_08, description_08_09, description_09_10, description_10_11, description_11_12, description_12_13, description_13_14, description_14_15, description_15_16, description_16_17, description_17_18, description_18_19,  description_19_20,  description_20_21,  description_21_22,  notes, finished_document, second_project_row=False):
    #check if already a document is existing for this day / drilling team
    feedback = frappe.get_list(doctype="Feedback Drilling Meter", filters={'date': date, 'drilling_team': drilling_team}, ignore_permissions=True)
    if feedback:
        #if doc is existing, delete it
        feedback_doc = frappe.delete_doc("Feedback Drilling Meter", feedback[0].get('name'), ignore_permissions=True)
        
    #create new doc
    feedback_doc = frappe.get_doc({
        'doctype': 'Feedback Drilling Meter',
        'drilling_team': drilling_team,
        'date': date,
        'drilling_meter': drilling_meter,
        'flushing': flushing_check,
        'hammer_change': hammer_change_check,
        'impact_part_change': impact_part_change_check,
        'drilling_assistant_1': assistant_1,
        'drilling_assistant_2': assistant_2,
        'temporary': temporary,
        'hotel_night': hotel_night_check,
        'finished_document': finished_document,
        #Create subtable "layers" for projects
        'project': [{
        'reference_doctype': "Feedback Drilling Meter Project",
        'project_number': project,
        'project_meter': project_meter
        }],
        #Create subtable "layers" for description
        'description': [{
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "06:00 - 07:00",
        'description': description_06_07
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "07:00 - 08:00",
        'description': description_07_08
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "08:00 - 09:00",
        'description': description_08_09
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "09:00 - 10:00",
        'description': description_09_10
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "10:00 - 11:00",
        'description': description_10_11
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "11:00 - 12:00",
        'description': description_11_12
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "12:00 - 13:00",
        'description': description_12_13
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "13:00 - 14:00",
        'description': description_13_14
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "14:00 - 15:00",
        'description': description_14_15
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "15:00 - 16:00",
        'description': description_15_16
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "16:00 - 17:00",
        'description': description_16_17
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "17:00 - 18:00",
        'description': description_17_18
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "18:00 - 19:00",
        'description': description_18_19
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "19:00 - 20:00",
        'description': description_19_20
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "20:00 - 21:00",
        'description': description_20_21
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "21:00 - 22:00",
        'description': description_21_22
        },
        {
        'reference_doctype': "Feedback Drilling Meter Description",
        'description_time': "Bemerkungen",
        'description': notes
        }]
    })
    
    if deputy != "Nein":
        feedback_doc.deputy = deputy

    if project2:
        project_entry = {
        'project_number': project2,
        'project_meter': project_meter2
        }
        feedback_doc.append('project', project_entry)
        
    feedback_doc = feedback_doc.insert(ignore_permissions=True)
    return

@frappe.whitelist(allow_guest=True)
def calculate_hammer_change(drilling_team):
    feedbacks = frappe.db.sql("""
                            SELECT
                                `date`,
                                `drilling_meter`,
                                `hammer_change`
                            FROM
                                `tabFeedback Drilling Meter`
                            WHERE
                                `drilling_team` = '{dt}'
                            ORDER BY
                                `date` DESC""".format(dt=drilling_team), as_dict=True)
    
    last_change = 0
    for feedback in feedbacks:
        last_change += feedback.get('drilling_meter')
        if feedback.get('hammer_change') == 1:
            break
    next_change = 10000 - last_change
    return last_change, next_change
    
@frappe.whitelist(allow_guest=True)
def calculate_impact_part_change(drilling_team):
    feedbacks = frappe.db.sql("""
                            SELECT
                                `date`,
                                `drilling_meter`,
                                `impact_part_change`
                            FROM
                                `tabFeedback Drilling Meter`
                            WHERE
                                `drilling_team` = '{dt}'
                            ORDER BY
                                `date` DESC""".format(dt=drilling_team), as_dict=True)
    
    last_change = 0
    for feedback in feedbacks:
        last_change += feedback.get('drilling_meter')
        if feedback.get('impact_part_change') == 1:
            break
    next_change = 3000 - last_change
    return last_change, next_change

@frappe.whitelist(allow_guest=True)
def get_transmitted_information(date, drilling_team):
    #get record for entered date
    record = frappe.db.sql("""
                            SELECT
                                `name`,
                                `date`,
                                `drilling_team`,
                                `deputy`,
                                `drilling_meter`,
                                `flushing`,
                                `hammer_change`,
                                `impact_part_change`,
                                `drilling_assistant_1`,
                                `drilling_assistant_2`,
                                `temporary`,
                                `hotel_night`
                            FROM
                                `tabFeedback Drilling Meter`
                            WHERE
                                `date` = '{date}'
                            AND
                                `drilling_team` = '{dt}'""".format(date=date, dt=drilling_team), as_dict=True)
    
    #if there is a record for this day, get projects and descriptions and return everything
    if len(record) > 0:
        projects = frappe.db.sql("""
                                SELECT
                                    `project_number`,
                                    `project_meter`
                                FROM
                                    `tabFeedback Drilling Meter Project`
                                WHERE
                                    `parent` = '{rec}'""".format(rec=record[0].get('name')), as_dict=True)
        
        descriptions = frappe.db.sql("""
                                    SELECT
                                        `description_time`,
                                        `description`
                                    FROM
                                        `tabFeedback Drilling Meter Description`
                                    WHERE
                                        `parent` = '{rec}'
                                    ORDER BY
                                        `description_time` ASC""".format(rec=record[0].get('name')), as_dict=True)
        
        return record, projects, descriptions
    else:
        return None
    
@frappe.whitelist(allow_guest=True)
def get_assistants_list():
    assistants = frappe.db.sql("""
        SELECT 
            `employee_name`
        FROM 
            `tabEmployee`
        WHERE 
            `designation` IN ('Bohrhelfer')
        AND
            `status` = 'Active'""", as_dict=True)
    
    assistants_list = []
    for assistant in assistants:
        assistants_list.append(assistant.get('employee_name'))
    
    return assistants_list
    
@frappe.whitelist(allow_guest=True)
def get_project_location(project):
    return frappe.get_value("Project", project, "object_location")
