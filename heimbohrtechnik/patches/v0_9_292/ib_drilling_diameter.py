# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from tqdm import tqdm

def execute():
    frappe.reload_doc("heim_bohrtechnik", "doctype", "Injection report")
    
    injection_reports = frappe.get_all("Injection report", fields=['name', 'drilling'])
    
    for ib in tqdm(injection_reports, desc="updating drilling diameter", unit="reports"):
        if ib.get('drilling'):
            frappe.db.set_value("Injection report", ib.get('name'), "drilling_diameter", ib.get('drilling'))
