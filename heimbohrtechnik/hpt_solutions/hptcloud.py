# Copyright (c) 2024-2025, libracore and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import requests

def send_project(project):
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    if not settings.hpt_cloud_customer or not settings.hpt_cloud_secret:
        frappe.throw("HPTcloud configuration missing. Please update Heim Settings")
        
    if isinstance(project, str):
        try:
            project_doc = frappe.get_doc("Project", project)
        except Exception as err:
            frappe.throw(err)
    else:
        frappe.throw("Invalid project parameter: please provide a valid project name")
        
    object_doc = frappe.get_doc("Object", projevct_doc.object)
    
    order = {
        'name': project_doc.name,
        'date': project_doc.expected_start_date,
        'object_name': object_doc.object_name,
        'object_street': object_doc.object_street,
        'object_location': object_doc.object_location,
        'gps_lat': object_doc.gps_lat,
        'gps_long': object_doc.gps_long,
        'details': []
    }
    
    if 'ews_specification' in object_doc:
        for e in object_doc.ews_specification:
            order['details'].append(e.as_dict())
            
    parameters = {
        "customer": settings.hpt_cloud_customer,
        "secret": settings.hpt_cloud_secret,
        "order": order
    }
    
    response = requests.post(
        "https://cloud.hpt.solutions/api/method/hptcloud.hptcloud.order_api.update_order",
        json = parameters
    )
    
    if response.status_code != 200:
        frappe.log_error( "Order upload failed with {0}".format(response.text), "HPT Upload failed")
    if 'error' in response.text:
        frappe.log_error( "Order upload failed with {0}".format(response.json()['message']['error']), "HPT Upload failed")

    if debug:
        print(response.text)
    
    return
