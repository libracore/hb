# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe

def execute():
    frappe.reload_doc("heim_bohrtechnik", "doctype", "Layer Directory")
    
    #get all Layer Directories
    layer_directories = frappe.db.sql("""
                                        SELECT
                                            `name`,
                                            `
