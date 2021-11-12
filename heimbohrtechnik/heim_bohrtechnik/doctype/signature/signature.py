# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Signature(Document):
    def before_save(self):
        email_footer = html = frappe.render_template("heimbohrtechnik/templates/includes/email_footer.html", self.as_dict())
        self.email_footer = email_footer
        return
