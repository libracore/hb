# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_object_details(truck, customer, object_name):
    if validate_credentials(truck, customer):
        obj = frappe.get_doc("Object", object_name)
        return {
            'address': "{0}<br>{1}<br>{2}".format(obj.object_name, obj.object_street, obj.object_location)
        }
    else:
        return {'error': 'Not allowed'}
    
def validate_credentials(truck, customer):
    truck = frappe.get_doc("Truck", truck)
    if truck.customer == customer:
        return True
    else:
        return False
