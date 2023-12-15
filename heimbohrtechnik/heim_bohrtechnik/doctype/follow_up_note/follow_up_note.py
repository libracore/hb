# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime
import html2text

class FollowUpNote(Document):
    def before_save(self):
        self.prevdoc_docname = self.quotation
        if not self.date:
            self.date = datetime.now().date()
            
        return
        

def create_note_from_communication(communication):
    if not communication.reference_doctype == "Quotation":
        return
        
    note = frappe.get_doc({
        'doctype': "Follow Up Note",
        'quotation': communication.reference_name,
        'prevdoc_name': communication.reference_name,
        'object': frappe.get_value("Quotation", communication.reference_name, "object"),
        'object_name': frappe.get_value("Quotation", communication.reference_name, "object_name"),
        'date': communication.communication_date,
        'notes': html2text.html2text(communication.content)
    })
    note.insert()
    frappe.db.commit()
    return
