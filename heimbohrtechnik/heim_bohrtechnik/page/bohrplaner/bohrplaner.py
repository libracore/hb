# -*- coding: utf-8 -*-
# Copyright (c) 2017-2022, libracore and contributors

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import getdate, date_diff, add_days, get_datetime
from datetime import date, timedelta
from frappe.desk.form.load import get_attachments

@frappe.whitelist()
def get_overlay_datas(from_date, to_date):
    projects = []
    
    matching_projects = frappe.db.sql("""
        SELECT 
            `name`, 
            `drilling_team`, 
            `expected_start_date`, 
            `expected_end_date`, 
            `start_half_day`, 
            `end_half_day`, 
            `object`
        FROM `tabProject`
        WHERE `project_type` = "External"
          AND 
            ((`expected_start_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_end_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_start_date` < '{from_date}' AND `expected_end_date` > '{to_date}')
            )
        """.format(from_date=from_date, to_date=to_date), as_dict=True)

    for p in matching_projects:
        correction = 0
        if p.expected_start_date < getdate(from_date):
            # start is before from_date
            correction = date_diff(p.expected_end_date, p.expected_start_date) - date_diff(p.expected_end_date, getdate(from_date))
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
            p.expected_start_date = getdate(from_date)
            if p.start_half_day.lower() == 'nm':
                p.start_half_day = 'vm'
        else:
            dauer = ((date_diff(p.expected_end_date, p.expected_start_date) - correction) + 1) * 2
        # compensate for duration exceeding to_date
        if p.expected_end_date > getdate(to_date):
            duration_correction = (date_diff(p.expected_end_date, getdate(to_date)) - 1) * 2
            dauer -= duration_correction
        if p.start_half_day.lower() == 'nm':
            dauer -= 1
        if p.end_half_day.lower() == 'vm':
            dauer -= 1
        
        p_data = get_project_data(p, dauer)
        projects.append(p_data)
        
    return projects
    
def get_project_data(p, dauer):
    project = frappe.get_doc("Project", p.name)
    p_object = frappe.get_doc("Object", p.object)
    construction_sites = frappe.get_all("Construction Site Description", 
        filters={'project': p.name}, 
        fields=['name', 'internal_crane_required', 'external_crane_Required', 'carrymax'])
    manager_short = frappe.db.get_value("User", project.manager, "username") if project.manager else ''
    drilling_equipment = []
    for de in (project.drilling_equipment or []):
        drilling_equipment.append(de.drilling_equipment)
    drilling_equipment = ", ".join(drilling_equipment)
    saugauftrag = 'Schlamm fremd'
    pneukran = ''
    for cl_entry in project.checklist:
        if cl_entry.activity == 'Schlammentsorgung':
            saugauftrag = cl_entry.supplier_name
        if cl_entry.activity == 'Kran':
            pneukran = cl_entry.supplier_name
    # carrymax from construction site
    if len(construction_sites) > 0:
        if not pneukran:
            if construction_sites[0].get('carrymax') == 1:
                pneukran = "Carrymax"
            elif construction_sites[0].get('internal_crane_required') == 1:
                pneukran = "int. Kran"
            elif construction_sites[0].get('external_crane_required') == 1:
                pneukran = "ext. Kran"
    
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
        
    return p_data
    
@frappe.whitelist()
def get_internal_overlay_datas(from_date, to_date):
    projects = []
    name_list = []
    
    projects_start = frappe.get_all('Project',
        filters=[
            ['expected_start_date', 'between', [from_date, to_date]],
            ['name', 'not in', name_list],
            ['project_type', '=', 'Internal']
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'end_half_day', 'object_name']
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
        
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'project': project
        }
        projects.append(p_data)
    
    projects_end = frappe.get_all('Project',
        filters=[
            ['expected_end_date', 'between', [from_date, to_date]],
            ['name', 'not in', name_list],
            ['project_type', '=', 'Internal']
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'end_half_day', 'object_name']
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
        
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'project': project
        }
        projects.append(p_data)
    
    projects_outside = frappe.get_all('Project',
        filters=[
            ['expected_start_date', '<', to_date],
            ['expected_end_date', '>', from_date],
            ['name', 'not in', name_list],
            ['project_type', '=', 'Internal']
        ],
        fields=['name', 'drilling_team', 'expected_start_date', 'expected_end_date', 'start_half_day', 'end_half_day', 'object_name']
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
        
        p_data = {
            'bohrteam': p.drilling_team,
            'start': get_datetime(p.expected_start_date).strftime('%d.%m.%Y'),
            'vmnm': p.start_half_day.lower(),
            'dauer': dauer,
            'project': project
        }
        projects.append(p_data)
        
    return projects
    
@frappe.whitelist()
def get_subproject_overlay_datas(from_date, to_date):
    subproject_list = []
    shift_controll = {}
    subprojects = frappe.db.sql("""
        SELECT
            `tabProject Subproject`.`start`,
            `tabProject Subproject`.`end`,
            `tabProject Subproject`.`team`,
            `tabProject Subproject`.`description`,
            `tabProject Subproject`.`subcontracting_order` AS `subcontracting_order`,
            `tabProject`.`name` as `project`,
            `tabProject`.`customer_name` as `customer_name`,
            `tabProject`.`ews_details` as `ews_details`,
            `tabProject`.`object_name`,
            `tabProject`.`object_street`,
            `tabProject`.`object_location`
        FROM `tabProject Subproject`
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabProject Subproject`.`parent`
        LEFT JOIN `tabSubcontracting Order` ON `tabSubcontracting Order`.`name` = `tabProject Subproject`.`subcontracting_order`
        WHERE 
            `tabProject Subproject`.`start` BETWEEN "{from_date}" AND "{to_date}"
            OR `tabProject Subproject`.`end` BETWEEN "{from_date}" AND "{to_date}"
        ORDER BY 
            `tabProject Subproject`.`team` ASC, `tabSubcontracting Order`.`prio` ASC;""".format(
            from_date=from_date, to_date=to_date), as_dict=True)
    for subproject in subprojects:
        subproject_duration = calc_duration(subproject.start, subproject.end, from_date, to_date)
        subproject_shift, shift_controll = subproject_shift_controll(subproject, get_datetime(subproject_duration['start']).strftime('%d.%m.%Y'), shift_controll)
        
        subproject_data = {
            'bohrteam': subproject.team,
            'start': get_datetime(subproject_duration['start']).strftime('%d.%m.%Y'),
            'dauer': subproject_duration['dauer'],
            'description': subproject.description,
            'id': subproject.name,
            'subproject_shift': subproject_shift,
            'project': subproject.project,
            'customer_name': subproject.customer_name,
            'ews_details': subproject.ews_details,
            'object_name': subproject.object_name,
            'object_street': subproject.object_street,
            'object_location': subproject.object_location,
            'subcontracting_order': subproject.subcontracting_order
        }
        subproject_list.append(subproject_data)
    
    return subproject_list

def calc_duration(start, end, from_date, to_date):
    correction = 0
    if start < getdate(from_date):
        correction = date_diff(end, start) - date_diff(end, getdate(from_date))
        dauer = ((date_diff(end, start) - correction) + 1) * 2
        start = getdate(from_date)
    else:
        dauer = ((date_diff(end, start) - correction) + 1) * 2
    return {
        'dauer': dauer,
        'start': start
    }

def subproject_shift_controll(subproject, start, shift_controll):
    if str(start) + str(subproject.team) in shift_controll:
        shift_controll[str(start) + str(subproject.team)] += 20
        return shift_controll[str(start) + str(subproject.team)], shift_controll
    else:
        shift_controll[str(start) + str(subproject.team)] = 0
        return 0, shift_controll

def get_traffic_lights_indicator(project):
    colors = []
    
    # projeknummer [0]
    projeknummer_color = '#ffa6a6;'
    if int(project.termin_bestaetigt) == 1:
        projeknummer_color = '#ffffbf;'
    if project.sales_order:
        akonto = int(frappe.db.sql("""
            SELECT COUNT(`tabSales Invoice`.`name`) AS `qty` 
            FROM `tabSales Invoice Item`
            LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
            WHERE `tabSales Invoice Item`.`sales_order` = '{so}' 
              AND `tabSales Invoice`.`docstatus` = 1
              AND `tabSales Invoice`.`title` = "Teilrechnung"; """.format(so=project.sales_order), as_dict=True)[0].qty)
        if akonto > 0:
            projeknummer_color = '#eefdec;'
        sinv = int(frappe.db.sql("""
            SELECT COUNT(`tabSales Invoice`.`name`) AS `qty` 
            FROM `tabSales Invoice Item` 
            LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
            WHERE `tabSales Invoice Item`.`parenttype` = 'Sales Invoice' 
              AND `tabSales Invoice Item`.`sales_order` = '{so}' 
              AND `tabSales Invoice`.`docstatus` = 1 
              AND `tabSales Invoice`.`title` IN ("Schlussrechnung", "Rechnung"); 
            """.format(so=project.sales_order), as_dict=True)[0].qty)
        if sinv > 0:
            projeknummer_color = '#81d41a;'
    colors.append(projeknummer_color)
    
    # auftraggeber [1]
    auftraggeber_color = '#ffa6a6;'
    if project.sales_order:
        unterzeichnete_ab = frappe.get_value("Sales Order", project.sales_order, "unterzeichnete_ab")
        if unterzeichnete_ab:
            auftraggeber_color = '#81d41a;'
    colors.append(auftraggeber_color)
    
    # objektname [2]
    objektname_color = '#ffa6a6;'               # base: red
    found_permits = 0
    found_permits_with_file = 0
    if not project.permits or len(project.permits) == 0:
        objektname_color = '#c4c7ca;'           # project has not permit records: grey
    else:
        for permit in project.permits:
            if 'Bohrbewilligung kantonal' in permit.permit:
                found_permits += 1
                if permit.file:
                    found_permits_with_file += 1
        if found_permits == found_permits_with_file:
            objektname_color = '#81d41a;'       # all permits available: green
    colors.append(objektname_color)
    
    # objekt_strasse [3]
    objekt_strasse_color = '#c4c7ca;'           # start with grey
    drill_notices = frappe.get_all("Bohranzeige", filters={'project': project.name}, fields={'name'})
    if len(drill_notices) > 0:
        # has a drill notice: red
        objekt_strasse_color = '#ffa6a6;'
    if int(project.drill_notice_sent) == 1:
        objekt_strasse_color = '#81d41a;'       # green
    colors.append(objekt_strasse_color)
    
    # objekt_plz_ort [4, 5, 6]
    objekt_plz_ort_color = '#c4c7ca;'
    if int(project.thermozement) == 1:
        objekt_plz_ort_color = '#9dc7f0;'
    colors.append(objekt_plz_ort_color)             # 4
    objekt_plz_ort_font_color = 'black;'
    objekt_plz_ort_border_color = ''
    for permit in project.permits:
        if 'Lärmschutzbewilligung' in permit.permit:
            objekt_plz_ort_font_color = 'red;'
            if permit.file:
                objekt_plz_ort_font_color = '#ffbf00;'          # orange
        #elif 'Strassensperrung' in permit.permit:              # removed by change request RB/2022-10-05
        #    if not permit.file:
        #        objekt_plz_ort_border_color = 'border: 1px solid red;'
    colors.append(objekt_plz_ort_font_color)       # 5
    colors.append(objekt_plz_ort_border_color)     # 6
    
    #ews_details [7]
    ews_details_color = '#ffa6a6;'
    po = frappe.db.sql("""SELECT `per_received` FROM `tabPurchase Order` WHERE `object` = '{0}' AND `docstatus` = 1""".format(project.object), as_dict=True)
    if len(po) > 0:
        ews_details_color = '#ffffbf;'
        if int(po[0].per_received) == 100:
            ews_details_color = '#81d41a;'
    colors.append(ews_details_color)
    
    # saugauftrag [8]
    saugauftrag_color = 'transparent;'
    for cl_entry in project.checklist:
        if cl_entry.activity == 'Schlammentsorgung':
            saugauftrag_color = '#ffa6a6;'              # orange
            #if cl_entry.supplier_name:
            if project.trough_ordered:
                saugauftrag_color = '#81d41a;'          # green
    colors.append(saugauftrag_color)
    
    # pneukran [9]
    pneukran_color = '#c4c7ca;'
    if int(project.crane_required) == 1:
        if int(project.crane_organized) == 1:
            pneukran_color = '#81d41a;'
        else:
            pneukran_color = '#ffa6a6;'
    colors.append(pneukran_color)
    
    # typ_bohrgeraet [10]
    typ_bohrgeraet_color = 'white;'
    colors.append(typ_bohrgeraet_color)
    
    # kuerzel_pl [11]
    kuerzel_pl_color = '#ffa6a6;'
    if is_construction_site_inspected(project.name) == 1:
        kuerzel_pl_color = '#81d41a;'
    colors.append(kuerzel_pl_color)
    
    # strassensperrung [12]
    strassensperrung_color = '#c4c7ca;'         # grey: not applicable
    for permit in project.permits:
        if 'Strassensperrung' in permit.permit:
            strassensperrung_color = '#ffa6a6;' # red: required
            if has_public_area_request(project.name):
                strassensperrung_color = '#ffa6a6';     # orange: requested
            if permit.file:                         
                strassensperrung_color = '#81d41a;'     # green: permit available
    colors.append(strassensperrung_color)
    
    return colors

def is_construction_site_inspected(project):
    inspected = frappe.db.sql("""
        SELECT MAX(`tabConstruction Site Description`.`site_inspected`) AS `is_inspected`
        FROM `tabConstruction Site Description`
        WHERE `tabConstruction Site Description`.`project` = "{project}";
    """.format(project=project), as_dict=True)
    return inspected[0]['is_inspected'] if len(inspected) > 0 else 0
    
def has_public_area_request(project):
    public_area_requests = frappe.get_all("Request for Public Area Use",
        filters={'project': project},
        fields=['name', 'sent']
    )
    if len(public_area_requests) > 0 and public_area_requests[0]['sent'] == 1:
        return True
    else:
        return False

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
    drilling_teams = frappe.db.sql("""
        SELECT 
            `name` AS `team_id`, 
            `title`, 
            `drm`, 
            `drt`, 
            `truck_and_weight`, 
            `has_trough`, 
            IFNULL(`trough_details`, "{trough}") AS `trough_details`, 
            `has_crane`, 
            IFNULL(`crane_details`, "{crane}") AS `crane_details`, 
            `phone`,
            `drilling_team_type`
        FROM `tabDrilling Team`""".format(
            trough=_('Has Trough'), crane=_('Has Crane')), as_dict=True)
        
    return drilling_teams

# Absences
@frappe.whitelist()
def get_absences_overlay_datas(from_date, to_date):
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    absences = []
    shift = -20
    emp = ''
    absences_raw = frappe.db.sql("""SELECT
                                    `name`,
                                    `employee`,
                                    `employee_name`,
                                    `from_date`,
                                    `to_date`
                                FROM `tabLeave Application`
                                WHERE `status` = 'Approved'
                                AND `docstatus` = 1
                                AND 
                                    (`from_date` BETWEEN '{from_date}' AND '{to_date}')
                                OR
                                    (`to_date` BETWEEN '{from_date}' AND '{to_date}')
                                OR
                                    (`from_date` < '{from_date}' AND `to_date` > '{to_date}')
                                ORDER BY `employee_name` ASC""".format(from_date=from_date, to_date=to_date), as_dict=True)
    for absence in absences_raw:
        duration = calc_duration(absence.from_date, absence.to_date, from_date, to_date)
        if absence.employee != emp:
            shift += 20
            emp = absence.employee
        
        _absence = {
            'start': get_datetime(duration['start']).strftime('%d.%m.%Y'),
            'dauer': duration['dauer'],
            'employee_name': absence.employee_name,
            'absence': absence.name,
            'shift': shift
        }
        absences.append(_absence)
    
    return absences

@frappe.whitelist()
def get_user_planning_days(user):
    if frappe.db.exists("Signature", user):
        return {
            'planning_days': frappe.get_value("Signature", user, "planning_days") or 30,
            'planning_past_days': frappe.get_value("Signature", user, "planning_past_days") or 0
        }
    else:
        return {
            'planning_days': 30,
            'planning_past_Days': 0
        }
    
@frappe.whitelist()
def print_bohrplaner(html):
    from frappe.utils.pdf import get_pdf
    from PyPDF2 import PdfFileWriter
    from frappe.utils.pdf import get_file_data_from_writer
    from erpnextswiss.erpnextswiss.attach_pdf import create_folder
    
    bohrplaner_css = frappe.read_file("{0}{1}".format(frappe.utils.get_bench_path(), "/apps/heimbohrtechnik/heimbohrtechnik/heim_bohrtechnik/page/bohrplaner/bohrplaner.css"))

    html = html + """<body>
        <meta name="pdfkit-orientation" content="Portrait"/><style>
        .print-format {
         margin-top: 0mm;
         margin-left: 0mm;
         margin-right: 0mm;
        }
        
        .object-div {
            font-size: 9pt !important;
        }
        """ + bohrplaner_css + "</style></body>"
    output = PdfFileWriter()
    output = get_pdf(html, output=output)
    
    file_name = "{0}.pdf".format(frappe.generate_hash(length=14))
    folder = create_folder("Bohrplaner-Prints", "Home")
    
    filedata = get_file_data_from_writer(output)
    
    _file = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "folder": folder,
        "is_private": 1,
        "content": filedata
    })
    
    _file.save(ignore_permissions=True)
    
    return _file.file_url
