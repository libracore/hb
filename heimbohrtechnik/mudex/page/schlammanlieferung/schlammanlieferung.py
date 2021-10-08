# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_object_details(truck, customer, object_name, key):
    if validate_credentials(truck, customer, object_name, key):
        obj = frappe.get_doc("Object", object_name)
        return {
            'address': "{0}<br>{1}<br>{2}".format(obj.object_name, obj.object_street, obj.object_location)
        }
    else:
        return {'error': 'Not allowed'}

@frappe.whitelist(allow_guest=True)
def get_truck_weight(truck):
    try:
        weight = frappe.get_value("Truck", truck, "net_weight")
        return {'weight': weight}
    except Exception as err:
        return {'error': err}

@frappe.whitelist(allow_guest=True)
def get_default_scale():
    scale = frappe.get_value("MudEx Settings", "MudEx Settings", "default_scale")
    return scale
        
def validate_credentials(truck, customer, object_name, key):
    truck = frappe.get_doc("Truck", truck)
    if truck.customer == customer:
        object_key = frappe.get_value("Object", object_name, "object_key")
        if key == object_key:
            return True
        else:
            return False
    else:
        return False
