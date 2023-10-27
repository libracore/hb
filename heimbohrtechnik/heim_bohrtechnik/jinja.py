# Copyright (c) 2021-2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

"""
Return the structured data for the pressure check QR
"""
def get_project_pressure(project):
    project_doc = frappe.get_doc("Project", project)
    object_doc = frappe.get_doc("Object", project_doc.object)
    data = {
        'project': project,
        'name': project_doc.object_name,
        'street': project_doc.object_street,
        'location': project_doc.object_location,
        'gps_coordinates': object_doc.gps_coordinates,
        'probes': []
    }
    for probe in object_doc.ews_specification:
        data['probes'].append({
            'count': probe.ews_count,
            'probe_type': probe.probe_type,
            'depth': probe.ews_depth,
            'diameter': probe.ews_diameter,
            'filling': "Thermozement" if project_doc.thermozement else "Zement, Bentonit"
            
        })
    
    #content = frappe.render_template("templates/includes/pressure_check_qr.html", data)
    content = "{0}".format(data)
    
    return content 
    
