# -*- coding: utf-8 -*-
# Copyright (c) 2021-2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class Signature(Document):
    def before_save(self):
        if not self.email_footer_template:
            frappe.throw( _("Please set an email template"), _("Validation") )
        template = frappe.get_doc("Email Footer Template", self.email_footer_template)
        email_footer = frappe.render_template(template.template, self.as_dict())
        self.email_footer = email_footer
        return

@frappe.whitelist()
def get_email_footer(template_name, user):
    template = frappe.get_doc("Email Footer Template", template_name)
    signature = frappe.get_doc("Signature", user)
    email_footer = frappe.render_template(template.template, signature.as_dict())
    return email_footer


#function set_value(doctype, docname, fieldname, value, fieldtype)