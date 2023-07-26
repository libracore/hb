# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# For license information, please see license.txt
#
# from heimbohrtechnik.heim_bohrtechnik.email_handler import save_message

from email.message import EmailMessage
from email.policy import SMTP
from email.mime.text import MIMEText
import mimetypes
from frappe.desk.form.load import get_attachments
from os import path, remove
from heimbohrtechnik.heim_bohrtechnik.nextcloud import get_physical_path, get_path, write_project_file_from_local_file
import frappe
import html2text

# this function will take a communication and store it as a local file
#
# params: communication ID and target file path
def save_message(communication, target_file):
    doc = frappe.get_doc("Communication", communication)
    
    # create base message
    msg = EmailMessage()
    msg['Subject'] = (doc.subject or "").replace("\n", "").replace("\r", "")
    msg['From'] = doc.sender
    if doc.recipients:
        msg['To'] = doc.recipients[:-2] if doc.recipients.endswith(", ") else doc.recipients
    msg['Cc'] = doc.cc
    msg['Bcc'] = doc.bcc
    msg['Date'] = doc.communication_date
    msg.set_content(html2text.html2text(doc.content))
    msg.add_alternative(doc.content, subtype='html')
    # add attachments
    attachments = get_attachments("Communication", communication)
    for a in attachments:
        full_name = get_physical_path(a['name'])
        file_name = a['file_name']
        ctype, encoding = mimetypes.guess_type(full_name)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        try:
            with open(full_name, 'rb') as fp:
                msg.add_attachment(fp.read(), maintype=maintype, subtype=subtype, filename=file_name)
        except:
            pass    # skip file if it cannot be read
            
    # store
    with open(target_file, 'wb') as fp:
        fp.write(msg.as_bytes(policy=SMTP))
        
    return
    
def upload_communication_to_nextcloud(communication):
    # create file
    tmp_file = "/tmp/{0}.eml".format(communication)
    save_message(communication, tmp_file)
    
    # select target
    communication = frappe.get_doc("Communication", communication)
    project = None
    
    if communication.reference_doctype == "Project":
        project = communication.reference_name
        if "Bohrstart" in communication.subject:
            target = get_path('drilling')
        elif "Fertigstellung" in communication.subject:
            target = get_path('drilling')
        elif "Mulden- & Saugwagenbestellung" in communication.subject:
            target = get_path('supplier_mud')
        else:
            target = get_path('drilling')
    elif communication.reference_doctype == "Sales Invoice":
        project = frappe.get_value("Sales Invoice", communication.reference_name, "object")
        target = get_path('invoice')
    elif communication.reference_doctype == "Bohranzeige":
        project = frappe.get_value("Bohranzeige", communication.reference_name, "project")
        target = get_path('drilling')
    elif communication.reference_doctype == "Request for Public Area Use":
        project = frappe.get_value("Request for Public Area Use", communication.reference_name, "project")
        target = get_path('road')
    elif communication.reference_doctype == "Sales Order":
        project = frappe.get_value("Sales Order", communication.reference_name, "object")
        target = get_path('order')
        
    # upload to nextcloud
    if project:
        write_project_file_from_local_file(project, tmp_file, target)
    
    # clear file
    remove(tmp_file)
    
    return
