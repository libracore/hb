# Copyright (c) 2023-2024, libracore and Contributors
# License: GNU General Public License v3. See license.txt
#
#


import frappe
from frappe import _

@frappe.whitelist()
def add_parking_to_construction_site(parking, object_id):
    construction_site_name = frappe.get_value("Construction Site Description", {"object": object_id}, "name")
    parking_doc = frappe.get_doc("Parking", parking)
    
    if construction_site_name:
        construction_site = frappe.get_doc("Construction Site Description", construction_site_name)
        if construction_site.parking_links:
            for parking_link in construction_site.parking_links:
                if parking_link.parking == parking:
                    frappe.throw(("Parkplatz bereits hinzugefügt."))
                    return False
        construction_site.append("parking_links", {
            "parking": parking_doc.name
        })
        construction_site.save()
        return True
    else:
        frappe.throw(("Keine Baustellenbeschreibung für dieses Objekt gefunden."))
        return False
        
