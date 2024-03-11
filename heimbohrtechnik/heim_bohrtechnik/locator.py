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
import requests

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
        SELECT `name`, `supplier_name`, `hauptadresse`, `telefon`, `main_hotel`, `remarks`,
        ((ABS(`gps_latitude` - {lat}) + ABS(`gps_longitude` - {lon})) / POW(5, `main_hotel`)) AS `prox`,        /* this is an approximation function by gps coordinates and a numeric factor in arbitrary units */
        `gps_latitude`, `gps_longitude`
        FROM `tabSupplier`
        WHERE `disabled` = 0
        AND `supplier_group` = "Hotel"
        ORDER BY `prox` ASC
        LIMIT 5;
    """.format(lat=object_doc.gps_lat, lon=object_doc.gps_long), as_dict=True)
    
    # refine actual distance -> TBD
    
    #render hotels to dialog
    html = frappe.render_template("heimbohrtechnik/templates/pages/find_hotels.html", {'hotels': hotels})
    
    new_doc = frappe.get_doc({
        'doctype': "Find Hotel Log",
        'object': object_name,
        'hotels': html
    })
    
    new_doc.insert()
    frappe.db.commit()
    
    return {
        'html': html,
        'hotels': hotels
    }
    
@frappe.whitelist()
def get_true_distance(from_lat, from_long, to_lat, to_long):
    host = frappe.get_doc("Heim Settings").routing_host
    link = '{h}/routing/{fla}/{flo}/{tla}/{tlo}'.format(
        h = host,
        fla = from_lat,
        flo = from_long,
        tla = to_lat,
        tlo = to_long)
    response = requests.get(link)
    return response.json()
    
