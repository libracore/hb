# -*- coding: utf-8 -*-
# Copyright (c) 2021-2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint

class ConstructionSiteDescription(Document):
    def before_save(self):
        # make sure there is a trace to the project
        has_project = False
        if self.object and frappe.db.exists("Project", self.object):
            self.project = self.object
            has_project = True
        # create required fields
        if cint(self.internal_crane_required) == 1:
            check_object_checklist(self.project if has_project else self.object, "Kran intern", has_project)
        if cint(self.external_crane_required) == 1:
            check_object_checklist(self.project if has_project else self.object, "Kran", has_project)
        # public area
        if cint(self.use_public_area) == 1:
            check_object_permit(self.project if has_project else self.object, "Strassensperrung", has_project)
        # water supply address
        if cint(self.hydrant) == 1:
            check_object_address(self.object, "Wasserversorger")
            
            
        return

"""
Checks, if an is in an object/project and add it if not
"""
def check_object_address(obj, address_type):
    o_doc = frappe.get_doc("Object", obj)
    has_address = False
    for adr in o_doc.addresses:
        if adr.address_type == address_type:
            has_address = True
            break
    
    if not has_address:
        o_doc.append('addresses', {
            'address_type': address_type
        })
        o_doc.save(ignore_permissions=True)
        
    return

"""
Checks, if a checklist item is in an object/project and add it if not
"""
def check_object_checklist(obj, activity_type, has_project):
    if has_project:
        doc = frappe.get_doc("Project", obj)
    else:
        doc = frappe.get_doc("Object", obj)
    has_entry = False
    for chk in doc.checklist:
        if chk.activity == activity_type:
            has_entry = True
            break
    
    if not has_entry:
        doc.append('checklist', {
            'activity': activity_type
        })
        doc.save(ignore_permissions=True)
        
    return
    
"""
Checks, if a permit is in an object/project and add it if not
"""
def check_object_permit(obj, permit, has_project):
    if has_project:
        doc = frappe.get_doc("Project", obj)
    else:
        doc = frappe.get_doc("Object", obj)
    has_entry = False
    for pm in doc.permits:
        if pm.permit == permit:
            has_entry = True
            break
    
    if not has_entry:
        doc.append('permits', {
            'permit': permit
        })
        doc.save(ignore_permissions=True)
        
    return

"""
Checks, if a constrcution site decsription is available and returns the descriptions
"""
@frappe.whitelist()
def has_construction_site_description(object):
    docs = frappe.get_all("Construction Site Description", filters={'object': object}, fields=['name'])
    return docs
    
"""
Checks, if a constrcution site decsription exists or if not, creates one
"""
@frappe.whitelist()
def find_create_construction_site_description(object):
    docs = has_construction_site_description(object)
    if len(docs) > 0:
        return docs[0]['name']
    else:
        # create new record
        doc = frappe.get_doc({
            'doctype': 'Construction Site Description',
            'object': object
        })
        doc.insert()
        return doc.name
