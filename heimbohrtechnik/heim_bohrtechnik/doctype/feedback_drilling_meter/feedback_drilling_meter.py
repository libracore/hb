# -*- coding: utf-8 -*-
# Copyright (c) 2023-2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.core.doctype.communication.email import make as make_email
from frappe.utils.data import getdate
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_overlay_datas
from frappe.utils import cint

class FeedbackDrillingMeter(Document):
    def validate(self):
        self.get_weekday()
        
    def get_weekday(self):
        date = frappe.utils.data.getdate(self.date)
        self.day = date.strftime('%A')
        
    def autoname(self):
        self.name = "{0} - {1}".format(self.drilling_team, self.date)
        
def reminder():
    #check settings
    reminder_active = frappe.db.get_value("Heim Settings", "Heim Settings", "send_feedback_reminder")
    if cint(reminder_active) == 0:
        return
    else:
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
                                `finished_document` = 1""".format(date=yesterday, dt=project.get('bohrteam')), as_dict=True)
            if not entry:
                #check if reminder is deactivated for this drilling team
                reminder_check = frappe.db.get_value("Drilling Team", project.get('bohrteam'), "not_remember_feedback")
                if cint(reminder_check) == 1:
                    return
                else:
                    # send mail
                    default_sender = frappe.get_all("Email Account", 
                        filters={'enable_outgoing': 1, 'default_outgoing': 1}, 
                        fields=['name', 'email_id'])
                    make_email(
                        recipients=frappe.db.get_value("Drilling Team", project.get('bohrteam'), "email"),
                        sender=default_sender[0]['email_id'],
                        subject="Erinnerung: Bohrmeter Rückmeldung",
                        content="Guten Morgen,<br><br>du hast gestern ({0}) keine Bohrmeter Rückmeldung eingereicht.".format(yesterday.strftime("%d.%m.%Y")),
                        send_email=True)
                        
                    #check two additional days and send mail to head if there were no feedbacks for more than two days
                    check_inactivity(yesterday, project.get('bohrteam'), default_sender)

def check_inactivity(yesterday, drilling_team, default_sender):
    next_checking_date = frappe.utils.add_days(yesterday, -1)
    checked_dates = 1
    
    #go one day back and check if there is a project for drilling team
    while checked_dates < 3:
        is_checking_date = get_overlay_datas(next_checking_date, next_checking_date, customer=None, drilling_team=drilling_team)
        if len(is_checking_date) > 0:
            #if there is a project, check if a feedback has been submitted
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
                                `finished_document` = 1""".format(date=next_checking_date, dt=drilling_team), as_dict=True)
            
            #if there is a feedback return with nothing, else add 1 to checked days
            if len(entry) > 0:
                return
            else:
                checked_dates += 1
                next_checking_date = frappe.utils.add_days(next_checking_date, -1)
        else:
            next_checking_date = frappe.utils.add_days(next_checking_date, -1)
                
    #if there are 3 missing dates in sequence, send Mail to Responsible
    if checked_dates >= 3:
        make_email(
            recipients=frappe.db.get_value("Heim Settings", "Heim Settings", "feedback_responsible"),
            sender=default_sender[0]['email_id'],
            subject="Fehlende Bohrmeterrückmeldungen",
            content="Guten Morgen,<br><br>{0} hat seit 3 Tagen keine Bohrmeter Rückmeldung eingereicht.".format(drilling_team),
            send_email=True)
    else:
        return
