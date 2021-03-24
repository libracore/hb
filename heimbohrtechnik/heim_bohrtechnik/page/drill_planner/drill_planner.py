# -*- coding: utf-8 -*-
# Copyright (c) 2017-2021, libracore and contributors

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import getdate, date_diff, add_days
from datetime import date, timedelta

@frappe.whitelist()
def get_content(from_date, to_date):
    data = {}
    data["drilling_teams"] = get_drilling_teams()
    data["days"], data["total_width"], data["weekend"], data["kw_list"], data["day_list"] = get_days(from_date, to_date)
    return data
    
def get_days(from_date, to_date):
    start_date = getdate(from_date)
    end_date = getdate(to_date)
    date_list = []
    weekend_list = []
    kw_list = {}
    day_list = {}
    total_width = 0
    total_weekday = 0
    total_weekend = 0
    
    delta = timedelta(days=1)
    while start_date <= end_date:
        date_list.append(start_date.strftime("%d.%m.%Y"))
        kw_list[start_date.strftime("%d.%m.%Y")] = start_date.strftime("%V")
        day_list[start_date.strftime("%d.%m.%Y")] = start_date.strftime("%a")
        week_day_no = start_date.weekday()
        if week_day_no >= 5:
            weekend_list.append(start_date.strftime("%d.%m.%Y"))
            total_weekend += 1
        else:
            total_weekday += 1
        start_date += delta
        
    total_width = (total_weekday * 161) + (total_weekend * 80) + 247
    
    return date_list, total_width, weekend_list, kw_list, day_list
    
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
            project_details[start_date.strftime("%d.%m.%Y")] = {
                'object': project.object,
                'object_name': project.object_name,
                'object_location': project.object_location,
                'ews_details': project.ews_details
            }
            start_date += delta
    
    return booked_days, booked_vm_start_days, booked_nm_start_days, booked_vm_end_days, booked_nm_end_days, project_details
    
@frappe.whitelist()
def reschedule_project(project=None, team=None, day=None, start_half_day=None, popup=False, new_project_start=None, new_project_end_date=None, end_half_day=None):
    project = frappe.get_doc("Project", project)
    
    if not popup:
        start_date = project.expected_start_date
        end_date = project.expected_end_date
        project_duration = date_diff(end_date, start_date)
        delta = timedelta(days=project_duration)
        
        new_project_start_day = day.split(".")[0]
        new_project_start_month = day.split(".")[1]
        new_project_start_year = day.split(".")[2]
        new_project_start = getdate(new_project_start_year + "-" + new_project_start_month + "-" + new_project_start_day)
        
        new_project_end_date = new_project_start
        new_project_end_date += delta
        
        project.expected_start_date = new_project_start
        project.expected_end_date = new_project_end_date
        
        if project.start_half_day != start_half_day:
            old_start_hd = project.start_half_day
            project.start_half_day = start_half_day
            if old_start_hd == 'NM':
                if project.end_half_day == 'NM':
                    project.end_half_day = 'VM'
                else:
                    project.end_half_day = 'NM'
                    project.expected_end_date = add_days(project.expected_end_date, -1)
            else:
                if project.end_half_day == 'VM':
                    project.end_half_day = 'NM'
                else:
                    project.end_half_day = 'VM'
                    project.expected_end_date = add_days(project.expected_end_date, 1)
        
        project.drilling_team = team
        
        project.save()
    else:
        project.expected_start_date = new_project_start
        project.expected_end_date = new_project_end_date
        project.start_half_day = start_half_day
        project.end_half_day = end_half_day
        project.drilling_team = team
        
        project.save()
        

@frappe.whitelist()
def get_overlay_data(project, selected_start, selected_end):
    data = {}
    data['a1'] = get_traffic_lights_indicator(project, 'a1')
    data['a2'] = get_traffic_lights_indicator(project, 'a2')
    data['a3'] = get_traffic_lights_indicator(project, 'a3')
    data['a4'] = get_traffic_lights_indicator(project, 'a4')
    data['a5'] = get_traffic_lights_indicator(project, 'a5')
    data['a6'] = get_traffic_lights_indicator(project, 'a6')
    data['a7'] = get_traffic_lights_indicator(project, 'a7')
    
    project = frappe.get_doc("Project", project)
    start_date = getdate(project.expected_start_date)
    end_date = getdate(project.expected_end_date)
    start_overwritten = False
    end_overwritten = False
    
    if getdate(selected_start) > start_date:
        start_date = getdate(selected_start)
        start_overwritten = True
    
    if getdate(selected_end) < end_date:
        end_date = getdate(selected_end)
        end_overwritten = True
    
    total_weekend = 0
    total_weekday = 0
    
    if not start_overwritten:
        if project.start_half_day == 'NM':
            if getdate(project.expected_start_date).weekday() >= 5:
                total_weekend -= 1
            else:
                total_weekday -= 1
    
    if not end_overwritten:
        if project.end_half_day == 'VM':
            if getdate(project.expected_end_date).weekday() >= 5:
                total_weekend -= 1
            else:
                total_weekday -= 1
    
    delta = timedelta(days=1)
    while start_date <= end_date:
        week_day_no = start_date.weekday()
        if week_day_no >= 5:
            total_weekend += 2
        else:
            total_weekday += 2
        start_date += delta
        
    total_overlay_width = (total_weekday * 80) + (total_weekend * 40)
    data['total_overlay_width'] = total_overlay_width
    
    return data

def get_traffic_lights_indicator(project, typ):
    # Ampeln:
    # a1 = Baustelle besichtigt: rot/grün (Checkbox)
    # a2 = Bewilligungen: von Untertabelle jede als Dokument (rot nichts, gelb einige, grün alle)
    # a3 = Kundenauftrag: Rot fehlt, gelb auf Entwurf, grün gültig
    # a4 = Materialstatus: rot fehlt/gelb bestellt (Lieferantenauftrag)/grün an Lager (Wareneingang)
    # a5 = Kran benötigt? (grau nein, rot nicht geplant, grün organisiert)
    # a6 = Bohrschlammentsorgung (rot: keiner, grün ein Schlammentsorger (Lieferant) im Objekt)
    # a7 = Bohranzeige versendet (Checkbox auf Projekt)
                                 
    project = frappe.get_doc("Project", project)
    drilling_object = frappe.get_doc("Object", project.object)
    
    if typ == 'a1':
        if drilling_object.construction_site_inspected == 1:
            return {
                'color': 'green',
                'tooltip': _('The construction site was visited')
            }
        else:
            return {
                'color': 'red',
                'tooltip': _("The construction site was <b>not</b> visited")
            }
    
    # tbd!
    if typ == 'a2':
        return {
            'color': 'red',
            'tooltip': _("This tooltip is an example and still needs to be programmed")
        }
    
    if typ == 'a3':
        if not project.sales_order:
            return {
                'color': 'red',
                'tooltip': _("No sales order available")
            }
        else:
            sales_order = frappe.get_doc("Sales Order", project.sales_order)
            if sales_order.docstatus == 1:
                return {
                    'color': 'green',
                    'tooltip': _("The sales order is submitted")
                }
            elif  sales_order.docstatus == 0:
                return {
                    'color': 'yellow',
                    'tooltip': _("The sales order is <b>not</b> submitted")
                }
            else:
                return {
                    'color': 'red',
                    'tooltip': _("The sales order is cancelled")
                }
    
    # tbd!
    if typ == 'a4':
        return {
            'color': 'red',
            'tooltip': _("This tooltip is an example and still needs to be programmed")
        }
    
    if typ == 'a5':
        if project.crane_required == 0:
            return {
                'color': 'grey',
                'tooltip': _("No crane is needed")
            }
        else:
            if project.crane_organized == 1:
                return {
                    'color': 'green',
                    'tooltip': _("The crane was organized")
                }
            else:
                return {
                    'color': 'red',
                    'tooltip': _("The crane has not yet been organized")
                }
    
    if typ == 'a6':
        if drilling_object.mud_disposer:
            return {
                'color': 'green',
                'tooltip': _("Mud Disposer entered")
            }
        else:
            return {
                'color': 'red',
                'tooltip': _("Mud Disposer missing")
            }
    
    if typ == 'a7':
        if project.drill_notice_sent == 1:
            return {
                'color': 'green',
                'tooltip': _("Drill notice sent")
            }
        else:
           return {
                'color': 'red',
                'tooltip': _("Drill notice <b>not</b> sent")
            }
