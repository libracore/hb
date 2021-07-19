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
    data["days"], data["total_width"], data["weekend"], data["kw_list"], data["day_list"], data["today"] = get_days(from_date, to_date)
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
    company = frappe.defaults.get_user_default("Company")
    holidaylist = frappe.get_doc("Company", company).default_holiday_list
    if holidaylist:
        holidaylist = frappe.get_doc("Holiday List", holidaylist)
        holidays = []
        for holiday in holidaylist.holidays:
            holidays.append(holiday.holiday_date.strftime("%d.%m.%Y"))
    delta = timedelta(days=1)
    while start_date <= end_date:
        date_list.append(start_date.strftime("%d.%m.%Y"))
        kw_list[start_date.strftime("%d.%m.%Y")] = start_date.strftime("%V")
        day_list[start_date.strftime("%d.%m.%Y")] = start_date.strftime("%a")
        week_day_no = start_date.weekday()
        if holidaylist:
            if start_date.strftime("%d.%m.%Y") in holidays:
                weekend_list.append(start_date.strftime("%d.%m.%Y"))
                total_weekend += 1
            else:
                total_weekday += 1
            start_date += delta
        else:
            if week_day_no >= 5:
                weekend_list.append(start_date.strftime("%d.%m.%Y"))
                total_weekend += 1
            else:
                total_weekday += 1
            start_date += delta
        
    total_width = (total_weekday * 161) + (total_weekend * 80) + 6
    
    today = date.today()
    today = today.strftime("%d.%m.%Y")
    
    return date_list, total_width, weekend_list, kw_list, day_list, today
    
def get_drilling_teams():
    drilling_teams = []
    _drilling_teams = frappe.db.sql("""SELECT `name`, `title`, `drm`, `drt`, `truck_and_weight`, `has_trough`, `trough_details`, `has_crane`, `crane_details`, `phone` FROM `tabDrilling Team`""", as_dict=True)
    
    for team in _drilling_teams:
        data = {}
        data["team"] = team.name
        data["title"] = team.title
        data["drm"] = team.drm
        data["drt"] = team.drt
        data["truck_and_weight"] = team.truck_and_weight
        data["has_trough"] = team.has_trough
        data["trough_details"] = team.trough_details or _('Has Trough')
        data["has_crane"] = team.has_crane
        data['crane_details'] = team.crane_details or _('Has Crane')
        data["phone"] = team.phone
        data["booked_days"], data["booked_vm_start_days"], data["booked_nm_start_days"], data["booked_vm_end_days"], data["booked_nm_end_days"], data["project_details"] = get_booked_days_of_drilling_team(team.name)
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
    data['object'] = frappe.get_doc("Object", project.object)
    if data['object'].manager:
        data['manager'] = frappe.get_doc("User", data['object'].manager).username
    else:
        data['manager'] = ''
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
    # a1 = Baustelle besichtigt (construction_site_inspected auf Objekt)
    # a2 = Bewilligungen (permits in Project)
    # a3 = Kundenauftrag (Sales Order in Project)
    # a4 = Materialstatus (Purchase Order and Delivery note linkt o Project)
    # a5 = Kran benötigt (Checklist in Project)
    # a6 = Bohrschlammentsorgung (Checklist in Project)
    # a7 = Bohranzeige versendet (Checkbox in Project)
                                 
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
    
    if typ == 'a2':
        missing_permits = []
        for permit in project.permits:
            if not permit.file:
                missing_permits.append(permit.permit)
        if len(missing_permits) > 0:
            if len(missing_permits) == len(project.permits):
                # all missing
                return {
                    'color': 'red',
                    'tooltip': _("All permits are missing")
                }
            else:
                # some missing
                return {
                    'color': 'yellow',
                    'tooltip': _("Following permits are missing:") + "<br>{missing_permits}".format(missing_permits='<br>'.join(missing_permits))
                }
        else:
            # all good
            return {
                'color': 'green',
                'tooltip': _("All permits available")
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
    
    if typ == 'a4':
        pos = frappe.db.sql("""SELECT DISTINCT `parent` FROM `tabPurchase Order Item` WHERE `project` = '{project}' AND `docstatus` != 2 LIMIT 1""".format(project=project.name), as_dict=True)
        if len(pos) > 0:
            po = frappe.get_doc("Purchase Order", pos[0].parent)
            if po.docstatus != 1:
                return {
                    'color': 'red',
                    'tooltip': _("Purchase Order") + " {po} ".format(po=po.name) + _("<b>not</b> submitted")
                }
            else:
                if po.per_received == 100:
                    return {
                        'color': 'green',
                        'tooltip': _("Purchase Order delivered")
                    }
                else:
                    return {
                        'color': 'yellow',
                        'tooltip': _("Purchase Order") + " {percent}% " + "delivered".format(percent=po.per_received)
                    }
        else:
            return {
                'color': 'red',
                'tooltip': _("No Purchase Order available")
            }
    
    if typ == 'a5':
        crane = frappe.db.sql("""SELECT `name`, `supplier` FROM `tabProject Checklist` WHERE `parent` = '{project}' AND `activity` = 'Kran'""".format(project=project.name), as_dict=True)
        if not len(crane) > 0:
            return {
                'color': 'grey',
                'tooltip': _("No crane is needed")
            }
        else:
            if crane[0].supplier:
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
        mud_disposer = frappe.db.sql("""SELECT `name`, `supplier` FROM `tabProject Checklist` WHERE `parent` = '{project}' AND `activity` = 'Schlammentsorgung'""".format(project=project.name), as_dict=True)
        if not len(mud_disposer) > 0:
            return {
                'color': 'red',
                'tooltip': _("The Mud Disposer has not yet been organized")
            }
        else:
            if mud_disposer[0].supplier:
                return {
                    'color': 'green',
                    'tooltip': _("The Mud Disposer was organized")
                }
            else:
                return {
                    'color': 'red',
                    'tooltip': _("The Mud Disposer has not yet been organized")
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
