# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Injectionreport(Document):
    def get_autocomplete_data(self, project):
        project_doc = frappe.get_doc("Project", project)
        object_doc = frappe.get_doc("Object", project_doc.object)
        if project_doc.drilling_team:
            drilling_team = frappe.get_doc("Drilling Team", project_doc.drilling_team)
        else:
            drilling_team = None
            
        return {
            'project': project_doc.as_dict(),
            'object': object_doc.as_dict(),
            'drilling_team': drilling_team,
        }
