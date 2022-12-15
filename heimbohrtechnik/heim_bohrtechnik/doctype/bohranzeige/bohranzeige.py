# -*- coding: utf-8 -*-
# Copyright (c) 2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnextswiss.erpnextswiss.attach_pdf import execute
from frappe.desk.form.load import get_attachments
from frappe.utils.file_manager import remove_file

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

    def before_save(self):
        # create pdf
        if frappe.db.exists("Bohranzeige", self.name):
            self.attach_pdf()
        return
    
    def after_insert(self):
        # initial pdf
        self.attach_pdf()
        return
    
    def attach_pdf(self):
        # check if this is already attached
        attachments = get_attachments("Bohranzeige", self.name)
        for a in attachments:
            if a.file_name == "{0}.pdf".format(self.name):
                remove_file(a.name, "Bohranzeige", self.name)
        # create and attach
        execute("Bohranzeige", self.name, title=self.name, print_format=self.print_format)
        return
