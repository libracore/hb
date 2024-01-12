# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FeedbackDrillingMeter(Document):
    def validate(self):
        self.get_weekday()
        
    def get_weekday(self):
        date = frappe.utils.data.getdate(self.date)
        self.day = date.strftime('%A')
