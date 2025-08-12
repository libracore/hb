# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe

def execute():
    frappe.reload_doc("heim_bohrtechnik", "doctype", "Layer Directory")
    frappe.reload_doc("heim_bohrtechnik", "doctype", "Layer Directory Drilling Tool")
    
    #get all Layer Directories
    layer_directories = frappe.db.sql("""
                                        SELECT
                                            `name`,
                                            `drilling_tool`,
                                            `drilling_tool_diameter`,
                                            `multiple_drilling_tools`,
                                            `drilling_tool_2`,
                                            `drilling_tool_diameter_2`,
                                            `probe_length`
                                        FROM
                                            `tabLayer Directory`
                                        WHERE
                                            `docstatus` != 2
                                        ORDER BY
                                            `modified` DESC;""", as_dict=True)
    loop = 0
    #Add Entries to child Table
    for layer_directory in layer_directories:
        if layer_directory.get('drilling_tool'):
            drilling_tool = frappe.get_doc({
                "doctype": "Layer Directory Drilling Tool",
                "parent": layer_directory.get('name'),
                "parenttype": "Layer Directory",
                "parentfield": "drilling_tools",
                "drilling_tool": layer_directory.get('drilling_tool'),
                "diameter": layer_directory.get('drilling_tool_diameter'),
                "to_depth": layer_directory.get('probe_length')
            })
            
            try:
                drilling_tool.insert()
            except Exception as Err:
                frappe.log_error("{0} - {1}".format(str(Err), layer_directory.get('name')), "Drilling Tool Patch Error")
        
        if layer_directory.get('multiple_drilling_tools') and layer_directory.get('drilling_tool_2'):
            drilling_tool_2 = frappe.get_doc({
                "doctype": "Layer Directory Drilling Tool",
                "parent": layer_directory.get('name'),
                "parenttype": "Layer Directory",
                "parentfield": "drilling_tools",
                "drilling_tool": layer_directory.get('drilling_tool_2'),
                "diameter": layer_directory.get('drilling_tool_diameter_2'),
                "to_depth": layer_directory.get('probe_length')
            })
            
            try:
                drilling_tool_2.insert()
            except Exception as Err:
                frappe.log_error("{0} - {1}".format(str(Err), layer_directory.get('name')), "Drilling Tool Patch Error")
    frappe.db.commit()
