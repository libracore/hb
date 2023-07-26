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
from os import path
from heimbohrtechnik.heim_bohrtechnik.nextcloud import get_physical_path
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
    
