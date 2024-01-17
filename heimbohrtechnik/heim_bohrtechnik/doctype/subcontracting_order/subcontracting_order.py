# -*- coding: utf-8 -*-
# Copyright (c) 2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SubcontractingOrder(Document):
    def before_save(self):
        if not (self.as_dict()).get('__islocal'):
            self.update_project()
        return
    
    def after_insert(self):
        self.update_project()
        
    def update_project(self):
        if self.project:
            # load referenced project
            p = frappe.get_doc("Project", self.project)
            # check if this order is already linked
            occured = False
            for s in p.subprojects:
                if s.subcontracting_order == self.name:
                    modified = False
                    occured = True
                    if s.start != self.from_date:
                        s.start = self.from_date
                        modified = True
                    if s.end != self.to_date:
                        s.end = self.to_date
                        modified = True
                    if s.description != self.order_description:
                        s.description = self.order_description
                        modified = True
                    if s.team != self.drilling_team:
                        s.team = self.drilling_team
                        modified = True
                    if modified:
                        p.save()
                        frappe.db.commit()
            # this order was not yet linked, create entry
            if not occured:
                p.append('subprojects', {
                    'start': self.from_date,
                    'end': self.to_date,
                    'description': (self.order_description or "")[:100],
                    'team': self.drilling_team,
                    'subcontracting_order': self.name
                })
                p.save()
                frappe.db.commit()
        return
    
    def get_bkps(self):
        if not self.project:
            return []
        sales_order_name = frappe.get_value("Project", self.project, 'sales_order')
        if not sales_order_name:
            return []
        
        sales_order = frappe.get_doc("Sales Order", sales_order_name)
        bkps = []
        for i in sales_order.items:
            if i.bkp not in bkps:
                bkps.append(i.bkp)
                
        return bkps
        
    def get_bkp_items(self, bkp):
        if not self.project:
            return []
        sales_order_name = frappe.get_value("Project", self.project, 'sales_order')
        if not sales_order_name:
            return []
        
        sales_order = frappe.get_doc("Sales Order", sales_order_name)
        items = []
        for i in sales_order.items:
            if i.bkp == bkp:
                items.append(i)
                
        return items
    
    def make_finish(self):
        finish = frappe.get_doc({
            'doctype': "Subcontracting Order Finish",
            'subcontracting_order': self.name,
            'project': self.project,
            'object': self.object,
            'object_name': self.object_name,
            'object_street': self.object_street,
            'object_location': self.object_location,
            'team': self.drilling_team
        })
        finish.insert()
        return finish

@frappe.whitelist()
def update_from_project(subcontracting_order, start_date, end_date, drilling_team, description):
    doc = frappe.get_doc("Subcontracting Order", subcontracting_order)
    if start_date != doc.from_date or end_date != doc.to_date:
        # update directly in the database to prevent loop
        frappe.db.sql("""
            UPDATE `tabSubcontracting Order`
            SET 
                `from_date` = "{from_date}", 
                `to_date` = "{to_date}",
                `drilling_team` = "{drilling_team}",
                `order_description` = "{description}"
            WHERE `name` = "{name}";
        """.format(name=subcontracting_order, from_date=start_date, to_date=end_date,
            description=description, drilling_team=drilling_team))
        
        frappe.db.commit()
    return
