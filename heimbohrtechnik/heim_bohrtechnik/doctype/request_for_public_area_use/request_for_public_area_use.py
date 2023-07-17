# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint
from heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description import check_object_permit

class RequestforPublicAreaUse(Document):        
    def before_save(self):
        # public area
        check_object_permit(self.project, frappe.get_cached_value("Heim Settings", "Heim Settings", "road_block_permit"), True)
        if self.other_projects and len(self.other_projects) > 0:
            for p in self.other_projects:
                check_object_permit(p.project, frappe.get_cached_value("Heim Settings", "Heim Settings", "road_block_permit"), True)
                
        return
