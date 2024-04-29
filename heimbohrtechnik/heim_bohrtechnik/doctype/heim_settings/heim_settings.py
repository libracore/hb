# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint

class HeimSettings(Document):
    pass

@frappe.whitelist()
def get_address_template(pincode=None):
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    if pincode:
        pincode = cint(pincode)
    address_types = []
    for at in settings.address_template:
        append_activity = False
        if pincode:
            activity = frappe.get_doc("Checklist Activity", at.address_type)
            if activity.pincodes and len(activity.pincodes) > 0:
                # only insert this if it is in range
                for plz in activity.pincodes:
                    if pincode >= plz.from_pincode and pincode <= plz.to_pincode:
                        append_activity = True
                        break
            else:
                append_activity = True
        else:
            append_activity = True
            
        if append_activity:
            address_types.append({'type': at.address_type, 'dt': at.dt})
    return address_types
