# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

import frappe

INSURANCE_TITLE = "Versicherung"

def execute():
    # assure that doctype changes are loaded first
    frappe.reload_doc("heim_bohrtechnik", "doctype", "Heim Settings")
    
    if not frappe.db.exists("Checklist Activity", INSURANCE_TITLE):
        insurance = frappe.get_doc({
            'doctype': 'Checklist Activity',
            'title': INSURANCE_TITLE,
            'party_type': 'Supplier',
            'is_standard': 0,
            'prio': 100
        })
        insurance.insert()
        
    frappe.db.set_value("Heim Settings", "Heim Settings", "insurance_activity", INSURANCE_TITLE)
    
    frappe.db.commit()
    
    return
