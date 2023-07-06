# Copyright (c) 2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt
#
#
# Helper functions to find closest suppliers
#
# Find closest hotels
#  $ bench execute heimbohrtechnik.heim_bohrtechnik.locator.find_closest_hotels --kwargs "{'object_name': 'P-231234' }"
#

import frappe

@frappe.whitelist()
def find_closest_hotels(object_name):
    # fetch object
    object_doc = frappe.get_doc("Object", object_name)
    # check if GPS is available
    if not object_doc.gps_lat or not object_doc.gps_long:
        # has no gps
        return None
        
    # lat/long approximation
    hotels = frappe.db.sql("""
        SELECT `name`, (ABS(`gps_latitude` - {lat}) + ABS(`gps_longitude` - {lon})) AS `prox`
        FROM `tabSupplier`
        WHERE `disabled` = 0
          AND `supplier_group` = "Hotel"
        ORDER BY `prox` ASC
        LIMIT 20;
    """.format(lat=object_doc.gps_lat, lon=object_doc.gps_long), as_dict=True)
    
    # refine actual distance
    # TBD
    
    return hotels
