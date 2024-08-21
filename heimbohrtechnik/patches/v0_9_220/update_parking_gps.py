# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

import frappe

def execute():
    # assure that doctype changes are loaded first
    frappe.reload_doc("heim_bohrtechnik", "doctype", "Parking")
    
    parkings = frappe.get_all("Parking")
    print("Processing {0} parkings...".format(len(parkings)))
    
    for p in parkings:
        parking = frappe.get_doc("Parking", p['name'])
        parking.update_gps()
        
    print("Done.")
    
    return
