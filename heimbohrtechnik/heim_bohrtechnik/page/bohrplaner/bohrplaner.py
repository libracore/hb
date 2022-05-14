# -*- coding: utf-8 -*-
# Copyright (c) 2017-2022, libracore and contributors

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
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'end_half_day', 'object']
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
        
        project = frappe.get_doc("Project", p.name)
        p_object = frappe.get_doc("Object", p.object)
        manager_short = frappe.db.get_value("User", project.manager, "username") if project.manager else ''
        drilling_equipments = []
        for d in project.drilling_equipment:
            drilling_equipments.append(d.drilling_equipment)
        drilling_equipment = ", ".join(drilling_equipments)
        saugauftrag = ''
        pneukran = ''
        for cl_entry in project.checklist:
            if cl_entry.activity == 'Schlammentsorgung':
                saugauftrag = cl_entry.supplier_name
            if cl_entry.activity == 'Kran':
                pneukran = cl_entry.supplier_name
        
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'ampeln': get_traffic_lights_indicator(project),
            'project': project,
            'saugauftrag': saugauftrag,
            'pneukran': pneukran,
            'manager_short': manager_short,
            'drilling_equipment': drilling_equipment
        }
        projects.append(p_data)
    
    projects_end = frappe.get_all('Project',
        filters=[
            ['expected_end_date', 'between', [from_date, to_date]],
            ['name', 'not in', name_list]
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'end_half_day', 'object']
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
        
        project = frappe.get_doc("Project", p.name)
        p_object = frappe.get_doc("Object", p.object)
        manager_short = frappe.db.get_value("User", p_object.manager, "username") if p_object.manager else ''
        drilling_equipment = p_object.drilling_equipment if p_object.drilling_equipment else ''
        saugauftrag = ''
        pneukran = ''
        for cl_entry in project.checklist:
            if cl_entry.activity == 'Schlammentsorgung':
                saugauftrag = cl_entry.supplier_name
            if cl_entry.activity == 'Kran':
                pneukran = cl_entry.supplier_name
        
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'ampeln': get_traffic_lights_indicator(project),
            'project': project,
            'saugauftrag': saugauftrag,
            'pneukran': pneukran,
            'manager_short': manager_short,
            'drilling_equipment': drilling_equipment
        }
        projects.append(p_data)
    
    projects_outside = frappe.get_all('Project',
        filters=[
            ['expected_start_date', '<', to_date],
            ['expected_end_date', '>', from_date],
            ['name', 'not in', name_list]
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'end_half_day', 'object']
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
        
        project = frappe.get_doc("Project", p.name)
        p_object = frappe.get_doc("Object", p.object)
        manager_short = frappe.db.get_value("User", p_object.manager, "username") if p_object.manager else ''
        drilling_equipment = p_object.drilling_equipment if p_object.drilling_equipment else ''
        saugauftrag = ''
        pneukran = ''
        for cl_entry in project.checklist:
            if cl_entry.activity == 'Schlammentsorgung':
                saugauftrag = cl_entry.supplier_name
            if cl_entry.activity == 'Kran':
                pneukran = cl_entry.supplier_name
        
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'ampeln': get_traffic_lights_indicator(project),
            'project': project,
            'saugauftrag': saugauftrag,
            'pneukran': pneukran,
            'manager_short': manager_short,
            'drilling_equipment': drilling_equipment
        }
        projects.append(p_data)
        
    return projects
    
def get_traffic_lights_indicator(project):
    colors = []
    
    # projeknummer
    projeknummer_color = '#ffa6a6;'
    if int(project.termin_bestaetigt) == 1:
        projeknummer_color = '#ffffbf;'
    if project.sales_order:
        akonto = int(frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabAkonto Invoice` WHERE `sales_order` = '{so}' AND `docstatus` = 1""".format(so=project.sales_order), as_dict=True)[0].qty)
        if akonto > 0:
            projeknummer_color = '#eefdec;'
        sinv = int(frappe.db.sql("""SELECT COUNT(`name`) AS `qty` FROM `tabSales Invoice Item` WHERE `parenttype` = 'Sales Invoice' AND `sales_order` = '{so}' AND `docstatus` = 1""".format(so=project.sales_order), as_dict=True)[0].qty)
        if sinv > 0:
            projeknummer_color = '#81d41a;'
    colors.append(projeknummer_color)
    
    # auftraggeber
    auftraggeber_color = '#ffa6a6;'
    if project.sales_order:
        unterzeichnete_ab = frappe.get_doc("Sales Order", project.sales_order).unterzeichnete_ab
        if unterzeichnete_ab:
            auftraggeber_color = '#81d41a;'
    colors.append(auftraggeber_color)
    
    # objektname
    objektname_color = '#ffa6a6;'
    found_permits = 0
    found_permits_with_file = 0
    for permit in project.permits:
        if 'Bohrbewilligung' in permit.permit:
            found_permits += 1
            if permit.file:
                found_permits_with_file += 1
    if found_permits == found_permits_with_file:
        objektname_color = '#81d41a;'
    colors.append(objektname_color)
    
    # objekt_strasse
    objekt_strasse_color = '#c4c7ca;'
    '''
        Status Rot --> Ich weiss nicht wie prüfen -> "Bohranzeige eingereicht: Projekt hat Bohranzeige"
    '''
    if int(project.drill_notice_sent) == 1:
        objekt_strasse_color = '#81d41a;'
    colors.append(objekt_strasse_color)
    
    # objekt_plz_ort
    objekt_plz_ort_color = '#c4c7ca;'
    if int(project.thermozement) == 1:
        objekt_plz_ort_color = '#9dc7f0;'
    colors.append(objekt_plz_ort_color)
    objekt_plz_ort_font_color = 'black;'
    objekt_plz_ort_border_color = ''
    for permit in project.permits:
        if 'Lärmschutzbewilligung' in permit.permit:
            objekt_plz_ort_font_color = 'red;'
            if permit.file:
                objekt_plz_ort_font_color = 'yellow;'
        elif 'Strassensperrung' in permit.permit:
            if not permit.file:
                objekt_plz_ort_border_color = 'border: 1px solid red;'
    colors.append(objekt_plz_ort_font_color)
    colors.append(objekt_plz_ort_border_color)
    
    #ews_details
    ews_details_color = '#ffa6a6;'
    po = frappe.db.sql("""SELECT `per_received` FROM `tabPurchase Order` WHERE `object` = '{0}' AND `docstatus` = 1""".format(project.object), as_dict=True)
    if len(po) > 0:
        ews_details_color = '#ffffbf;'
        if int(po[0].per_received) == 100:
            ews_details_color = '#81d41a;'
    colors.append(ews_details_color)
    
    # saugauftrag
    saugauftrag_color = 'transparent;'
    for cl_entry in project.checklist:
        if cl_entry.activity == 'Schlammentsorgung':
            saugauftrag_color = '#ffa6a6;'
            if cl_entry.supplier_name:
                saugauftrag_color = '#81d41a;'
    colors.append(saugauftrag_color)
    
    # pneukran
    pneukran_color = '#c4c7ca;'
    if int(project.crane_required) == 1:
        if int(project.crane_organized) == 1:
            pneukran_color = '#81d41a;'
        else:
            pneukran_color = '#ffa6a6;'
    colors.append(pneukran_color)
    
    # typ_bohrgeraet
    typ_bohrgeraet_color = 'white;'
    colors.append(typ_bohrgeraet_color)
    
    # kuerzel_pl
    kuerzel_pl_color = '#ffa6a6;'
    baustelle_besichtigt = int(project.construction_site_inspected)
    if baustelle_besichtigt == 1:
        kuerzel_pl_color = '#81d41a;'
    colors.append(kuerzel_pl_color)
    
    # strassensperrung
    strassensperrung_color = '#c4c7ca;'
    for permit in project.permits:
        if 'Strassensperrung' in permit.permit:
            strassensperrung_color = '#ffa6a6;'
            if permit.file:
                strassensperrung_color = '#81d41a;'
    colors.append(strassensperrung_color)
    
    return colors
    
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
        project.crane_organized = '0'
        project.save()
    else:
        project.expected_start_date = getdate(new_project_start)
        project.expected_end_date = getdate(new_project_end_date)
        project.start_half_day = start_half_day
        project.end_half_day = end_half_day
        project.drilling_team = team
        project.crane_organized = '0'
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
