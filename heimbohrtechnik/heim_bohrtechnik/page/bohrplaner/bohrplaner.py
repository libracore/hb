# -*- coding: utf-8 -*-
# Copyright (c) 2017-2021, libracore and contributors

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import getdate, date_diff, add_days, get_datetime
from datetime import date, timedelta

@frappe.whitelist()
def get_overlay_datas(from_date, to_date):
    projects = []
    name_list = []
    
    projects_start = frappe.get_all('Project',
        filters=[
            ['expected_start_date', 'between', [from_date, to_date]],
            ['name', 'not in', name_list]
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'object', 'end_half_day']
    )
    for p in projects_start:
        correction = 0
        if p.expected_start_date < getdate(from_date):
            correction = date_diff(p.expected_end_date, p.expected_start_date) - date_diff(p.expected_end_date, getdate(from_date))
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
            p.expected_start_date = getdate(from_date)
            if p.start_half_day.lower() == 'nm':
                p.start_half_day = 'vm'
        else:
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
        if p.start_half_day.lower() == 'nm':
            dauer -= 1
        if p.end_half_day.lower() == 'vm':
            dauer -= 1
        name_list.append(p.name)
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'object': frappe.get_doc("Object", p.object),
            'name': p.name,
            'ampeln': get_traffic_lights_indicator(p.name)
        }
        projects.append(p_data)
    
    projects_end = frappe.get_all('Project',
        filters=[
            ['expected_end_date', 'between', [from_date, to_date]],
            ['name', 'not in', name_list]
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'object', 'end_half_day']
    )
    for p in projects_end:
        correction = 0
        if p.expected_start_date < getdate(from_date):
            correction = date_diff(p.expected_end_date, p.expected_start_date) - date_diff(p.expected_end_date, getdate(from_date))
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
            p.expected_start_date = getdate(from_date)
            if p.start_half_day.lower() == 'nm':
                p.start_half_day = 'vm'
        else:
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
        if p.start_half_day.lower() == 'nm':
            dauer -= 1
        if p.end_half_day.lower() == 'vm':
            dauer -= 1
        name_list.append(p.name)
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'object': frappe.get_doc("Object", p.object),
            'name': p.name,
            'ampeln': get_traffic_lights_indicator(p.name)
        }
        projects.append(p_data)
    
    projects_outside = frappe.get_all('Project',
        filters=[
            ['expected_start_date', '<', to_date],
            ['expected_end_date', '>', from_date],
            ['name', 'not in', name_list]
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'object', 'end_half_day']
    )
    for p in projects_outside:
        correction = 0
        if p.expected_start_date < getdate(from_date):
            correction = date_diff(p.expected_end_date, p.expected_start_date) - date_diff(p.expected_end_date, getdate(from_date))
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
            p.expected_start_date = getdate(from_date)
            if p.start_half_day.lower() == 'nm':
                p.start_half_day = 'vm'
        else:
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
        if p.start_half_day.lower() == 'nm':
            dauer -= 1
        if p.end_half_day.lower() == 'vm':
            dauer -= 1
        name_list.append(p.name)
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'object': frappe.get_doc("Object", p.object),
            'name': p.name,
            'ampeln': get_traffic_lights_indicator(p.name)
        }
        projects.append(p_data)
        
    return projects
    
def get_traffic_lights_indicator(project):
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
    a1 = False
    a2 = False
    a3 = False
    a4 = False
    a5 = False
    a6 = False
    a7 = False
    data = {}
    
    #if typ == 'a1':
    if drilling_object.construction_site_inspected == 1:
        data['a1'] = {
            'color': 'green',
            'tooltip': _('The construction site was visited')
        }
        a1 = True
    else:
        data['a1'] = {
            'color': 'red',
            'tooltip': _("The construction site was <b>not</b> visited")
        }
    
    #if typ == 'a2':
    missing_permits = []
    for permit in project.permits:
        if not permit.file:
            missing_permits.append(permit.permit)
    if len(missing_permits) > 0:
        if len(missing_permits) == len(project.permits):
            # all missing
            data['a2'] =  {
                'color': 'red',
                'tooltip': _("All permits are missing")
            }
        else:
            # some missing
            data['a2'] = {
                'color': 'yellow',
                'tooltip': _("Following permits are missing:") + "<br>{missing_permits}".format(missing_permits='<br>'.join(missing_permits))
            }
    else:
        # all good
        data['a2'] = {
            'color': 'green',
            'tooltip': _("All permits available")
        }
        a2 = True
    
    #if typ == 'a3':
    if not project.sales_order:
        data['a3'] = {
            'color': 'red',
            'tooltip': _("No sales order available")
        }
    else:
        sales_order = frappe.get_doc("Sales Order", project.sales_order)
        if sales_order.docstatus == 1:
            data['a3'] = {
                'color': 'green',
                'tooltip': _("The sales order is submitted")
            }
            a3 = True
        elif  sales_order.docstatus == 0:
            data['a3'] = {
                'color': 'yellow',
                'tooltip': _("The sales order is <b>not</b> submitted")
            }
        else:
            data['a3'] = {
                'color': 'red',
                'tooltip': _("The sales order is cancelled")
            }
    
    #if typ == 'a4':
    pos = frappe.db.sql("""SELECT DISTINCT `parent` FROM `tabPurchase Order Item` WHERE `project` = '{project}' AND `docstatus` != 2 LIMIT 1""".format(project=project.name), as_dict=True)
    if len(pos) > 0:
        po = frappe.get_doc("Purchase Order", pos[0].parent)
        if po.docstatus != 1:
            data['a4'] = {
                'color': 'red',
                'tooltip': _("Purchase Order") + " {po} ".format(po=po.name) + _("<b>not</b> submitted")
            }
        else:
            if po.per_received == 100:
                data['a4'] = {
                    'color': 'green',
                    'tooltip': _("Purchase Order delivered")
                }
                a4 = True
            else:
                data['a4'] = {
                    'color': 'yellow',
                    'tooltip': _("Purchase Order") + " {percent}% " + "delivered".format(percent=po.per_received)
                }
    else:
        data['a4'] = {
            'color': 'red',
            'tooltip': _("No Purchase Order available")
        }
    
    #if typ == 'a5':
    crane_activity = frappe.get_single("Heim Settings").crane_activity or 'Kran'
    crane = frappe.db.sql("""SELECT `name`, `supplier` FROM `tabProject Checklist` WHERE `parent` = '{project}' AND `activity` = '{crane_activity}'""".format(project=project.name, crane_activity=crane_activity), as_dict=True)
    if not len(crane) > 0:
        data['a5'] = {
            'color': 'grey',
            'tooltip': _("No crane is needed")
        }
        a5 = True
    else:
        if crane[0].supplier:
            data['a5'] = {
                'color': 'green',
                'tooltip': _("The crane was organized")
            }
            a5 = True
        else:
            data['a5'] = {
                'color': 'red',
                'tooltip': _("The crane has not yet been organized")
            }
    
    #if typ == 'a6':
    mud_disposer_activity = frappe.get_single("Heim Settings").mud_disposer_activity or 'Schlammentsorgung'
    mud_disposer = frappe.db.sql("""SELECT `name`, `supplier` FROM `tabProject Checklist` WHERE `parent` = '{project}' AND `activity` = '{mud_disposer_activity}'""".format(project=project.name, mud_disposer_activity=mud_disposer_activity), as_dict=True)
    if not len(mud_disposer) > 0:
        data['a6'] = {
            'color': 'red',
            'tooltip': _("The Mud Disposer has not yet been organized")
        }
    else:
        if mud_disposer[0].supplier:
            data['a6'] = {
                'color': 'green',
                'tooltip': _("The Mud Disposer was organized")
            }
            a6 = True
        else:
            data['a6'] = {
                'color': 'red',
                'tooltip': _("The Mud Disposer has not yet been organized")
            }
    
    #if typ == 'a7':
    if project.drill_notice_sent == 1:
        data['a7'] = {
            'color': 'green',
            'tooltip': _("Drill notice sent")
        }
        a7 = True
    else:
       data['a7'] = {
            'color': 'red',
            'tooltip': _("Drill notice <b>not</b> sent")
        }
        
    if a1 and \
       a2 and \
       a3 and \
       a4 and \
       a6 and \
       a7 and \
       a5:
        data['bgc'] = 'background-color: #eefdec;'
        data ['bc'] = 'border: 2px solid #81d41a;'
    elif a1 and \
         a2 and \
         a3 and \
         a7:
        data['bgc'] = 'background-color: #ffffbf;'
        data ['bc'] = 'border: 2px solid #ffff6d;'
    else:
        data['bgc'] = 'background-color: #ffeae9;'
        data ['bc'] = 'border: 2px solid #ffa6a6;'
        
    return data
    
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
        
        if project.start_half_day != start_half_day.upper():
            old_start_hd = project.start_half_day
            project.start_half_day = start_half_day.upper()
            if old_start_hd == 'NM':
                if project.end_half_day == 'NM':
                    project.end_half_day = 'VM'
                else:
                    project.end_half_day = 'NM'
            else:
                if project.end_half_day == 'VM':
                    project.end_half_day = 'NM'
                else:
                    project.end_half_day = 'VM'
        
        project.drilling_team = team
        
        project.save()
    else:
        project.expected_start_date = getdate(new_project_start)
        project.expected_end_date = getdate(new_project_end_date)
        project.start_half_day = start_half_day
        project.end_half_day = end_half_day
        project.drilling_team = team
        
        project.save()
    
@frappe.whitelist()
def get_content(from_date, to_date):
    data = {}
    data["drilling_teams"] = get_drilling_teams()
    data["days"], data["weekend"], data["kw_list"], data["day_list"], data["today"] = get_days(from_date, to_date)
    return data
    
def get_days(from_date, to_date):
    start_date = getdate(from_date)
    end_date = getdate(to_date)
    date_list = []
    weekend_list = []
    kw_list = {}
    day_list = {}
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
            start_date += delta
        else:
            if week_day_no >= 5:
                weekend_list.append(start_date.strftime("%d.%m.%Y"))
            start_date += delta
        
    today = date.today()
    today = today.strftime("%d.%m.%Y")
    
    return date_list, weekend_list, kw_list, day_list, today
    
def get_drilling_teams():
    drilling_teams = []
    _drilling_teams = frappe.db.sql("""SELECT `name`, `title`, `drm`, `drt`, `truck_and_weight`, `has_trough`, `trough_details`, `has_crane`, `crane_details`, `phone` FROM `tabDrilling Team`""", as_dict=True)
    
    for team in _drilling_teams:
        data = {}
        data["title"] = team.title
        data["drm"] = team.drm
        data["drt"] = team.drt
        data["truck_and_weight"] = team.truck_and_weight
        data["has_trough"] = team.has_trough
        data["trough_details"] = team.trough_details or _('Has Trough')
        data["has_crane"] = team.has_crane
        data['crane_details'] = team.crane_details or _('Has Crane')
        data["phone"] = team.phone
        drilling_teams.append(data)
    
    return drilling_teams
