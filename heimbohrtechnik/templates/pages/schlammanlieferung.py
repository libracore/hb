# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import datetime
from frappe.utils import cint, flt

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

@frappe.whitelist(allow_guest=True)
def insert_delivery(truck, customer, object_name, full_weight, empty_weight, net_weight, traces, load_type, ph, key):
    if not validate_credentials(truck, customer, object_name, key):
        return {'delivery': 'Invalid Key'}
        
    # prepare values
    allocation = None
    if frappe.db.exists("Object", object_name):
        o = frappe.get_doc("Object", object_name)
        allocation = [{
            'object': object_name,
            'oject_name': o.object_name,
            'object_street': o.object_street,
            'object_location': o.object_location,
            'weight': float(net_weight)
        }]
        if not load_type:
            load_type = o.load_type
    trace = json.loads(traces)
    for t in trace:
        t['weight'] = float(t['weight'])
    truck_doc = frappe.get_doc("Truck", truck)
    config = frappe.get_doc("MudEx Settings", "MudEx Settings")
    customer_doc = frappe.get_doc("Customer", customer)
    
    # create new record
    delivery = frappe.get_doc({
        'doctype': 'Truck Delivery',
        'truck': truck,
        'truck_description': truck_doc.title,
        'truck_owner': truck_doc.truck_owner,
        'truck_scale': config.default_scale,
        'date': datetime.datetime.now(),
        'customer': customer,
        'customer_name': customer_doc.customer_name,
        'full_weight': float(full_weight),
        'empty_weight': float(empty_weight),
        'net_weight': float(net_weight),
        'load_type': load_type,
        'ph': flt(ph),
        'objects': allocation,
        'trace': trace
    })
    delivery = delivery.insert(ignore_permissions=True)
    delivery.submit()
    return {'delivery': delivery.name}
    
@frappe.whitelist(allow_guest=True)
def get_load_types(object=None):
    all_load_types = frappe.get_all("Truck Load Type", fields=['name'])
    if object:
        load_type = frappe.get_value("Object", object, 'load_type')
    else:
        load_type = None
        
    return {'types': all_load_types, 'object_load_type': load_type}

@frappe.whitelist(allow_guest=True)
def set_ph(truck_delivery, truck, customer, object_name, key):
    if not validate_credentials(truck, customer, object_name, key):
        return "Invalid Key"
        
    # prepare values
    allocation = None
    if frappe.db.exists("Truck Delivery", truck_delivery):
        ph_sensor_name = frappe.get_value("MudEx Settings", "MudEx Settings", "default_ph_sensor")
        ph_sensor = frappe.get_doc("pH Sensor", ph_sensor_name)
        ph_sensor.read_sensor()
        if frappe.db.exists("Truck Delivery", truck_delivery):
            frappe.db.sql("""
                UPDATE `tabTruck Delivery`
                SET `ph` = %(ph)s
                WHERE `name` = %(name)s;
                """,
                {'ph': ph_sensor.ph, 'name': truck_delivery}
            )
            frappe.db.commit()
            return "Stored pH = {0} to {1}".format(ph_sensor.ph, truck_delivery)
            
        else:
            return "Invalid Truck Delivery"
    
    else:
        return "Truck delivery {0} not found".format(truck_delivery)
    
