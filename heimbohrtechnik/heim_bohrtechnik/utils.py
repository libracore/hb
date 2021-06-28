# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def get_standard_permits():
    permits = frappe.get_all("Permit Type", filters={'is_standard': 1}, fields=['name'])
    standard_permits = []
    for p in permits:
        standard_permits.append(p['name'])
    return standard_permits

@frappe.whitelist()
def get_mandatory_permits():
    permits = frappe.get_all("Permit Type", filters={'is_mandatory': 1}, fields=['name'])
    mandatory_permits = []
    for p in permits:
        mandatory_permits.append(p['name'])
    return mandatory_permits

@frappe.whitelist()
def get_standard_activities():
    activities = frappe.get_all("Checklist Activity", filters={'is_standard': 1}, fields=['name'])
    standard_activities = []
    for a in activities:
        standard_activities.append(a['name'])
    return standard_activities

@frappe.whitelist()
def get_object_description(object_name):
    obj = frappe.get_doc("Object", object_name)
    data = {
        'object': obj.as_dict()
    }
    html = frappe.render_template("heimbohrtechnik/templates/includes/object_description.html", data)
    return html
