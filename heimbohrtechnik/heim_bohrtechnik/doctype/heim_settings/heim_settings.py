# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class HeimSettings(Document):
    pass

@frappe.whitelist()
def get_address_template():
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    address_types = []
    for at in settings.address_template:
        address_types.append({'type': at.address_type, 'dt': at.dt})
    return address_types
