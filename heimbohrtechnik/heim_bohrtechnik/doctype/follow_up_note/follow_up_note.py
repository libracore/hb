# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime

class FollowUpNote(Document):
    def before_save(self):
        self.prevdoc_docname = self.quotation
        if not self.date:
            self.date = datetime.now().date()
            
        return
        

def create_note_from_communication(communication):
    note = frappe.get_doc({
        'doctype': "Follow Up Note",
        'date': communication.communication_date,
        'notes': communication.content
    })
    note.insert()
    frappe.db.commit()
    return
