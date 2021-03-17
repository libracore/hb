# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Object(Document):
    def has_project(self):
        if frappe.db.exists("Project", self.name):
            return 1
        else:
            return 0
    
    def create_project(self):
        project = frappe.get_doc({
            "doctype": "Project",
            "name": self.name,
            "project_name": self.name,
            "object": self.name
        })
        project.insert()
        return
