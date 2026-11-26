# -*- coding: utf-8 -*-
# Copyright (c) 2025-2026, libracore and contributors
# License: AGPL v3. See LICENCE

import frappe
from frappe import _
from datetime import datetime
from frappe.utils import now
from hmac import compare_digest

def validate_key(project, key):
    if not frappe.db.exists("Project", project):
        return False
    obj = frappe.get_value("Project", project, "object")
    if not frappe.db.exists("Object", obj):
        return False
    if key and compare_digest(key, frappe.get_value("Object", obj, "object_key")):
        return True
    else:
        return False

@frappe.whitelist(allow_guest=True)
def fetch_project_data(project_name, key):
    if not validate_key(project_name, key):
        frappe.throw( _("Ungültige Zugangsdaten") )
        return False
    try:
        project_data = {}
        project = frappe.get_doc("Project", project_name)
        project_data["expected_start_date"] = project.expected_start_date
        project_data["expected_end_date"] = project.expected_end_date

        object_data = frappe.get_doc("Object", project.object)
        project_data["object"] = object_data.name

        address = object_data.object_street + ", " + object_data.plz + " " + object_data.city
        project_data["address"] = address

        geology_office_addresses = object_data.addresses
        for address in geology_office_addresses:
            if address.address_type == "Geologe":
                if address.address_display:
                    split_address = address.address_display.split("<br>")
                    if len(split_address) == 5:
                        address_string = split_address[1] + ", " + split_address[2] + ", " + split_address[3]
                    else:
                        address_string = split_address[1] + ", " + split_address[2]
                    project_data["geology_office"] = address_string
                    project_data["geology_office_name"] = split_address[0]
        return project_data
    except Exception as e:
        return False

@frappe.whitelist(allow_guest=True)
def get_drilling_sample(project, key):
    if not validate_key(project, key):
        return
    #get all drilling samples where status is either erfasst or bestätigt
    drilling_samples = frappe.get_all("Drilling Sample", filters={"project": project, "status": "erfasst"}, fields=["name", "status", "storage_location", "drilling_samples_all", "condition_of_drill_material__drill_bags", "custom_drilling_depth", "drilling_master", "acceptance_by", "geological_expert", "issued_by"])
    return drilling_samples

@frappe.whitelist(allow_guest=True)
def submit_drilling_sample(project, key, status, lagerort, bohrprobe_alle, 
    benutzerdefiniert_num, zustand_bohrmaterial, bohrmeister, entgegennahme_durch, geologische_fachperson, 
    ausgehaendigt_von, geologist_browser, drilling_master_browser, drilling_sample=None):
    if not validate_key(project, key):
        return False
    #if status is neu, create a new drilling sample
    if status == "neu":
        project_data = fetch_project_data(project, key)
        drilling_sample = frappe.new_doc("Drilling Sample")
        drilling_sample.project = project
        drilling_sample.object = project_data["object"]
        drilling_sample.address = project_data["address"]
        drilling_sample.geology_office = project_data.get("geology_office") or "-"
        drilling_sample.geology_office_name = project_data.get("geology_office_name") or "-"
        drilling_sample.status = "erfasst"
        drilling_sample.storage_location = lagerort
        drilling_sample.drilling_samples_all = bohrprobe_alle
        drilling_sample.custom_drilling_depth = benutzerdefiniert_num
        drilling_sample.condition_of_drill_material__drill_bags = zustand_bohrmaterial
        drilling_sample.drilling_master = bohrmeister
        drilling_sample.acceptance_by = entgegennahme_durch
        drilling_sample.geological_expert = geologische_fachperson
        drilling_sample.issued_by = ausgehaendigt_von
        drilling_sample.browserid_geologist = geologist_browser
        drilling_sample.date_drilling_master = time_without_ms(now())
        drilling_sample.browserid_drilling_master = drilling_master_browser
        drilling_sample.insert(ignore_permissions=True)
        return "Drilling Sample created successfully"
    #if status is erfasst, update the drilling sample
    elif status == "erfasst":
        drilling_sample = frappe.get_doc("Drilling Sample", {"project": project, "name": drilling_sample, "status": "erfasst"})
        drilling_sample.status = "bestätigt"
        drilling_sample.geological_expert = geologische_fachperson
        drilling_sample.issued_by = ausgehaendigt_von
        drilling_sample.date_geologist = time_without_ms(now())
        drilling_sample.browserid_geologist = geologist_browser
        drilling_sample.save(ignore_permissions=True)
        return "Drilling Sample updated successfully"
    else:
        return False
    
def time_without_ms(current_time):
    return datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
