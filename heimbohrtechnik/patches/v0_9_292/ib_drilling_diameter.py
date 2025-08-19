# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe

def execute():
    frappe.reload_doc("heim_bohrtechnik", "doctype", "Injection report")
    
    injection_reports = frappe.db.sql("""
                                        SELECT
                                            `name`,
                                            `drilling`
                                        FROM
                                            `tabInjection report`;""", as_dict=True)
    
    for ib in injection_reports:
        if ib.get('drilling'):
            frappe.db.set_value("Injection report", ib.get('name'), "drilling_diameter", ib.get('drilling'))
