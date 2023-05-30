# -*- coding: utf-8 -*-
# Copyright (c) 2018-2023, libracore and contributors
# For license information, please see license.txt
#
# call the API from
#   /api/method/heimbohrtechnik.heim_bohrtechnik.calendar.download_calendar?secret=[secret]
#

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
            FROM `tabEvent` 
            WHERE `event_type` = 'Public';
        """
    else:
        sql_query = """
            SELECT * 
            FROM `tabEvent` 
            WHERE 
                `event_type` = 'Private'
                AND `project_manager` = "{user}";
        """.format(user=user)
    events = frappe.db.sql(sql_query, as_dict=True)
    # add events
    for erp_event in events:
        event = Event()
        event.add('summary', erp_event['subject'])
        event.add('dtstart', erp_event['starts_on'])
        if erp_event['ends_on']:
            event.add('dtend', erp_event['ends_on'])
        event.add('dtstamp', erp_event['modified'])
        event.add('description', erp_event['description'])
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
