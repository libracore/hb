# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from tqdm import tqdm

def execute():
    try:
        # Get all objects with GPS coordinates
        objects = frappe.get_all("Object", filters={"gps_coordinates": ["is", "set"]}, fields=["name", "gps_coordinates"])
        total= len(objects)

        for obj in tqdm(objects, desc="Updating GPS", unit="object"):
            gps_coordinates = obj.gps_coordinates.split(",")
            if len(gps_coordinates) == 2:
                lat = flt(gps_coordinates[0].replace("'", ""))
                lng = flt(gps_coordinates[1].replace("'", ""))
                frappe.db.set_value("Object", obj.name, "gps_lat", lat)
                frappe.db.set_value("Object", obj.name, "gps_long", lng)
        
        # Commit the changes
        frappe.db.commit()
    except Exception as e:
        print("Unable to update GPS coordinates:", e)
    return
