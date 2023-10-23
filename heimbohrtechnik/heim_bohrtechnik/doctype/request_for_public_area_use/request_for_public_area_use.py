# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint
from heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description import check_object_permit
from erpnextswiss.erpnextswiss.attach_pdf import execute
from frappe.desk.form.load import get_attachments
from frappe.utils.file_manager import remove_file

class RequestforPublicAreaUse(Document):        
    def before_save(self):
        # public area
        check_object_permit(self.project, frappe.get_cached_value("Heim Settings", "Heim Settings", "road_block_permit"), True)
        if self.other_projects and len(self.other_projects) > 0:
            for p in self.other_projects:
                check_object_permit(p.project, frappe.get_cached_value("Heim Settings", "Heim Settings", "road_block_permit"), True)
                
        return
        
    def after_insert(self):
        # initial pdf (later will be controlled in js)
        self.attach_pdf()
        return
    
    def attach_pdf(self):
        # check if this is already attached
        attachments = get_attachments("Request for Public Area Use", self.name)
        for a in attachments:
            if a.file_name == "{0}.pdf".format(self.name):
                remove_file(a.name, "Request for Public Area Use", self.name)
        # create and attach
        execute("Request for Public Area Use", self.name, title=self.name, print_format=self.print_format)
        frappe.db.commit()
        return
