# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint
from erpnextswiss.erpnextswiss.attach_pdf import execute
from frappe.desk.form.load import get_attachments
from frappe.utils.file_manager import remove_file

class WaterSupplyRegistration(Document):
    def after_insert(self):
        # initial pdf (later will be controlled in js)
        self.attach_pdf()
        return
    
    def attach_pdf(self):
        # check if this is already attached
        attachments = get_attachments("Water Supply Registration", self.name)
        for a in attachments:
            if a.file_name == "{0}.pdf".format(self.name):
                remove_file(a.name, "Water Supply Registration", self.name)
        # create and attach
        execute("Water Supply Registration", self.name, title=self.name, print_format=self.print_format)
        frappe.db.commit()
        return
