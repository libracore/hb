# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe

def execute():
    try:
        loop = 1
        # Get all objects with GPS coordinates
        objects = frappe.get_all("Object", filters={"gps_coordinates": ["is", "set"]}, fields=["name", "gps_coordinates"])
        total= len(objects)

        for obj in objects:
            gps_coordinates = obj.gps_coordinates.split(",")
            if len(gps_coordinates) == 2:
                lat = float(gps_coordinates[0].replace("'", ""))
                long = float(gps_coordinates[1].replace("'", ""))
                frappe.db.set_value("Object", obj.name, "gps_lat", lat)
                frappe.db.set_value("Object", obj.name, "gps_long", long)
            print("Updating GPS coordinates: {0}/{1}".format(loop, total))
            loop += 1
        
        # Commit the changes
        frappe.db.commit()
    except Exception as e:
        print("Unable to update GPS coordinates:", e)
    return
