# -*- coding: utf-8 -*-
# Copyright (c) 2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Bohranzeige(Document):
    def get_autocomplete_data(self, project):
        project_doc = frappe.get_doc("Project", project)
        object_doc = frappe.get_doc("Object", project_doc.object)
        construction_site_descriptions = frappe.get_all(
            "Construction Site Description", 
            filters={'object': object_doc.name},
            fields=['name']
        )
        if len(construction_site_descriptions) > 0:
            construction_site_description = frappe.get_doc(
                "Construction Site Description", construction_site_descriptions[0]).as_dict()
        else:
            construction_site_description = None
            
        return {
            'project': project_doc.as_dict(),
            'object': object_doc.as_dict(),
            'construction_site_description': construction_site_description
        }
