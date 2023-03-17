# -*- coding: utf-8 -*-
# Copyright (c) 2022-2023, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import datetime
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_content, get_overlay_datas

"""
This function checks the access and returns the restricted information
"""
@frappe.whitelist(allow_guest=True)
def get_grid(from_date, to_date):
    data = get_content(from_date[1:11], to_date[1:11], only_teams=True)

    return data
    
    
@frappe.whitelist(allow_guest=True)
def get_data(customer, key, from_date, to_date):
    if not frappe.db.exists("Customer", customer):
        return []
    if frappe.get_value("Customer", customer, "key") != key:
        return []
    
    data = get_overlay_datas(from_date[1:11], to_date[1:11], customer)
    
    return data

"""
Compute the last planned date (for visible range)
"""
@frappe.whitelist(allow_guest=True)
def get_last_date(customer, key):
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
    
    if len(last_date) > 0:
        return last_date[0]['expected_end_date']
    else:
        return None
