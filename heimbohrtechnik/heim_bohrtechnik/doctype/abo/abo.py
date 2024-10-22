# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_years
import json

class Abo(Document):
	pass
    
def send_abo_reminder():
    #check if reminder should be sent
    if frappe.db.get_value("Heim Settings", "Heim Settings", "send_abo_reminder"):
        
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
        
        #send Reminder and update Abo Document
        for abo in abos_with_reminder:
            recipient = send_email_reminder(abo.get('name'), abo.get('customer_name'))
            update_abo(abo.get('name'), recipient)
            
    return
        
def send_email_reminder(abo_name, customer_name):
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
    
@frappe.whitelist()
def create_invoice(doc_name):
    abo_doc = frappe.get_doc("Abo", doc_name)
    
    # ~ #create sales invoice
    sales_invoice_doc = frappe.get_doc({
                                        'doctype': "Sales Invoice",
                                        'customer' : abo_doc.get('customer'),
                                        'object_description': abo_doc.get('description'),
                                        'contact_person': abo_doc.get('contact')
                                        })
    
    #add items to sales invoice
    for item in abo_doc.items:
        sales_invoice_doc.append("items", {
                                        'reference_doctype': "Sales Invoice Item",
                                        'item_code': item.get('item_code'),
                                        'qty': item.get('qty')
                                })
    
    sales_invoice_doc.save()
    
    #update abo
    abo_doc.append("invoices", {
                        'reference_doctype': "Abo Invoice",
                        'invoice_date': getdate(),
                        'invoice': sales_invoice_doc.name,
                        'created_by': frappe.session.user
                    })
    
    abo_doc.save()
    frappe.db.commit()
    
    return sales_invoice_doc.name
    
@frappe.whitelist()
def get_email_information(contact):
    recipient = None
    e_mails = frappe.db.sql("""
                                SELECT
                                    `email_id`,
                                    `is_primary`
                                FROM
                                    `tabContact Email`
                                WHERE
                                    `parent` = '{contact}'
                                ORDER BY
                                    `is_primary` DESC""".format(contact=contact), as_dict=True)
                                    
    if len(e_mails) > 0:
        recipient = e_mails[0].get('email_id')
    
    cc = frappe.session.user
    
    return {
            'recipient' : recipient,
            'cc': cc
            }
