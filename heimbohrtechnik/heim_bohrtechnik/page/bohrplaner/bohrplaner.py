# -*- coding: utf-8 -*-
# Copyright (c) 2017-2025, libracore and contributors

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils.data import getdate, date_diff, add_days, get_datetime
from datetime import date, timedelta, datetime
from frappe.desk.form.load import get_attachments
from frappe.utils import cint, get_url_to_form
from math import floor
from heimbohrtechnik.heim_bohrtechnik.nextcloud import write_file_to_base_path, get_physical_path
from heimbohrtechnik.heim_bohrtechnik.date_controller import move_project, get_duration_days
from heimbohrtechnik.heim_bohrtechnik.utils import get_drilling_meters_per_day
from heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description import has_construction_site_description

BG_GREEN = '#81d41a;'
BG_ORANGE = '#ffbf00;'
BG_RED = '#ffa6a6;'
BG_LIGHT_GREEN = '#eefdec;'
BG_DARK_GREEN = '#006400;'
BG_GREY = '#c4c7ca;'
BG_BLUE = '#9dc7f0;'
BG_WHITE = '#ffffff;'
BG_BLACK = '#000000;'
BG_DARK_RED = '#8b0000;' # '#7b241c'
BG_DARK_ORANGE = '#d76400;'
BG_YELLOW = '#FFEA00;'

WEEKDAYS = {
    0: "So",
    1: "Mo", 
    2: "Di",
    3: "Mi",
    4: "Do",
    5: "Fr",
    6: "Sa"
}
@frappe.whitelist()
def get_overlay_datas(from_date, to_date, customer=None, drilling_team=None):
    projects = []
    
    customer_filter = ""
    if customer:
        customer_filter =  """ AND `tabProject`.`customer` = "{customer}" """.format(customer=customer)
    drilling_team_filter = ""
    if drilling_team:
        drilling_team_filter = """ AND `tabProject`.`drilling_team` = '{drilling_team}'""".format(drilling_team=drilling_team)
        
    matching_projects = frappe.db.sql("""
        SELECT 
            `name`, 
            `drilling_team`, 
            `expected_start_date`, 
            `expected_end_date`, 
            `start_half_day`, 
            `end_half_day`, 
            `object`,
            `drilling_meter_per_day`,
            `has_subproject`,
            `drilling_method`
        FROM `tabProject`
        WHERE `project_type` = "External"
          AND `status` IN ("Open", "Completed")
          AND 
            ((`expected_start_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_end_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_start_date` < '{from_date}' AND `expected_end_date` > '{to_date}')
            )
          {customer_filter}
          {drilling_team_filter}
        ORDER BY
            `tabProject`.`expected_start_date` ASC;
        """.format(from_date=from_date, to_date=to_date, customer_filter=customer_filter, drilling_team_filter=drilling_team_filter), as_dict=True)

    for p in matching_projects:
        if p.expected_start_date < getdate(from_date):
            p.expected_start_date = getdate(from_date)
            if p.start_half_day.lower() == 'nm':
                p.start_half_day = 'vm'
        
        dauer = calc_duration(p.expected_start_date, p.expected_end_date, from_date, to_date)['dauer']
        if p.start_half_day.lower() == 'nm' :
            dauer -= 1
        if p.end_half_day.lower() == 'vm' and (p.expected_end_date.weekday() < 5 and p.expected_end_date <= getdate(to_date)):
            dauer -= 1

        if p.expected_start_date.weekday() > 5:
            p.start_half_day = 'vm'
            if p.expected_start_date.weekday() == 6:
                p.expected_start_date = frappe.utils.add_days(p.expected_start_date, 1)
        p_data = get_project_data(p, dauer)
        projects.append(p_data)
    return projects
    
def get_project_data(p, dauer):
    project = frappe.get_doc("Project", p.get('name'))
    p_object = frappe.get_doc("Object", project.object)
    requires_traffic_control = False
    traffic_light = 0
    toitoi = 0
    blue_drop = 0
    red_drop = 0
    clear_drop = 0
    requires_water_supply = False
    construction_sites = has_construction_site_description(p.get('name'))
    manager_short = frappe.get_cached_value("User", project.manager, "username") if project.manager else ''
    drilling_equipment = []
    construction_site = None
    if construction_sites and len(construction_sites) > 0:
        construction_site = frappe.get_doc("Construction Site Description", construction_sites[0].get('name'))
        for de in (construction_site.drilling_equipment or []):
            drilling_equipment.append(de.drilling_equipment)
        drilling_equipment = ", ".join(drilling_equipment)
        
        if cint(construction_site.requires_traffic_control):
            requires_traffic_control = True
            
        if cint(construction_site.requires_traffic_light):
            traffic_light = 1
            
    if drilling_equipment == []:            # no construction site description, rewrite to empty string
        drilling_equipment = ""
    saugauftrag = 'Schlamm fremd'
    mud = None
    mud_supplier = None
    pneukran = ''
    pneukran_details = {}
    activities = {
        'internal_crane': frappe.get_cached_value("Heim Settings", "Heim Settings", "int_crane_activity"),
        'external_crane': frappe.get_cached_value("Heim Settings", "Heim Settings", "crane_activity"),
        'carrymax': frappe.get_cached_value("Heim Settings", "Heim Settings", "carrymax_activity"),
        'mud': frappe.get_cached_value("Heim Settings", "Heim Settings", "mud_disposer_activity"),
        'trough': frappe.get_cached_value("Heim Settings", "Heim Settings", "trough_activity"),
        'traffic_control': frappe.get_cached_value("Heim Settings", "Heim Settings", "traffic_control_activity"),
        'water_supply': frappe.get_cached_value("Heim Settings", "Heim Settings", "water_supply_activity")
    }
    flag_ext_crane = False
    flag_int_crane = False
    flag_carrymax = False
    flag_override_mud = False
    # read project checklist
    for cl_entry in project.checklist:
        if cl_entry.activity == activities['mud']:
            saugauftrag = cl_entry.supplier_short_display or cl_entry.supplier_name
            if cl_entry.supplier == "L-03749":
                flag_override_mud = True
        elif not flag_ext_crane and cl_entry.activity == activities['external_crane']:
            pneukran_details = cl_entry.as_dict()
            flag_ext_crane = True
        elif not flag_int_crane and cl_entry.activity == activities['internal_crane']:
            pneukran_details = cl_entry.as_dict()
            flag_int_crane = True
        elif cl_entry.activity == activities['trough']:
            mud = cl_entry.supplier_short_display or cl_entry.supplier_name
        elif cl_entry.activity == activities['carrymax']:
            flag_carrymax = True
        elif cl_entry.activity == activities['traffic_control']:
            requires_traffic_control = True
        elif cl_entry.activity == activities['water_supply']:
            if cint(cl_entry.no_hydrant) == 0:
                requires_water_supply = True
            else:
                clear_drop = 1              # mark reuqired but not available
    
    # read construction site
    if construction_site:
        if construction_site.get('carrymax') == 1:
            flag_carrymax = True
        elif construction_site.get('internal_crane_required') == 1:
            flag_int_crane = True
        elif construction_site.get('external_crane_required') == 1:
            flag_ext_crane = True
            
    # set crane base
    if flag_ext_crane:
        pneukran = pneukran_details.get('supplier_short_display') or pneukran_details.get('supplier_name') or "ext. Kran"
        project.crane_required = 1
    if flag_int_crane:
        pneukran = pneukran_details.get('supplier_short_display') or pneukran_details.get('supplier_name') or "int. Kran"
    if flag_ext_crane and flag_int_crane:
        # conflict
        pneukran = "(!)" + pneukran
    if flag_carrymax:
        if pneukran:
            pneukran = "Carrymax, " + pneukran
        else:
            pneukran = "Carrymax"
            
    # extend crane details
    if 'appointment' in pneukran_details and pneukran_details['appointment']:
        
        pneukran += " {0}".format(get_short_time(pneukran_details['appointment']))
    if 'appointment_end' in pneukran_details and pneukran_details['appointment_end']:
        pneukran += " / {0}".format(get_short_time(pneukran_details['appointment_end']))
    
    # extend crane with traffic control
    if requires_traffic_control:
        pneukran += " <b>VD</b>"
    
    # override mud for special case
    if flag_override_mud:
        saugauftrag = mud
    
    # check toitoi status
    toitoi = cint(project.toitoi_ordered)
    
    # check water supply status
    if requires_water_supply:
        water_supply_registrations = frappe.get_all("Water Supply Registration", filters={'project': project.name}, fields=['name'])
        if len(water_supply_registrations) > 0:
            blue_drop = 1
        else:
            red_drop = 1
    
    p_data = {
            'bohrteam': p.get('drilling_team'),
            'start': get_datetime(p.get('expected_start_date')).strftime('%d.%m.%Y'),
            'vmnm': p.get('start_half_day').lower(),
            'dauer': dauer,
            'ampeln': get_traffic_lights_indicator(project),
            'project': project,
            'saugauftrag': saugauftrag,
            'pneukran': pneukran,
            'manager_short': manager_short,
            'drilling_equipment': drilling_equipment,
            'ews_details': (project.ews_details or "").replace("PN20", "<b>PN20</b>").replace("PN35", "<b>PN35</b>").replace("PN50", "<b>PN50</b>"),
            'traffic_light': traffic_light,
            'toitoi': toitoi,
            'red_drop': red_drop,
            'blue_drop': blue_drop,
            'clear_drop': clear_drop,
            'has_subproject': p.get('has_subproject'),
            'drilling_method': p.get('drilling_method')
        }
        
    return p_data

def get_short_time(d):
    day = WEEKDAYS[cint(d.strftime("%w"))]
    s = "{0} {1}".format(day, d.strftime("%H:%M"))
    return s
    
@frappe.whitelist()
def get_internal_overlay_datas(from_date, to_date, customer=None):
    projects = []
    
    customer_filter = ""
    if customer:
        customer_filter =  """ AND `tabProject`.`customer` = "{customer}" """.format(customer=customer)
        
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
                                            WHERE `project_type` = "Internal"
                                              AND 
                                                ((`expected_start_date` BETWEEN '{from_date}' AND '{to_date}')
                                                 OR (`expected_end_date` BETWEEN '{from_date}' AND '{to_date}')
                                                 OR (`expected_start_date` < '{from_date}' AND `expected_end_date` > '{to_date}')
                                                )
                                              {customer_filter}
                                                """.format(from_date=from_date, to_date=to_date, customer_filter=customer_filter), as_dict=True)
    for p in matching_projects:
        project = frappe.get_doc("Project", p.name)
        if p.expected_start_date < getdate(from_date):
            p.expected_start_date = getdate(from_date)
            if p.start_half_day.lower() == 'nm':
                p.start_half_day = 'vm'
        
        dauer = calc_duration(p.expected_start_date, p.expected_end_date, from_date, to_date)['dauer']
        if p.start_half_day.lower() == 'nm' :
            dauer -= 1
        if p.end_half_day.lower() == 'vm' and (p.expected_end_date.weekday() < 5 and p.expected_end_date <= getdate(to_date)):
            dauer -= 1
        
        if p.expected_start_date.weekday() == 6:
            p.expected_start_date = frappe.utils.add_days(p.expected_start_date, 1)
        
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
def get_subproject_overlay_datas(from_date, to_date, drilling_team=None):
    subproject_list = []
    condition = ""
    earliest_start = None
    last_end = None
    if drilling_team:
        condition = """ AND `tabSubcontracting Order`.`drilling_team` = "{drilling_team}" """.format(drilling_team=drilling_team)
        
    subprojects = frappe.db.sql("""
        SELECT
            `tabProject Subproject`.`start`,
            `tabProject Subproject`.`end`,
            `tabProject Subproject`.`team`,
            `tabProject Subproject`.`description`,
            `tabProject Subproject`.`subcontracting_order` AS `subcontracting_order`,
            `tabSubcontracting Order`.`prio`,
            `tabProject`.`name` as `project`,
            `tabProject`.`customer_name` as `customer_name`,
            `tabProject`.`ews_details` as `ews_details`,
            `tabProject`.`object_name`,
            `tabProject`.`object_street`,
            `tabProject`.`object_location`,
            `tabUser`.`username` AS `manager_short`
        FROM `tabProject Subproject`
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabProject Subproject`.`parent`
        LEFT JOIN `tabSubcontracting Order` ON `tabSubcontracting Order`.`name` = `tabProject Subproject`.`subcontracting_order`
        LEFT JOIN `tabUser` ON `tabProject`.`manager` = `tabUser`.`name`
        WHERE 
            (`tabProject Subproject`.`start` BETWEEN "{from_date}" AND "{to_date}"
            OR `tabProject Subproject`.`end` BETWEEN "{from_date}" AND "{to_date}")
            AND `tabProject`.`status` IN ("Open", "Completed")
            {condition}
        ORDER BY 
            `tabProject Subproject`.`team` ASC, `tabProject Subproject`.`start` ASC, `tabSubcontracting Order`.`prio` ASC;""".format(
            from_date=from_date, to_date=to_date, condition=condition), as_dict=True)
    for subproject in subprojects:
        subproject_duration = calc_duration(subproject.start, subproject.end, from_date, to_date)

        if not earliest_start or subproject.start < earliest_start:
            earliest_start = subproject.start
        if not last_end or subproject.end > last_end:
            last_end = subproject.end
            
        subproject_data = {
            'bohrteam': subproject.team,
            'start': get_datetime(subproject_duration['start']).strftime('%d.%m.%Y'),
            'dauer': subproject_duration['dauer'],
            'end': subproject.end,
            'description': subproject.description,
            'id': subproject.name,
            'project': subproject.project,
            'customer_name': subproject.customer_name,
            'ews_details': subproject.ews_details,
            'object_name': subproject.object_name,
            'object_street': subproject.object_street,
            'object_location': subproject.object_location,
            'subcontracting_order': subproject.subcontracting_order,
            'background': get_project_billing_status_color(subproject.project) or "#ffffe0",
            'manager_short': subproject.manager_short
        }
        subproject_list.append(subproject_data)
    
    # shift controller
    if len(subproject_list) > 0:
        current_date = earliest_start
        shift_control = {}
        drilling_teams = frappe.get_all("Drilling Team", filters={'drilling_team_type': 'Verlängerungsteam'}, fields=['name'])
        # prepare a matrix with each day, each team to count active subprojects
        while current_date <= last_end:
            cur_date_str = current_date.strftime('%Y-%m-%d')
            shift_control[cur_date_str] = {}
            for d in drilling_teams:
                # prepare three lanes
                shift_control[cur_date_str][d['name']] = {'0': 0, '1': 0, '2': 0}
            current_date = add_days(current_date, 1)
        for s in subproject_list:
            # check if the relevant parameters start, end and team are available
            if not s['bohrteam'] or not s['start'] or not s['end']:
                continue
            # find first available lane for subproject
            current_date = datetime.strptime(s['start'], '%d.%m.%Y').date()        # need to decode from array
            available_lanes = {'0': 0, '1': 0, '2': 0}
            subproject_days = []
            while current_date <= s['end']:
                cur_date_str = current_date.strftime('%Y-%m-%d')
                subproject_days.append(cur_date_str)
                available_lanes['0'] += shift_control[cur_date_str][s['bohrteam']]['0']
                available_lanes['1'] += shift_control[cur_date_str][s['bohrteam']]['1']
                available_lanes['2'] += shift_control[cur_date_str][s['bohrteam']]['2']

                current_date = add_days(current_date, 1)
                
            if available_lanes['0'] == 0:
                s['subproject_shift'] = 0
                reserve_lane(shift_control, subproject_days, s['bohrteam'], '0')
            elif available_lanes['1'] == 0:
                s['subproject_shift'] = 1
                reserve_lane(shift_control, subproject_days, s['bohrteam'], '1')
            else:
                s['subproject_shift'] = 2
                reserve_lane(shift_control, subproject_days, s['bohrteam'], '2')
    
    return subproject_list

def reserve_lane(shift_control, subproject_days, bohrteam, lane):
    for day in subproject_days:
        shift_control[day][bohrteam][lane] = 1
    return
    
def calc_duration(start, end, from_date, to_date):
    '''
    start = record start date
    end = record end date
    from_date = filter from date
    to_date = filter to date
    start_date = latest (record or filter) start/from date
    end_date = earliest (record or filter) end/to date
    '''
    if start < getdate(from_date):
        start_date = getdate(from_date)
    else:
        start_date = start
    if end > getdate(to_date):
        end_date = getdate(to_date)
    else:
        end_date = end
    
    fixed_start = start_date
    delta = timedelta(days=1)
    duration = 0
    while start_date <= end_date:
        week_day_no = start_date.weekday()
        if week_day_no < 5:
            duration += 2
        else:
            duration += 0.5
        start_date += delta
    
    return {
        'dauer': duration,
        'start': fixed_start
    }
    

def get_project_billing_status_color(project):
    color = None
    sales_order = frappe.get_value("Project", project, "sales_order")
    if sales_order:
        akonto = int(frappe.db.sql("""
            SELECT COUNT(`tabSales Invoice`.`name`) AS `qty` 
            FROM `tabSales Invoice Item`
            LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
            WHERE `tabSales Invoice Item`.`sales_order` = '{so}' 
              AND `tabSales Invoice`.`docstatus` = 1
              AND (`tabSales Invoice`.`title` = "Teilrechnung"
                OR `tabSales Invoice`.`title` LIKE  "%Akonto-Rechnung"); """.format(so=sales_order), as_dict=True)[0].qty)
        if akonto > 0:
            color = BG_LIGHT_GREEN         # light green
        sinv = int(frappe.db.sql("""
            SELECT COUNT(`tabSales Invoice`.`name`) AS `qty` 
            FROM `tabSales Invoice Item` 
            LEFT JOIN `tabSales Invoice` ON `tabSales Invoice`.`name` = `tabSales Invoice Item`.`parent`
            WHERE `tabSales Invoice Item`.`parenttype` = 'Sales Invoice' 
              AND `tabSales Invoice Item`.`sales_order` = '{so}' 
              AND `tabSales Invoice`.`docstatus` = 1 
              AND `tabSales Invoice`.`title` IN ("Schlussrechnung", "Rechnung"); 
            """.format(so=sales_order), as_dict=True)[0].qty)
        if sinv > 0:
            color = BG_GREEN           # green
    return color
    
def get_traffic_lights_indicator(project):
    colors = []
    
    # projeknummer [0]
    projeknummer_color = BG_RED                     # red
    if cint(project.termin_bestaetigt) == 1:
        projeknummer_color = BG_ORANGE              # orange
    billing_color = get_project_billing_status_color(project.name)
    if billing_color:
        projeknummer_color = billing_color
    colors.append(projeknummer_color)
    
    # auftraggeber [1]
    auftraggeber_color = BG_RED                     # red
    if project.sales_order:
        unterzeichnete_ab = frappe.get_value("Sales Order", project.sales_order, "unterzeichnete_ab")
        if unterzeichnete_ab:
            auftraggeber_color = BG_GREEN           # green: signed sales order file
    colors.append(auftraggeber_color)
    
    # objektname [2]
    objektname_color = BG_RED                       # base: red
    found_permits = 0
    found_permits_with_file = 0
    if not project.permits or len(project.permits) == 0:
        objektname_color = BG_GREY                  # project has no permit records: grey
    else:
        for permit in project.permits:
            if 'Bohrbewilligung' in permit.permit:             # formerly if 'Bohrbewilligung kantonal'
                found_permits += 1
                if permit.file:
                    found_permits_with_file += 1
        if found_permits > 0:
            if found_permits == found_permits_with_file:
                objektname_color = BG_GREEN         # all permits available: green
            elif found_permits_with_file > 0:
                objektname_color = BG_ORANGE         # some permits available: orange
    colors.append(objektname_color)
    
    # objekt_strasse [3]
    objekt_strasse_color = BG_GREY              # start with grey
    drill_notices = frappe.get_all("Bohranzeige", filters={'project': project.name}, fields={'name'})
    if len(drill_notices) > 0:
        # has a drill notice: red
        objekt_strasse_color = BG_RED           # red
    if cint(project.drill_notice_sent) == 1:
        objekt_strasse_color = BG_GREEN         # green
    colors.append(objekt_strasse_color)
    
    # objekt_plz_ort [4, 5, 6]
    objekt_plz_ort_color = BG_GREY              # grey
    if int(project.thermozement) == 1:
        objekt_plz_ort_color = BG_BLUE          # blue
    colors.append(objekt_plz_ort_color)         # 4
    objekt_plz_ort_font_color = BG_BLACK
    objekt_plz_ort_border_color = ''
    for permit in project.permits:
        if 'Lärmschutzbewilligung' in permit.permit:
            objekt_plz_ort_font_color = BG_DARK_RED
            if cint(project.noise_permit_requested):
                objekt_plz_ort_font_color = BG_DARK_ORANGE
            if permit.file:
                objekt_plz_ort_font_color = BG_DARK_GREEN            # dark green
        #elif 'Strassensperrung' in permit.permit:              # removed by change request RB/2022-10-05
        #    if not permit.file:
        #        objekt_plz_ort_border_color = 'border: 1px solid red;'
    colors.append(objekt_plz_ort_font_color)       # 5
    colors.append(objekt_plz_ort_border_color)     # 6
    
    #ews_details [7]
    ews_details_color = BG_RED                      # red
    pos = frappe.db.sql("""
        SELECT `per_received`, `order_confirmation`, `status`
        FROM `tabPurchase Order` 
        WHERE `object` = '{0}' 
          AND `docstatus` < 2;""".format(project.object), as_dict=True)
    if len(pos) > 0 and pos[0]['per_received'] != None:
        ews_details_color = BG_YELLOW               # yellow: ordered
        all_confirmed = True
        all_received = True
        for p in pos:
            if p['status'] == "Closed":
                continue
            if not p['order_confirmation']:
                all_confirmed = False
            if cint(p['per_received']) < 100:
                all_received = False
        if all_confirmed:
            ews_details_color = BG_ORANGE           # orange: confirmed
        if all_received:
            ews_details_color = BG_GREEN            # green: available
    colors.append(ews_details_color)
    
    # saugauftrag [8]
    saugauftrag_color = BG_GREY                     # grey
    for cl_entry in project.checklist:
        if cl_entry.activity == 'Schlammentsorgung':
            saugauftrag_color = BG_ORANGE           # orange
            #if cl_entry.supplier_name:
            if project.trough_ordered:
                saugauftrag_color = BG_GREEN        # green
    colors.append(saugauftrag_color)
    
    # pneukran [9]
    pneukran_color = BG_GREY                        # grey
    if cint(project.crane_required) == 1:
        if cint(project.crane_organized) == 1:
            pneukran_color = BG_GREEN               # green
        else:
            pneukran_color = BG_ORANGE              # orange
    colors.append(pneukran_color)
    
    # typ_bohrgeraet [10] - find infomail and file
    typ_bohrgeraet_color = BG_RED                   # start with red
    if has_infomail(project.name):
        typ_bohrgeraet_color = BG_ORANGE            # has infomail: orange
        if project.project_file_created:
            typ_bohrgeraet_color = BG_GREEN         # project file has been created
    colors.append(typ_bohrgeraet_color)
    
    # kuerzel_pl [11]
    kuerzel_pl_color = BG_RED                       # red
    if is_construction_site_inspected(project.name) == 1:
        kuerzel_pl_color = BG_GREEN                 # green
    elif project.visit_date:
        kuerzel_pl_color = BG_ORANGE                # orange
    elif cint(project.visit_mail_sent):
        kuerzel_pl_color = BG_BLUE                  # blue
    colors.append(kuerzel_pl_color)
    
    # strassensperrung [12]
    strassensperrung_color = BG_GREY                    # grey: not applicable
    for permit in project.permits:
        if 'Strassensperrung' in permit.permit:
            #strassensperrung_color = BG_RED            # red: not used - should always be in the list
            if has_public_area_request(project.name):
                strassensperrung_color = BG_ORANGE      # orange: requested
            if permit.file:                         
                strassensperrung_color = BG_GREEN       # green: permit available
    colors.append(strassensperrung_color)
    
    # drill order [13]
    kuerzel_pl_font_color = BG_BLACK
    if cint(project.drill_order_created) == 1:
        kuerzel_pl_font_color = BG_WHITE              # white
    colors.append(kuerzel_pl_font_color)
    return colors

def is_construction_site_inspected(project):
    inspected = frappe.db.sql("""
            SELECT MAX(`tabConstruction Site Description`.`site_inspected`) AS `is_inspected`
            FROM `tabConstruction Site Description`
            WHERE SUBSTRING(`tabConstruction Site Description`.`project`, 1, 8) = SUBSTRING(%(project)s, 1, 8);
        """,
        {'project': project}, 
        as_dict=True
    )
    return inspected[0]['is_inspected'] if len(inspected) > 0 else 0
    
def has_public_area_request(project):
    public_area_requests = frappe.db.sql("""
        SELECT 
            `tabRequest for Public Area Use`.`name`,
            `tabRequest for Public Area Use`.`sent` 
        FROM `tabRequest for Public Area Use` 
        LEFT JOIN `tabRelated Project` ON `tabRelated Project`.`parent` = `tabRequest for Public Area Use`.`name` 
        WHERE 
            `tabRequest for Public Area Use`.`project` = "{project}" 
            OR (`tabRelated Project`.`parenttype` = "Request for Public Area Use"  
                AND `tabRelated Project`.`project` = "{project}");
        """.format(project=project), as_dict=True)
        
    if len(public_area_requests) > 0 and public_area_requests[0]['sent'] == 1:
        return True
    else:
        return False

def has_infomail(project):
    # consider all infomails with the same base project
    infomails = frappe.db.sql("""
        SELECT `name`
        FROM `tabInfomail`
        WHERE `project` LIKE "{project_base}%";
        """.format(project_base=project[:8]), as_dict=True)
    return True if len(infomails) > 0 else False
        
@frappe.whitelist()
def reschedule_project(project=None, team=None, day=None, start_half_day=None, popup=False, 
    new_project_start=None, new_project_end_date=None, end_half_day=None, visit_date=None, log=True):
    project = frappe.get_doc("Project", project)
    if visit_date:
        project.visit_date = visit_date
        
    project_changes = [{
        'project': project.name,
        'from_start_date': project.expected_start_date,
        'from_start_vmnm': project.start_half_day,
        'from_end_date': project.expected_end_date,
        'from_end_vmnm': project.end_half_day,
        'from_drilling_team': project.drilling_team
    }]
    
    if not popup:
        start_date = project.expected_start_date
        end_date = project.expected_end_date
        # find duration in workdays
        project_duration_workdays = get_working_days(project.expected_start_date, project.start_half_day, project.expected_end_date, project.end_half_day)
        
        project_duration = date_diff(end_date, start_date)
        delta = timedelta(days=project_duration)
        
        if day:
            new_project_start_day = day.split(".")[0]
            new_project_start_month = day.split(".")[1]
            new_project_start_year = day.split(".")[2]
            new_project_start = getdate(new_project_start_year + "-" + new_project_start_month + "-" + new_project_start_day)
        
        new_project_end_date = new_project_start + delta
        
        # half day correction
        if project.start_half_day != start_half_day.upper():
            old_start_hd = project.start_half_day
            project.start_half_day = start_half_day.upper()
            if old_start_hd == 'NM':                # start from NM to VM (earlier)
                if project.end_half_day == 'NM':
                    project.end_half_day = 'VM'
                else:
                    project.end_half_day = 'NM'
                    new_project_end_date = new_project_end_date + timedelta(days=-1)     # move to prior day
            else:                                   # start from VM to NM (later)
                if project.end_half_day == 'VM':
                    project.end_half_day = 'NM'
                else:
                    project.end_half_day = 'VM'
                    new_project_end_date = new_project_end_date + timedelta(days=1)     # move to next day
                    
        # verify working days
        correction = 1
        while correction != 0:
            new_working_days = get_working_days(new_project_start, project.start_half_day, new_project_end_date, project.end_half_day)
            correction = floor(project_duration_workdays - new_working_days)
            if correction != 0:
                new_project_end_date = new_project_end_date + timedelta(days=correction)
        
        # if this ends in a weekend, shorten to before weekend
        end_workdays = get_working_days(new_project_end_date, project.end_half_day, new_project_end_date, project.end_half_day)
        while end_workdays <= 0:            # get working days will yield -0.5 on a weekend
            new_project_end_date = new_project_end_date + timedelta(days=-1)
            end_workdays = get_working_days(new_project_end_date, project.end_half_day, new_project_end_date, project.end_half_day)
        
        project.expected_start_date = new_project_start
        project.expected_end_date = new_project_end_date
        project.drilling_team = team
        project.crane_organized = '0'
        project.save()
    else:
        project.expected_start_date = getdate(new_project_start)
        project.expected_end_date = getdate(new_project_end_date)
        project.start_half_day = start_half_day
        project.end_half_day = end_half_day
        new_duration, new_meter_per_day = get_drilling_meters_per_day(project.name, project.object, new_project_start, start_half_day, new_project_end_date, end_half_day)
        project.duration = new_duration
        project.drilling_meter_per_day = new_meter_per_day
        project.drilling_team = team
        project.crane_organized = '0'
        project.save()
    
    # recap and log
    project_changes[-1].update({
        'to_start_date': project.expected_start_date,
        'to_start_vmnm': project.start_half_day,
        'to_end_date': project.expected_end_date,
        'to_end_vmnm': project.end_half_day,
        'to_drilling_team': project.drilling_team
    })
    if log:
        log_drilling_move("Umplanung einzelnes Projekt im Bohrplaner", project_changes)
    return project_changes[-1]

@frappe.whitelist()
def reschedule_subcontracting(subcontracting=None, team=None, day=None):
    subcontracting = frappe.get_doc("Subcontracting Order", subcontracting)
    
    start_date = subcontracting.from_date
    end_date = subcontracting.to_date
    subcontracting_duration = date_diff(end_date, start_date)
    delta = timedelta(days=subcontracting_duration)
    
    new_subcontracting_start_day = day.split(".")[0]
    new_subcontracting_start_month = day.split(".")[1]
    new_subcontracting_start_year = day.split(".")[2]
    new_subcontracting_start = getdate(new_subcontracting_start_year + "-" + new_subcontracting_start_month + "-" + new_subcontracting_start_day)
    
    new_subcontracting_end_date = new_subcontracting_start
    new_subcontracting_end_date += delta
    
    subcontracting.from_date = new_subcontracting_start
    subcontracting.to_date = new_subcontracting_end_date
    
    if frappe.db.exists("Drilling Team", team):
        subcontracting.drilling_team = team
    else:
        team = team.replace("-2", "").replace("-3", "")
        if frappe.db.exists("Drilling Team", team):
            subcontracting.drilling_team = team
    subcontracting.save()
    
@frappe.whitelist()
def get_content(from_date, to_date, only_teams=False):
    data = {}
    data["drilling_teams"] = get_drilling_teams(only_teams)
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

# find the number of full/half working days
def get_working_days(start_date, start_half_day, end_date, end_half_day):
    date_list, weekend_list, kw_list, day_list, today = get_days(start_date, end_date)
    project_duration_workdays = len(date_list) - len(weekend_list)
    if start_half_day == "NM":
        project_duration_workdays -= 0.5
    if end_half_day == "VM":
        project_duration_workdays -= 0.5
    return project_duration_workdays
    
def get_weekend_day_correction(from_date, to_date):
    start_date = getdate(from_date)
    end_date = getdate(to_date)
    delta = timedelta(days=1)
    sundays = 0
    while start_date <= end_date:
        week_day_no = start_date.weekday()
        if week_day_no == 6:
            sundays += 3
        start_date += delta
    
    return sundays
    
def get_drilling_teams(only_teams=False):
    team_filter = ''
    if only_teams:
        team_filter = """AND `drilling_team_type` = 'Bohrteam'"""
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
            `drilling_team_type`,
            `appartment`
        FROM `tabDrilling Team`
        WHERE `drilling_team_type` != 'Deaktiviert'
        {team_filter}""".format(
            trough=_('Has Trough'), crane=_('Has Crane'), team_filter=team_filter), as_dict=True)
        
    return drilling_teams

# Absences
@frappe.whitelist()
def get_absences_overlay_datas(from_date, to_date):
    from_date = getdate(from_date)
    to_date = getdate(to_date)
    absences = []
    shift = 0
    last_date = []
    
    absences_raw = frappe.db.sql("""
        SELECT
            `name`,
            `employee`,
            `employee_name`,
            `from_date`,
            `to_date`,
            `leave_type`,
            `remarks`
        FROM `tabLeave Application`
        WHERE 
            `from_date` <= '{to_date}'
            AND`to_date` >= '{from_date}'
            AND `docstatus` < 2
        ORDER BY `from_date` ASC, `employee_name` ASC;""".format(from_date=from_date, to_date=to_date), as_dict=True)
    
    for absence in absences_raw:
        duration = calc_duration(absence.from_date, absence.to_date, from_date, to_date)     # in ['dauer'] segments
        shift = -1
        if len(last_date) == 0:
            last_date.append(absence.to_date)
            shift = 0
        else:
            for l in range(0, len(last_date)):
                if absence.from_date > last_date[l]:
                    shift = l * 20
                    last_date[l] = absence.to_date
                    break
                    
        if shift < 0:
            shift = len(last_date) * 20
            last_date.append(absence.to_date)
            
        _absence = {
            'start': get_datetime(duration['start']).strftime('%d.%m.%Y'),
            'dauer': duration['dauer'],
            'employee_name': absence.employee_name,
            'absence': absence.name,
            'shift': shift,
            'color': "#90ee90;" if "Militär" in absence.leave_type else "#faa0a0" if "krank" in absence.leave_type.lower() else "#ffffe0;",
            'remarks': absence.remarks
        }
        absences.append(_absence)
    
    return absences

@frappe.whitelist()
def get_user_planning_days(user):
    if frappe.db.exists("Signature", user):
        return {
            'planning_days': frappe.get_value("Signature", user, "planning_days") or 30,
            'planning_past_days': frappe.get_value("Signature", user, "planning_past_days") or 0,
            'print_block_length_factor': frappe.get_value("Heim Settings", "Heim Settings", "block_length_factor") or 51
        }
    else:
        return {
            'planning_days': 30,
            'planning_past_Days': 0,
            'print_block_length_factor': frappe.get_value("Heim Settings", "Heim Settings", "block_length_factor") or 51
        }
    
@frappe.whitelist()
def print_bohrplaner(start_date, previous_week=False, target_file=None):
    from frappe.utils.pdf import get_pdf
    from PyPDF2 import PdfFileWriter
    from frappe.utils.pdf import get_file_data_from_writer
    from erpnextswiss.erpnextswiss.attach_pdf import create_folder

    if not target_file:
        fname = "Bohrplaner.pdf"
        # clean old "Bohrplaner.pdf" from files and file system
        bp_files = frappe.get_all("File", filters={'file_name': fname})
        for f in bp_files:
            doc = frappe.get_doc("File", f['name'])
            doc.delete()
    
    html = get_bohrplaner_html(start_date, previous_week)
    
    output = PdfFileWriter()
    output = get_pdf(html, output=output)
    
    if not target_file:
        folder = create_folder("Bohrplaner-Prints", "Home")
        
        filedata = get_file_data_from_writer(output)
        
        _file = frappe.get_doc({
            "doctype": "File",
            "file_name": fname,
            "folder": folder,
            "is_private": 1,
            "content": filedata
        })
        
        _file.save(ignore_permissions=True)
        
        return {'url': _file.file_url, 'name': _file.name}
    else:
        output_stream = open(target_file, "wb")
        output.write(output_stream)
        output_stream.close()
        
        return {'url': None, 'name': target_file}

def backup():
    # prepare date: start today for the backup (if you start on next Monday, the current week will not be visible)
    target_file="/tmp/Bohrplaner.pdf"
    today = date.today()
    today_str = "{y:04d}-{m:02d}-{d:02d}".format(y=today.year, m=today.month, d=today.day)
    # create the pdf as a local file
    f = print_bohrplaner(today_str, previous_week=True, target_file=target_file)
    # upload to nextcloud
    write_file_to_base_path(target_file)
    return
    
def get_bohrplaner_css():
    return frappe.read_file("{0}{1}".format(frappe.utils.get_bench_path(), "/apps/heimbohrtechnik/heimbohrtechnik/heim_bohrtechnik/page/bohrplaner/bohrplaner.css"))
    
def get_bohrplaner_html(start_date, previous_week=False):
    end_date = frappe.utils.add_days(start_date, 20)
    if previous_week:
        start_date = frappe.utils.add_days(start_date, -7)

    timeline = []

    data = {
        'grid': get_content(start_date, end_date, only_teams=True),
        'start_date': start_date,
        'drilling_teams': {},
        'css': get_bohrplaner_css(),
        'weekend_columns': []
    }
    
    
    for key, value in data['grid']['day_list'].items():
        if value == "Mon" or value == "Tue" or value == "Wed" or value == "Thu" or value == "Fri":
            timeline.append({"date": key, "day": value, "vmnm": "VM"})
            timeline.append({"date": key, "day": value, "vmnm": "NM"})
        elif value == "Sat":
            timeline.append({"date": key, "day": value, "vmnm": "VM"})
    
    #get weekend columns for grid
    weekend_columns = []
    desired_values = ['Sat', 'Sun']
    saturday_value = ['Sat']
    real_weekends = [key for key, value in data['grid']['day_list'].items() if value in desired_values]
    saturdays = [key for key, value in data['grid']['day_list'].items() if value in saturday_value]
    i = 0
    for day in data['grid']['day_list']:
        i += 1
        if not day in real_weekends:
            if day in data['grid']['weekend']:
                weekend_columns.append(i)
                i += 1
                weekend_columns.append(i)
            else:
                i += 1
        else:
            if day in saturdays:
                weekend_columns.append(i)
            else:
                i -= 1
    
    data['weekend_columns'] = weekend_columns
    drilling_teams = {}
        
    for drilling_team in data['grid']['drilling_teams']:
        # get all projects
        for project in timeline:
            print(project)
            projects = frappe.db.sql("""SELECT `name`, `project_type`, `object_name`
                        FROM `tabProject` 
                        WHERE CONCAT(`expected_start_date`, " ", IF(`start_half_day` = "VM", "06", "14")) <= '{date}' 
                        AND CONCAT(`expected_end_date`, " ", IF(`end_half_day` = "VM", "06", "14")) >= '{date}'
                        AND `drilling_team` = '{drillt}'
                        AND `status` IN ("Open", "Completed")
                        ORDER BY `project_type` DESC, 
                        `expected_start_date` DESC;""".format(
                        date = "{0} {1}".format(datetime.strptime(project['date'], "%d.%m.%Y").strftime("%Y-%m-%d"), "06" if project['vmnm'] == "VM" else "14"),
                        drillt = drilling_team['team_id']), as_dict=True)
            
            if len(projects) > 0:
                project['project'] = projects[0]['name']
                project['project_type'] = projects[0]['project_type']
                project['object_name'] = projects[0]['object_name']
            else:
                project['project'] = None
                
        stacked_projects = []
        same_project = set()
        
        for i in range(0, len(timeline)):
            last_project = None
            if len(stacked_projects) > 0 and 'project' in stacked_projects[-1]:
                last_project = stacked_projects[-1]['project'].get('name')
            if len(stacked_projects) == 0 or last_project != timeline[i]['project']:
                if timeline[i].get("project_type") == "External":
                    if timeline[i]['project'] in same_project and timeline[i]['project'] != None:
                        actual_project = {
                            'name': timeline[i]['project'],
                            'drilling_team': drilling_team['team_id'],
                            'start_half_day': timeline[i]['vmnm'],
                            'expected_start_date': timeline[i]['date']
                        }
                        project_data = get_project_data(actual_project, 1)
                        project_data['project_type'] = 'extension'
                        stacked_projects.append(project_data)
                    else:
                        actual_project = {
                            'name': timeline[i]['project'],
                            'drilling_team': drilling_team['team_id'],
                            'start_half_day': timeline[i]['vmnm'],
                            'expected_start_date': timeline[i]['date']
                        }
                        stacked_projects.append(
                            get_project_data(actual_project, 1) if timeline[i]['project'] else {'dauer': 1})
                        actual_value = timeline[i].get('project')
                        same_project.add(actual_value)
                else:
                    if timeline[i].get('project'):
                        int_p_data = {
                            'name': timeline[i]['project'],
                            'drilling_team': drilling_team['team_id'],
                            'dauer': 1,
                            'project' : {
                                'object_name': timeline[i].get('object_name'),
                                'name': timeline[i]['project']
                            },
                            'project_type': "internal"
                        }
                        stacked_projects.append(int_p_data)
                    else:
                        stacked_projects.append({'dauer': 1})
            else:
                #extend former project
                stacked_projects[-1]['dauer'] += 1
        data['drilling_teams'][drilling_team['team_id']] = stacked_projects
    
    html = frappe.render_template("heimbohrtechnik/heim_bohrtechnik/page/bohrplaner/print.html", data)
    return html
    
    
def get_gap_duration(start_date, start_half_day, end_date, end_half_day):
    date_list, weekend_list, kw_list, day_list, today = get_days(start_date, end_date)
    desired_values = ['Sat', 'Sun']
    real_weekends = [key for key, value in day_list.items() if value in desired_values]
    gap_duration_workdays = len(date_list) - len(real_weekends)
    if start_half_day == "NM" and start_date not in real_weekends:
        gap_duration_workdays -= 0.5
    if end_half_day == "VM" and end_date not in real_weekends:
        gap_duration_workdays -= 0.5

    gap_duration = gap_duration_workdays * 2
    if len(real_weekends) != 0:
        gap_duration += 1
    for i in range(1, len(weekend_list)):
        multiple_weekends = date_diff(datetime.strptime(weekend_list[i], "%d.%m.%Y"), datetime.strptime(weekend_list[i-1], "%d.%m.%Y"))
        if multiple_weekends == 6:
            gap_duration += 1

    return gap_duration
    

"""
In open projects, find conflicts with regional holidays.
"""
def find_holiday_conflicts():
    # get regions
    regions = frappe.get_all("Regional Holidays", fields=['region'])
    
    conflicted_projects = []
    for region in regions:
        # fetch holidays
        holidays_raw = frappe.db.sql("""
                SELECT `holiday_date` AS `date`
                FROM `tabHoliday`
                WHERE `parent` = "{region}"
                  AND `parenttype` = "Regional Holidays"
                  AND `holiday_date` >= CURDATE();
            """.format(region=region['region']), as_dict=True)
            
        holidays = []
        for h in holidays_raw:
            holidays.append(h['date'])
        
        # get all open projects in this region
        projects = frappe.db.sql("""
            SELECT `name`, `expected_start_date`, `expected_end_date`, `drilling_team`
            FROM `tabProject`
            WHERE
                `status` = "Open"
                AND `object_location` LIKE "%{region}"
                AND `expected_start_date` IS NOT NULL
                AND `expected_end_date` IS NOT NULL
                AND `project_type` != "Internal"
            """.format(region=region['region']), as_dict=True)
        
        for project in projects:
            contained = False
            # check if any holiday is in this planned period
            for h in holidays:
                if (h >= project['expected_start_date']) and (h <= project['expected_end_date']):
                    contained = h
                    continue
            
            if contained:
                conflicted_projects.append(
                    {
                        'project': project['name'],
                        'date': contained,
                        'region': region['region'],
                        'url': get_url_to_form("Project", project['name']),
                        'drilling_team': project['drilling_team']
                    }
                )
    # sort conflicts by ascending date
    sorted_conflicted_projects = sorted(conflicted_projects, key=lambda d: d['date'], reverse=False)
    
    return sorted_conflicted_projects

"""
In open projects, per drilling team, find overlaps
"""
def find_project_conflicts(drilling_team=None):
    # get drilling teams
    if drilling_team:
        drilling_teams = [{'name': drilling_team}]
    else:
        drilling_teams = frappe.get_all("Drilling Team", filters={'drilling_team_type': 'Bohrteam'}, fields=['name'])
    
    conflicted_projects = []
    # get all open projects in drilling team
    for drilling_team in drilling_teams:
        # get all open projects in this drilling team           # 2023-06-05 removed , "Completed" OVe
        projects = frappe.db.sql("""
            SELECT `name`, `expected_start_date`, `expected_end_date`, `start_half_day`, `end_half_day`
            FROM `tabProject`
            WHERE
                `status` IN ("Open")
                AND `drilling_team` = "{0}"
                AND `expected_start_date` IS NOT NULL
                AND `expected_end_date` >= CURDATE()
                AND `name` NOT LIKE "P-INT-%"
            ORDER BY `expected_start_date` ASC, `modified` DESC
            """.format(drilling_team['name']), as_dict=True)
            
        if len(projects) > 1:
            for p in range(0, (len(projects) - 1)):
                if projects[p]['expected_end_date'] > projects[p+1]['expected_start_date'] \
                    or (projects[p]['expected_end_date'] == projects[p+1]['expected_start_date'] and (projects[p]['end_half_day'] == "NM" or projects[p+1]['start_half_day'] == "VM")):
                    # find by conflict affected subcontracting orders, public area uses, cranes and infomails
                    conflicted_projects.append(
                        get_conflict_details(p1=projects[p]['name'], p2=projects[p+1]['name'])
                    )
    
    return conflicted_projects

"""
p1 is the first and p2 the second project
"""
def get_conflict_details(p1, p2):
    p1_doc = frappe.get_doc("Project", p1)
    p2_doc = frappe.get_doc("Project", p2)
    ext_crane_activity = frappe.get_cached_value("Heim Settings", "Heim Settings", "crane_activity")
    
    # find by conflict affected subcontracting orders, public area uses, cranes and infomails
    road_blocks = frappe.db.sql("""
        SELECT 
            `tabRequest for Public Area Use`.`name`,
            `tabRequest for Public Area Use`.`from_date`,
            `tabRequest for Public Area Use`.`to_date`
        FROM `tabRequest for Public Area Use`
        LEFT JOIN `tabRelated Project` ON `tabRelated Project`.`parent` = `tabRequest for Public Area Use`.`name`
        WHERE 
            `tabRequest for Public Area Use`.`project` = "{project}"
            OR `tabRelated Project`.`project` = "{project}"
    """.format(project=p2), as_dict=True)
    
    infomails = frappe.db.sql("""
        SELECT 
            `tabInfomail`.`name`
        FROM `tabInfomail`
        WHERE 
            `tabInfomail`.`project` = "{project}"
    """.format(project=p2), as_dict=True)
    
    crane = None
    for c in p2_doc.checklist:
        if c.activity == ext_crane_activity:
            crane = {
                'crane': c.activity,
                'supplier': c.supplier,
                'supplier_name': c.supplier_name,
                'appointment': c.appointment,
                'appointment_end': c.appointment_end
            }
            
    # find hte next project (adjacent), as this would have a conflict if this conflict is resolved
    adjacent_project = frappe.db.sql("""
        SELECT `name`
        FROM `tabProject`
        WHERE `drilling_team` = "{drilling_team}"
          AND (`expected_start_date` = "{same_day}"
               OR `expected_start_date` = "{next_day}");
    """.format(drilling_team=p2_doc.drilling_team, same_day=p2_doc.expected_end_date,
        next_day=(p2_doc.expected_end_date + timedelta(days=1))), as_dict=True)
    if len(adjacent_project) > 0:
        adjacent_project = adjacent_project[0]['name']
    else:
        adjacent_project = None
        
    return {
        'project': p1,
        'conflict': p2,
        'drilling_team': p2_doc.drilling_team,
        'details': "{0} ({2}) > {1} ({3})".format(p1_doc.expected_end_date, 
            p2_doc.expected_start_date, p1_doc.end_half_day, p2_doc.start_half_day),
        'subprojects': p2_doc.subprojects,
        'road_blocks': road_blocks,
        'crane': crane,
        'infomails': infomails,
        'url': get_url_to_form("Project", p1),
        'conflict_url': get_url_to_form("Project", p2),
        'adjacent_project': adjacent_project
    }
                    
"""
Find and prerender conflicts
"""
@frappe.whitelist()
def get_conflicts():
    conflicts = {
        'project_conflicts': find_project_conflicts(),
        'holiday_conflicts': find_holiday_conflicts()
    }
    html = frappe.render_template("heimbohrtechnik/heim_bohrtechnik/page/bohrplaner/conflict_dialog.html", conflicts)
    return html

"""
Resolve conflicts of a drilling team
"""
@frappe.whitelist()
def resolve_conflicts(drilling_team, debug=True):
    # get all conflicts
    conflicts = find_project_conflicts(drilling_team)
    project_changes = []
    # iterate to resolve conflicts
    while (len(conflicts) > 0):
        # find next start
        if frappe.get_value("Project", conflicts[0]['project'], 'end_half_day') == "VM":       # ends on VM/morning
            next_half_day = "NM"
            next_date = frappe.get_value("Project", conflicts[0]['project'], 'expected_end_date')
        else:                               # ends on NM / afternoon: next day
            next_half_day = "VM"
            next_date = frappe.get_value("Project", conflicts[0]['project'], 'expected_end_date') + timedelta(days=1)
        # make sure new start is not on a holiday
        workdays = get_working_days(next_date, next_half_day, next_date, next_half_day)
        while workdays <= 0:            # get working days will yield -0.5 on a weekend
            next_date = next_date + timedelta(days=1)
            workdays = get_working_days(next_date, next_half_day, next_date, next_half_day)
            
        # move later project to next available date
        project_changes.append(reschedule_project(
            project=conflicts[0]['conflict'], 
            team=drilling_team,
            new_project_start=next_date,
            start_half_day=next_half_day,
            popup=False,
            log=False
        ))
        
        # iterate to find next conflict
        conflicts = find_project_conflicts(drilling_team)
    
    if len(project_changes) > 0:
        log_drilling_move("Konflikte gelöst in {0}".format(drilling_team), project_changes)
    return

"""
Get Subproject Overview for Project Search Dialog
"""
@frappe.whitelist()
def get_subproject_overview(project):
    subprojects = frappe.db.sql("""
                                    SELECT
                                        `subcontracting_order` AS `subproject`,
                                        `start`,
                                        `end`,
                                        `team`,
                                        `description`
                                    FROM `tabProject Subproject`
                                    WHERE `parent` = '{project}'
                                """.format(project=project), as_dict=True)
    if len(subprojects) > 0:
        table = """<p>Mit dem Projekt verknüpfte Unterprojekte:</p>
                    <table style="width:100%;" class="project-search-modal-table">
                        <thead>
                            <tr>
                                <th>Start</th>
                                <th>Ende</th>
                                <th>Team</th>
                                <th>Beschreibung</th>
                            </tr>
                        </thead>
                        <tbody>"""
        for sub_p in subprojects:
            table += """
                        <tr onclick="route_to_subproject(this);" data-subproject="{4}" data-start="{5}">
                            <td>{0}</td>
                            <td>{1}</td>
                            <td>{2}</td>
                            <td>{3}</td>
                        </tr>
                    """.format(frappe.utils.get_datetime(sub_p.start).strftime('%d.%m.%Y'), \
                    frappe.utils.get_datetime(sub_p.end).strftime('%d.%m.%Y'), \
                    sub_p.team, sub_p.description, sub_p.subproject, sub_p.start)
        
        table += """</tbody></table>""".format(subprojects[0].start, subprojects[0].subproject)
        return table
    else:
        return """<p>Keine Unterprojekte vorhanden.</p>"""

@frappe.whitelist()
def get_mfk_overlay_datas(from_date, to_date):
    sql_query = """
                    SELECT 
                    `truck`, 
                    `drilling_team`, 
                    `start_time`, 
                    `end_time`
                    FROM `tabMFK`
                    WHERE `start_time` BETWEEN '{from_date}' AND '{to_date}'
                    OR `end_time` BETWEEN '{from_date}' AND '{to_date}'
                """.format(from_date=from_date, to_date=to_date)
                
    data = frappe.db.sql(sql_query, as_dict=True)
    mfk_data = []
    shifts = {}
    for entry in data:
        # build a key map to see duplicate services
        key = "{0}:{1}".format(entry.drilling_team, entry.start_time)
        if key not in shifts:
            shifts[key] = 1
            _shift = 0
        else:
            _shift = 12 * shifts[key]
            shifts[key] += 1
            
        mfk_data.append({
            'truck': entry.truck,
            'drilling_team': entry.drilling_team,
            'start_date': frappe.utils.get_datetime(entry.start_time).strftime('%d.%m.%Y'),
            'start_time': frappe.utils.get_datetime(entry.start_time).strftime('%H:%M:%S'),
            'end_date': frappe.utils.get_datetime(entry.end_time).strftime('%d.%m.%Y'),
            'end_time': frappe.utils.get_datetime(entry.end_time).strftime('%H:%M:%S'),
            'shift': _shift
        })
    
    return mfk_data

"""
This function will move all projects, start with the provided project by (days) days
"""
@frappe.whitelist()
def move_projects(from_project, drilling_team, days):
    if not drilling_team:
        return {'error': 'No drilling team'}

    if type(days) != float:
        days = float(days)

    start_date = frappe.get_value("Project", from_project, "expected_start_date")
    if not start_date:
        return {'error': 'No start date found'}
    
    raw_projects = frappe.db.sql("""SELECT
            `name`,
            `expected_start_date`,
            `expected_end_date`,
            `fixed_date`
        FROM `tabProject`
        WHERE 
            `drilling_team` = "{drilling_team}"
            AND `expected_start_date` >= "{start_date}"
        ORDER BY `expected_start_date` ASC
        ;
    """.format(drilling_team=drilling_team, start_date=start_date), as_dict=True)
    
    projects = []
    first_project = True
    fixed_project = None
    
    for project in raw_projects:
        if first_project == True:
            projects.append({
                'name': project.name
            })
            first_project = False
            last_project = project
        else:
            gap = get_gap(last_project.expected_end_date, project.expected_start_date)
            if gap >= days and days > 0:
                break
            else:
                projects.append({
                    'name': project.name
                })
                last_project = project
        if project.fixed_date == 1:
            fixed_project = project.name
            
    if fixed_project:
        frappe.msgprint('Fixiertes Projekt {0} betroffen - Schieben abgebrochen!'.format(fixed_project), title='Achtung', indicator='red')
        return {'success': 0, 'project_changes': "None"}
    
    project_changes = []
    for p in projects:
        p_doc = frappe.get_doc("Project", p['name'])
        project_changes.append({
            'project': p_doc.name,
            'from_start_date': p_doc.expected_start_date,
            'from_start_vmnm': p_doc.start_half_day,
            'from_end_date': p_doc.expected_end_date,
            'from_end_vmnm': p_doc.end_half_day,
            'from_drilling_team': p_doc.drilling_team
        })
        
        duration = get_duration_days(p_doc.expected_start_date, p_doc.start_half_day, p_doc.expected_end_date, p_doc.end_half_day)
        new_project_dates = move_project(p_doc.expected_start_date, p_doc.start_half_day, duration, days)
        p_doc.expected_start_date = new_project_dates['start_date']
        p_doc.start_half_day = new_project_dates['start_hd']
        p_doc.expected_end_date = new_project_dates['end_date']
        p_doc.end_half_day = new_project_dates['end_hd']
                
        p_doc.save()
        
        # recap and log
        project_changes[-1].update({
            'to_start_date': p_doc.expected_start_date,
            'to_start_vmnm': p_doc.start_half_day,
            'to_end_date': p_doc.expected_end_date,
            'to_end_vmnm': p_doc.end_half_day,
            'to_drilling_team': p_doc.drilling_team
        })
        
    frappe.db.commit()
    
    log_drilling_move("Projekte ab {0} schieben".format(from_project), project_changes)
    
    return {'success': 1, 'project_changes': project_changes}
    
"""
This function will add days until the date is no longer a holiday.

Test: $ bench execute heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner.holiday_safe_add_days --kwargs "{'source_date': '2023-07-31', 'days': 1}"
"""
@frappe.whitelist()
def holiday_safe_add_days(source_date, days):
    if type(source_date) == str:
        source_date = datetime.strptime(source_date, "%Y-%m-%d")
    if type(days) == str:
        days = cint(days)
    
    target_date = source_date + timedelta(days=days)
    while (date_is_holiday(target_date)):
        target_date = target_date + timedelta(days=1)
    return target_date
    
def date_is_holiday(date):
    is_holiday = frappe.db.sql("""
        SELECT `parent`
        FROM `tabHoliday`
        WHERE `holiday_date` = "{date}";""".format(date=date), as_dict=True)
    if len(is_holiday) > 0:
        return True
    else:
        return False
   
def log_drilling_move(title, project_changes):
    log = frappe.get_doc({
        'doctype': 'Drilling Move Log',
        'title': title,
        'date': datetime.now()
    })
    for c in project_changes:
        log.append('projects', c)
        
    log.insert()
    frappe.db.commit()
    return log.name
    
def get_gap(start, end):
    date = frappe.utils.add_days(start, 1)
    gap_length = 0
    date_list, weekend_list, kw_list, day_list, today = get_days(start, end)
    while date < end:
        if date.strftime("%d.%m.%Y") in weekend_list:
            date = frappe.utils.add_days(date, 1)
        else:
            gap_length += 1
            date = frappe.utils.add_days(date, 1)
    
    return gap_length

@frappe.whitelist()
def get_project_details(project):
    details = {
        'project': {},
        'object': {},
        'construction_site_description': {}
    }
    
    if frappe.db.exists("Project", project):
        project_doc = frappe.get_doc("Project", project)
        details['project'] = project_doc.as_dict()
        if project_doc.object:
            object_doc = frappe.get_doc("Object", project_doc.object)
            details['object'] = object_doc.as_dict()
        construction_site_descriptions = has_construction_site_description(project)
        if construction_site_descriptions:
            construction_site_doc = frappe.get_doc("Construction Site Description", construction_site_descriptions[0]['name'])
            details['construction_site_description'] = construction_site_doc.as_dict()
        if project_doc.manager:
            user_doc = frappe.get_doc("User", project_doc.manager)
            details["project"]["manager_name"] = user_doc.full_name
            
    return details
    
