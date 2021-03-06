# -*- coding: utf-8 -*-
# Copyright (c) 2017-2021, libracore and contributors

from __future__ import unicode_literals
import frappe
from frappe.utils.data import getdate, date_diff
from datetime import date, timedelta

@frappe.whitelist()
def get_content(from_date, to_date):
    data = {}
    data["drilling_teams"] = get_drilling_teams()
    data["days"], data["total_width"] = get_days(from_date, to_date)
    return data
    
def get_days(from_date, to_date):
    start_date = getdate(from_date)
    end_date = getdate(to_date)
    date_list = []
    total_width = 0
    
    delta = timedelta(days=1)
    while start_date <= end_date:
        date_list.append(start_date.strftime("%d.%m.%Y"))
        start_date += delta
        total_width += 1
        
    total_width = (total_width * 161) + 247
    
    return date_list, total_width
    
def get_drilling_teams():
    drilling_teams = []
    _drilling_teams = frappe.db.sql("""SELECT `name` FROM `tabDrilling Team`""", as_list=True)
    
    for team in _drilling_teams:
        data = {}
        data["team"] = team[0]
        data["booked_days"], data["booked_vm_start_days"], data["booked_nm_start_days"], data["booked_vm_end_days"], data["booked_nm_end_days"], data["project_details"] = get_booked_days_of_drilling_team(team[0])
        drilling_teams.append(data)
    
    return drilling_teams
    
def get_booked_days_of_drilling_team(team):
    booked_days = []
    booked_vm_start_days = []
    booked_nm_start_days = []
    booked_vm_end_days = []
    booked_nm_end_days = []
    project_details = {}
    
    projects = frappe.db.sql("""SELECT
                                `expected_start_date`,
                                `expected_end_date`,
                                `start_half_day`,
                                `end_half_day`,
                                `object`,
                                `object_name`,
                                `object_location`,
                                `ews_details`
                            FROM `tabProject` WHERE `drilling_team` = '{team}'""".format(team=team), as_dict=True)
    for project in projects:
        delta = timedelta(days=1)
        
        start_date = getdate(project.expected_start_date)
        end_date = getdate(project.expected_end_date)
        
        if project.start_half_day == 'VM':
            booked_vm_start_days.append(start_date.strftime("%d.%m.%Y"))
            project_details[start_date.strftime("%d.%m.%Y")] = {
                'object': project.object,
                'object_name': project.object_name,
                'object_location': project.object_location,
                'ews_details': project.ews_details
            }
        else:
            booked_nm_start_days.append(start_date.strftime("%d.%m.%Y"))
            project_details[start_date.strftime("%d.%m.%Y")] = {
                'object': project.object,
                'object_name': project.object_name,
                'object_location': project.object_location,
                'ews_details': project.ews_details
            }
        start_date += delta
        
        
        if project.end_half_day == 'VM':
            booked_vm_end_days.append(end_date.strftime("%d.%m.%Y"))
            project_details[end_date.strftime("%d.%m.%Y")] = {
                'object': project.object,
                'object_name': project.object_name,
                'object_location': project.object_location,
                'ews_details': project.ews_details
            }
        else:
            booked_nm_end_days.append(end_date.strftime("%d.%m.%Y"))
            project_details[end_date.strftime("%d.%m.%Y")] = {
                'object': project.object,
                'object_name': project.object_name,
                'object_location': project.object_location,
                'ews_details': project.ews_details
            }
        
        while start_date < end_date:
            booked_days.append(start_date.strftime("%d.%m.%Y"))
            dauer = date_diff(end_date, start_date)
            project_details[start_date.strftime("%d.%m.%Y")] = {
                'object': project.object,
                'object_name': project.object_name,
                'object_location': project.object_location,
                'ews_details': project.ews_details
            }
            start_date += delta
    
    return booked_days, booked_vm_start_days, booked_nm_start_days, booked_vm_end_days, booked_nm_end_days, project_details