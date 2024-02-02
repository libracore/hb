# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class LayerDirectory(Document):
    def get_autocomplete_data(self, project):
        project_doc = frappe.get_doc("Project", project)
        object_doc = frappe.get_doc("Object", project_doc.object)
        if project_doc.drilling_team:
            drilling_team = frappe.get_doc("Drilling Team", project_doc.drilling_team)
        else:
            drilling_team = None
            
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
        
        ews_details = []
        
        for ews in object_doc.ews_specification:
            ews_details.append({
                'ews_depth': ews.ews_depth,
                'ews_diameter': ews.ews_diameter,
                'probe_type': ews.probe_type
                })
        
        frappe.log_error(ews_details, "ews_details")
            
        return {
            'project': project_doc.as_dict(),
            'object': object_doc.as_dict(),
            'construction_site_description': construction_site_description,
            'drilling_team': drilling_team,
            'ews_details': ews_details
        }
