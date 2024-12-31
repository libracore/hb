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
        
        # find amount of mud in the sales order
        sales_order_mud_amount = 0
        if project_doc.sales_order:
            sales_order = frappe.get_doc("Sales Order", project_doc.sales_order)
            mud_item = frappe.get_value("Heim Settings", "Heim Settings", "mud_item")
            for item in sales_order.items:
                if item.item_code.startswith(mud_item):
                    sales_order_mud_amount = item.qty
        
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
                'probe_type': ews.probe_type,
                'count': ews.ews_count,
                'pressure_level': ews.pressure_level
                })
            
        return {
            'project': project_doc.as_dict(),
            'object': object_doc.as_dict(),
            'construction_site_description': construction_site_description,
            'drilling_team': drilling_team,
            'ews_details': ews_details,
            'sales_order_mud_amount': sales_order_mud_amount
        }

    def before_save(self):
        # check if this is an arteser, and if so, mark object
        is_arteser = False
        if self.layers:
            for l in self.layers:
                if "Arteser" in (l.observations or ""):
                    is_arteser = True
                    break
                    
        if is_arteser and self.object:
            frappe.db.sql("""UPDATE `tabObject` SET `arteser` = 1 WHERE `name` = "{o}";""".format(o=self.object))
            frappe.db.commit()
        
        return
