# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class FeedbackDrillingMeter(Document):
    def validate(self):
        self.get_week_and_weekday()
        
    def get_week_and_weekday(self):
        date = frappe.utils.data.getdate(self.date)
        self.week = int(date.strftime('%U')) + 1
        self.day = date.strftime('%A')
