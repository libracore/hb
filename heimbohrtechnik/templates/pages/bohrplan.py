# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import datetime
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_content, get_overlay_datas, get_subproject_overlay_datas, get_internal_overlay_datas

"""
This function checks the access and returns the restricted information
"""
@frappe.whitelist(allow_guest=True)
def get_grid(from_date, to_date, drilling_team=None, tv_mode=False):
    data = get_content(from_date[1:11], to_date[1:11], only_teams=True if not drilling_team else False)

    if drilling_team:
        dt = frappe.get_doc("Drilling Team", drilling_team).as_dict()
        data['drilling_teams'] = [{
            'crane_details': dt['crane_details'],
            'drilling_team_type': dt['drilling_team_type'],
            'drm': dt['drm'],
            'drt': dt['drt'],
            'has_crane': dt['has_crane'],
            'has_trough': dt['has_trough'],
            'phone': dt['phone'],
            'team_id': drilling_team,
            'title': drilling_team,
            'trough_details': dt['trough_details'],
            'truck_and_weight': dt['truck_and_weight']
        }]
            
    return data
    
    
@frappe.whitelist(allow_guest=True)
def get_data(key, from_date, to_date, customer=None, drilling_team=None, tv_mode=False):
    if not customer and not drilling_team and not tv_mode:
        return {'error': 'No customer or drilling team'}
    
    if customer:
        if not frappe.db.exists("Customer", customer):
            return {'error': 'Invalid customer'}
        if frappe.get_value("Customer", customer, "key") != key:
            return {'error': 'Invalid key'}
        
        data = {
            'projects': get_overlay_datas(from_date[1:11], to_date[1:11], customer),
            'internals': get_internal_overlay_datas(from_date[1:11], to_date[1:11], customer)
        }
    elif drilling_team:
        if not frappe.db.exists("Drilling Team", drilling_team):
            return {'error': 'Invalid drilling team'}
        if frappe.get_value("Drilling Team", drilling_team, "team_key") != key:
            return {'error': 'Invalid key'}
        
        data = {
            'subprojects': get_subproject_overlay_datas(from_date[1:11], to_date[1:11], drilling_team)
        }
    else:
        # TV mode
        data = {
            'projects': get_overlay_datas(from_date[1:11], to_date[1:11]),
            'internals': get_internal_overlay_datas(from_date[1:11], to_date[1:11])
        }
    
    return data

"""
Check secret
"""
@frappe.whitelist(allow_guest=True)
def verify_secret(key):
    if frappe.get_value("Heim Settings", "Heim Settings", "tv_access_secret") == key:
        return True
    else:
        return False

"""
Compute the last planned date (for visible range)
"""
@frappe.whitelist(allow_guest=True)
def get_last_date(customer=None, key=None, drilling_team=None):
    last_date = []

    if not key:
        return None
    if customer:
        if not frappe.db.exists("Customer", customer):
            return None
        if frappe.get_value("Customer", customer, "key") != key:
            return None
        
        last_date = frappe.db.sql("""
            SELECT MAX(`expected_end_date`) AS `expected_end_date`
            FROM `tabProject`
            WHERE `tabProject`.`customer` = "{customer}"
              AND `tabProject`.`status` = "Open"
              ;
        """.format(customer=customer), as_dict=True)
    else:
        if not frappe.db.exists("Drilling Team", drilling_team):
            return None
        if frappe.get_value("Drilling Team", drilling_team, "team_key") != key:
            return None
        
        last_date = frappe.db.sql("""
            SELECT MAX(`to_date`) AS `expected_end_date`
            FROM `tabSubcontracting Order`
            WHERE `tabSubcontracting Order`.`drilling_team` = "{drilling_team}"
              ;
        """.format(drilling_team=drilling_team), as_dict=True)
        
    if len(last_date) > 0:
        return last_date[0]['expected_end_date']
    else:
        return None
