# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PermitType(Document):
    pass

@frappe.whitelist()
def get_standard_permits():
    permits = frappe.get_all("Permit Type", filters={'is_standard': 1}, fields=['name'])
    standard_permits = []
    for p in permits:
        standard_permits.append(p['name'])
    return standard_permits

@frappe.whitelist()
def get_standard_permits():
    permits = frappe.get_all("Permit Type", filters={'is_mandatory': 1}, fields=['name'])
    mandatory_permits = []
    for p in permits:
        mandatory_permits.append(p['name'])
    return mandatory_permits
