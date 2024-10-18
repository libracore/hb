# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_years

class Abo(Document):
	pass
    
def send_abo_reminder():
    #check if reminder should be sent
    if frappe.db.get_value("Heim Settings", "Heim Settings", "send_abo_reminder"):
        print("0")
        #get all abos with needed reminders
        abos_with_reminder = frappe.db.sql("""
                                            SELECT
                                                `name`,
                                                `customer_name`
                                            FROM
                                                `tabAbo`
                                            WHERE
                                                `next_reminder` <= CURDATE()
                                            AND
                                                `disabled` = 0""", as_dict=True)
        print(abos_with_reminder)
        #send Reminder and update Abo Document
        for abo in abos_with_reminder:
            recipient = send_email_reminder(abo.get('name'), abo.get('customer_name'))
            update_abo(abo.get('name'), recipient)
            
    return
        
def send_email_reminder(abo_name, customer_name):
    print("1")
    #get recipient
    recipient = frappe.db.get_value("Heim Settings", "Heim Settings", "abo_reminder_to")
    
    #create subject and message
    subject = "Abo {0}".format(abo_name)
    message = "Guten Tag,<br><br>bei Abo {0} von {1} steht die Verlängerung an.<br><br>Freundliche Grüsse und einen guten Start in den Tag.".format(abo_name, customer_name)
    
    frappe.sendmail( 
            recipients=[recipient],
            # ~ cc= [cc],
            subject= subject,
            message= message, 
            reference_doctype="Abo",
            reference_name=abo_name,
            sender='hb-ag@erpnext.swiss')
    
    return recipient
    
def update_abo(abo_name, reminder_to):
    print("2")
    #get Abo Doc
    abo_doc = frappe.get_doc("Abo", abo_name)
    
    #calculate next reminder date
    years = 0
    if abo_doc.interval == "Biannual":
        years = 2
    else:
        years = 1
    next_reminder = add_years(abo_doc.next_reminder, years)
    
    #update doc
    abo_doc.next_reminder = next_reminder
    abo_doc.set_reminder_manually = 0
    abo_doc.last_reminder = getdate()
    
    #add reminder row in subtable
    abo_doc.append("reminders", {
                                        'reference_doctype': "Abo Reminder",
                                        'reminder_date': getdate(),
                                        'reminder_to': reminder_to
                                    })
    
    abo_doc.save()
    frappe.db.commit()
    return

    
    
