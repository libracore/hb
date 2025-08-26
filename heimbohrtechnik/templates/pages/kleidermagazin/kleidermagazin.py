# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
from frappe.utils import cint, flt

@frappe.whitelist(allow_guest=True)
def get_employees(secret):
    if validate_credentials(secret):
        employees = frappe.db.sql("""
            SELECT `name`, `employee_name`
            FROM `tabEmployee`
            WHERE `status` = "Active"
            ORDER BY `employee_name` ASC;
            """, as_dict=True)
        return {
            'employees': employees
        }
    else:
        return {'error': 'Not allowed'}

@frappe.whitelist(allow_guest=True)
def check_pin(secret, pin):
    if validate_credentials(secret):
        user = frappe.db.sql("""
            SELECT `name`
            FROM `tabSignature`
            WHERE `pin` = %(pin)s;
            """, {'pin': pin}, as_dict=True)
        if len(user) > 0:
            return {
                'user': user[0]['name']
            }
        else:
            return {'error': 'Invalid pin'}
    else:
        return {'error': 'Not allowed'}
        
def validate_credentials(secret):
    if frappe.get_value("Einstellungen Kleidermagazin", "Einstellungen Kleidermagazin", "secret") == secret:
        return True
    else:
        return False

@frappe.whitelist(allow_guest=True)
def insert_material_issue(secret, user, items, employee, remarks=None):
    config = frappe.get_doc("Einstellungen Kleidermagazin", "Einstellungen Kleidermagazin")
    
    if type(items) == str:
        items = json.loads(items)
    
    # create new record
    material = frappe.get_doc({
        'doctype': "Stock Entry",
        'company': frappe.get_cached_value("Warehouse", config.warehouse, "company"),
        'stock_entry_type': "Material Issue",
        'employee': employee,
        'from_warehouse': config.warehouse,
        'owner': user,
        'remarks': remarks
    })
    
    for item in items:
        material.append("items", {
            'item_code': item,
            'qty': 1
        })
    
    material = material.insert(ignore_permissions=True)
    material.submit()
    return {'material': material.name}
    
