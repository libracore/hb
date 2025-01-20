# Copyright (c) 2024-2025, libracore and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import requests
import base64
from frappe.utils.file_manager import save_file

def send_project(project, debug=False):
    settings = frappe.get_doc("HPT Settings", "HPT Settings")
    if not settings.hpt_cloud_customer or not settings.hpt_cloud_secret:
        return
        
    if isinstance(project, str):
        try:
            project_doc = frappe.get_doc("Project", project)
        except Exception as err:
            frappe.throw(err)
    else:
        project_doc = project
    
    if project_doc.project_type != "External":
        return
        
    object_doc = frappe.get_doc("Object", project_doc.object)
    
    order = {
        'name': project_doc.name,
        'date': "{0}".format(project_doc.expected_start_date),
        'object_name': object_doc.object_name,
        'object_street': object_doc.object_street,
        'object_location': object_doc.object_location,
        'gps_lat': object_doc.gps_lat,
        'gps_long': object_doc.gps_long,
        'details': []
    }
    
    if 'ews_specification' in object_doc.as_dict():
        for e in object_doc.ews_specification:
            order['details'].append({
                'ews_count': e.ews_count,
                'ews_depth': e.ews_depth,
                'ews_diameter': e.ews_diameter,
                'ews_diameter_unit': e.ews_diameter_unit,
                'ews_wall_strength': e.ews_wall_strength,
                'pressure_level': e.pressure_level,
                'probe_type': e.probe_type,
                'ews_material': e.ews_material
            })
            
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
        frappe.log_error( "Order upload failed with {0}".format(response.text), "HPT Upload failed")

    if debug:
        print(response.text)
    
    return

@frappe.whitelist(allow_guest=True)
def post_report(customer, secret, project, report, report_name):
    settings = frappe.get_doc("HPT Settings", "HPT Settings")
    if not settings.hpt_cloud_customer or not settings.hpt_cloud_secret:
        frappe.log_error( "Posting report from hptcloud to ERP failed: missing configuration", "hptcloud" )
        return {'success': False}
    if customer != settings.hpt_cloud_customer or secret != settings.hpt_cloud_secret:
        frappe.log_error( "Posting report from hptcloud to ERP failed: invalid credentials", "hptcloud" )
        return {'success': False}
    if not frappe.db.exists("Project", project):
        frappe.log_error( "Posting report from hptcloud to ERP failed: project {0} not found".format(project), "hptcloud" )
        return {'success': False}
    
    save_file(
        fname="{0}.pdf".format(report_name),
        content=base64.b64decode(report),
        dt="Project",
        dn=project,
        is_private=True
    )
    
    return {'success': True}
