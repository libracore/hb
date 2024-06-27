# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.core.doctype.communication.email import make as make_email
from frappe.utils.data import getdate
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_overlay_datas

class FeedbackDrillingMeter(Document):
    def validate(self):
        self.get_weekday()
        
    def get_weekday(self):
        date = frappe.utils.data.getdate(self.date)
        self.day = date.strftime('%A')
        
def reminder():
    #get yesterday
    yesterday = frappe.utils.add_days(getdate(), -1)
    
    #check if yesterday was a working day -> Do Nothing if yes
    holiday = frappe.db.sql("""
                            SELECT
                                `holiday_date`
                            FROM
                                `tabHoliday`
                            WHERE
                                `holiday_date` = '{day}'""".format(day=yesterday), as_dict=True)
    if len(holiday) > 0:
        return
    
    projects = get_overlay_datas(yesterday, yesterday, customer=None, drilling_team=None)
    for project in projects:
        entry = frappe.db.sql("""
                        SELECT
                            `name`
                        FROM
                            `tabFeedback Drilling Meter`
                        WHERE
                            `date` = '{date}'
                        AND
                            `drilling_team` = '{dt}'
                        AND
                            `docstatus` = 1""".format(date=yesterday, dt=project.get('bohrteam')), as_dict=True)
        if not entry:
            # send mail
            make_email(
                recipients=frappe.db.get_value("Drilling Team", project.get('bohrteam'), "email"),
                sender= "Administrator",
                subject="Erinnerung: BohrmeterRückmeldung",
                content="Guten Morgen,<br><br>du hast gestern ({0}) keine Bohrmeter Rückmeldung eingereicht.".format(yesterday.strftime("%Y-%m-%d")),
                doctype="Feedback Drilling Meter",
                name=None,
                print_format="Standard",
                attachments=[],
                send_email=True
            )
        else:
            return
