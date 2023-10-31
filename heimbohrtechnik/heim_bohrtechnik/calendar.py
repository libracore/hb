# -*- coding: utf-8 -*-
# Copyright (c) 2018-2023, libracore and contributors
# For license information, please see license.txt
#
# call the API from
#   /api/method/heimbohrtechnik.heim_bohrtechnik.calendar.download_calendar?secret=[secret]
#   /api/method/heimbohrtechnik.heim_bohrtechnik.calendar.download_mfk_calendar?secret=[secret]

from icalendar import Calendar, Event
from datetime import datetime
import frappe

def get_calendar(secret, user=None):
    # check access
    caldav_secret = frappe.db.get_value("Heim Settings", "Heim Settings", "caldav_secret")
    if not caldav_secret:
        return
    if secret != caldav_secret:
        return
        
    # initialise calendar
    cal = Calendar()

    # set properties
    cal.add('prodid', '-//libracore business software//libracore//')
    cal.add('version', '2.0')

    # get data
    if not user:
        sql_query = """
            SELECT * 
            FROM `tabProject` 
            WHERE `visit_date` IS NOT NULL;
        """
    else:
        sql_query = """
            SELECT * 
            FROM `tabProject` 
            WHERE 
                `visit_date` IS NOT NULL
                AND `project_manager` = "{user}";
        """.format(user=user)
    visits = frappe.db.sql(sql_query, as_dict=True)
    # add visits
    for erp_visit in visits:
        event = Event()
        event.add('summary', erp_event['name'])
        event.add('dtstart', erp_event['visit_date'])
        #if erp_event['ends_on']:
        #    event.add('dtend', erp_event['ends_on'])
        event.add('dtstamp', erp_event['modified'])
        event.add('description', "{0}\n\r{1}\n\r{2}".format(
            erp_event['object_name'], 
            erp_event['object_street'], 
            erp_event['object_location']))
        # add to calendar
        cal.add_component(event)
    
    return cal

@frappe.whitelist(allow_guest=True)
def download_calendar(secret, user=None):
    frappe.local.response.filename = "calendar.ics"
    calendar = get_calendar(secret, user)
    if calendar:
        frappe.local.response.filecontent = calendar.to_ical()
    else:
        frappe.local.response.filecontent = "No access"
    frappe.local.response.type = "download"

def get_mfk_calendar(secret):
    # check access
    caldav_secret = frappe.db.get_value("Heim Settings", "Heim Settings", "caldav_secret")
    if not caldav_secret:
        return
    if secret != caldav_secret:
        return
        
    # initialise calendar
    cal = Calendar()

    # set properties
    cal.add('prodid', '-//libracore business software//libracore//')
    cal.add('version', '2.0')

    # get data
    sql_query = """
        SELECT * 
        FROM `tabMFK` 
        ORDER BY `start_time` DESC;
    """
    events = frappe.db.sql(sql_query, as_dict=True)
    # add visits
    for e in events:
        event = Event()
        event.add('summary', "MFK {0} ({1})".format(e['truck'], e['drilling_team']))
        event.add('dtstart', e['start_time'])
        event.add('dtend', e['end_time'])
        event.add('dtstamp', e['modified'])
        event.add('description', "{0}\n\r{1}\n\r{2}".format(
            "MFK", 
            e['truck'], 
            e['drilling_team']))
        # add to calendar
        cal.add_component(event)
    
    return cal

@frappe.whitelist(allow_guest=True)
def download_mfk_calendar(secret):
    frappe.local.response.filename = "calendar.ics"
    calendar = get_mfk_calendar(secret)
    if calendar:
        frappe.local.response.filecontent = calendar.to_ical()
    else:
        frappe.local.response.filecontent = "No access"
    frappe.local.response.type = "download"
