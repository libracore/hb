# -*- coding: utf-8 -*-
# Copyright (c) 2021-2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ConstructionSiteDescription(Document):
    def before_save(self):
        if self.object and frappe.db.exists("Project", self.object):
            self.project = self.object
        return
