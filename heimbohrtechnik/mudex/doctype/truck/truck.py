# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from heimbohrtechnik.heim_bohrtechnik.doctype.object.object import get_key

class Truck(Document):
    def before_save(self):
        if not self.key:
            self.set_key()
            
        return
    
    def set_key(self):
        self.key = get_key()
        return

    
