# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024, libracore AG and contributors
# For license information, please see license.txt
#
# Note: assignments are controlled by assignment rules
#

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
from frappe.utils import cint

class DrillingRequest(Document):
    def create_object(self):
        obj = frappe.get_doc({
            'doctype': "Object",
            'object_name': self.planned_project,
            'object_location': self.object_location,
            'object_mode': self.classification,
            'object_type': self.object_type
        })
        obj.flags.ignore_validate = True
        obj.flags.ignore_mandatory = True
        obj.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.db.set_value("Drilling Request", self.name, "object", obj.name)
        return obj.name
        
    def create_quotation(self):
        qtn = frappe.get_doc({
            'doctype': "Quotation",
            'party_name': self.customer,
            'customer_name': self.customer_name,
            'title': self.customer_name,
            'object': self.object,
            'transaction_date': datetime.today(),
            'valid_till': (datetime.today() + timedelta(
                days=cint(frappe.get_cached_value("Selling Settings", "Selling Settings", "default_valid_till"))))
        })
        # add markups
        qtn.append("markup_positions", {
            'description': "LSVA",
            'percent': 3
        })
        
        qtn.flags.ignore_validate = True
        qtn.flags.ignore_mandatory = True
        qtn.insert(ignore_permissions=True)
        frappe.db.commit()
        frappe.db.set_value("Drilling Request", self.name, "quotation", qtn.name)
        if self.status == "Offen":
            frappe.db.set_value("Drilling Request", self.name, "status", "In Arbeit")
        return qtn.name

@frappe.whitelist()
def close_request(quotation):
    requests_by_quotation = frappe.get_all("Drilling Request", 
        filters={'quotation': quotation},
        fields=['name'])
    for request in requests_by_quotation:
        frappe.db.set_value("Drilling Request", request['name'], "status", "Abgeschlossen")
    return
