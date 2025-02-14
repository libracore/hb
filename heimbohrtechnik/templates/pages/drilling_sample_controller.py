# -*- coding: utf-8 -*-
# Copyright (c) 2025, libracore and contributors
# License: AGPL v3. See LICENCE

import frappe
from frappe import _
from datetime import datetime
from heimbohrtechnik.heim_bohrtechnik.doctype.drilling_sample.drilling_sample import fetch_project_data
from frappe.utils import now

@frappe.whitelist(allow_guest=True)
def get_drilling_sample(project):
    #get all drilling samples where status is either erfasst or bestätigt
    drilling_samples = frappe.get_all("Drilling Sample", filters={"project": project, "status": "erfasst"}, fields=["name", "status", "storage_location", "drilling_samples_all", "condition_of_drill_material__drill_bags", "custom_drilling_depth", "drilling_master", "acceptance_by", "geological_expert", "issued_by"])
    return drilling_samples

@frappe.whitelist(allow_guest=True)
def submit_drilling_sample(project, drilling_sample, status, lagerort, bohrprobe_alle, benutzerdefiniert_num, zustand_bohrmaterial, bohrmeister, entgegennahme_durch, geologische_fachperson, ausgehaendigt_von, geologist_browser, drilling_master_browser):
    #if status is neu, create a new drilling sample
    if status == "neu":
        project_data = fetch_project_data(project)
        drilling_sample = frappe.new_doc("Drilling Sample")
        drilling_sample.project = project
        drilling_sample.object = project_data["object"]
        drilling_sample.address = project_data["address"]
        drilling_sample.geology_office = project_data["geology_office"]
        drilling_sample.geology_office_name = project_data["geology_office_name"]
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