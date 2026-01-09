# Copyright (c) 2023-2024, libracore and Contributors
# License: GNU General Public License v3. See license.txt
#
#
# Helper functions to find closest suppliers and geolocation
#
# Find closest hotels
#  $ bench execute heimbohrtechnik.heim_bohrtechnik.locator.find_closest_hotels --kwargs "{'object_name': 'P-231234' }"
#

import frappe
import requests
from frappe.utils.background_jobs import enqueue
from frappe.utils import flt
from datetime import datetime
from frappe import _
from time import sleep
import re

@frappe.whitelist()
def find_closest_hotels(object_name):
    query = """
        SELECT 
            `name`, 
            `supplier_name`, 
            `hauptadresse`, 
            `telefon`, 
            `main_hotel`, 
            `remarks`,
            ((ABS(`gps_latitude` - {lat}) + ABS(`gps_longitude` - {lon})) / POW(5, `main_hotel`)) AS `prox`,        /* this is an approximation function by gps coordinates and a numeric factor in arbitrary units */
            `gps_latitude`, 
            `gps_longitude`
        FROM `tabSupplier`
        WHERE 
            `disabled` = 0
            AND `supplier_group` = "Hotel"
        ORDER BY `prox` ASC
        LIMIT 5;
    """
    
    template = "heimbohrtechnik/templates/pages/find_hotels.html"
    
    closest_hotels = find_closest(object_name, query, template)
    
    if closest_hotels:
        new_doc = frappe.get_doc({
            'doctype': "Find Hotel Log",
            'object': object_name,
            'hotels': closest_hotels.get('html')
        })
        
        new_doc.insert(ignore_permissions=True)
        frappe.db.commit()
    
    return closest_hotels

@frappe.whitelist()
def find_closest_parkings(object_name):
    query = """
        SELECT 
            `name`, 
            `street`, 
            `pincode`, 
            `city`, 
            `canton`,
            `gps_latitude`,
            `gps_longitude`,
            ((ABS(`tabParking`.`gps_latitude` - {lat}) + ABS(`tabParking`.`gps_longitude` - {lon}))) AS `prox`        /* this is an approximation function by gps coordinates and a numeric factor in arbitrary units */
        FROM `tabParking`
        WHERE 
            `gps_latitude` IS NOT NULL
            AND `gps_longitude` IS NOT NULL
        ORDER BY `prox` ASC
        LIMIT 5;
    """
    
    template = "heimbohrtechnik/templates/pages/find_parkings.html"
    
    return find_closest(object_name, query, template)
    
@frappe.whitelist()
def find_closest_troughs(object_name):
    trough_activity = frappe.get_value("Heim Settings", "Heim Settings", "trough_activity")
    query = """
        SELECT 
            `tabSupplier`.`name`, 
            `tabSupplier`.`supplier_name`, 
            `tabSupplier`.`hauptadresse`, 
            `tabSupplier`.`telefon`, 
            `tabSupplier`.`main_hotel`, 
            `tabSupplier Activity`.`remarks`,
            ((ABS(`tabSupplier Activity`.`gps_lat` - {lat}) + ABS(`tabSupplier Activity`.`gps_long` - {lon})) / POW(5, `tabSupplier`.`main_hotel`)) AS `prox`,        /* this is an approximation function by gps coordinates and a numeric factor in arbitrary units */
            `tabSupplier Activity`.`gps_lat` AS `gps_latitude`, 
            `tabSupplier Activity`.`gps_long` AS `gps_longitude`,
            `tabSupplier Activity`.`trough_size`,
            `tabSupplier Activity`.`place_trough_rate`,
            `tabSupplier Activity`.`disposal_rate`,
            `tabSupplier Activity`.`reach`,
            `tabSupplier Activity`.`trough_address`,
            `tabSupplier Activity`.`details`,
            `tabSupplier Activity`.`other`,
            "/*MUD*/" AS `activity_type`
        FROM `tabSupplier Activity`
        LEFT JOIN `tabSupplier` ON `tabSupplier`.`name` = `tabSupplier Activity`.`parent`
        WHERE 
            `tabSupplier Activity`.`activity` = "/*TROUGH*/"
            AND `tabSupplier`.`disabled` = 0
            AND `tabSupplier Activity`.`remarks` != "NICHT AKTIV"
        ORDER BY `prox` ASC
        LIMIT 5;
    """.replace("/*TROUGH*/", trough_activity)
    
    template = "heimbohrtechnik/templates/pages/find_supplier.html"
    
    return find_closest(object_name, query, template)
    
@frappe.whitelist()
def find_closest_mud(object_name):
    mud_activity = frappe.get_value("Heim Settings", "Heim Settings", "mud_disposer_activity")
    query = """
        SELECT 
            `tabSupplier`.`name`, 
            `tabSupplier`.`supplier_name`, 
            `tabSupplier`.`hauptadresse`, 
            `tabSupplier`.`telefon`, 
            `tabSupplier`.`main_hotel`, 
            `tabSupplier Activity`.`remarks`,
            ((ABS(`tabSupplier Activity`.`gps_lat` - {lat}) + ABS(`tabSupplier Activity`.`gps_long` - {lon})) / POW(5, `tabSupplier`.`main_hotel`)) AS `prox`,        /* this is an approximation function by gps coordinates and a numeric factor in arbitrary units */
            `tabSupplier Activity`.`gps_lat` AS `gps_latitude`, 
            `tabSupplier Activity`.`gps_long` AS `gps_longitude`,
            `tabSupplier Activity`.`trough_size`,
            `tabSupplier Activity`.`place_trough_rate`,
            `tabSupplier Activity`.`disposal_rate`,
            `tabSupplier Activity`.`reach`,
            `tabSupplier Activity`.`trough_address`,
            `tabSupplier Activity`.`details`,
            `tabSupplier Activity`.`other`,
            "/*MUD*/" AS `activity_type`
        FROM `tabSupplier Activity`
        LEFT JOIN `tabSupplier` ON `tabSupplier`.`name` = `tabSupplier Activity`.`parent`
        WHERE 
            `tabSupplier Activity`.`activity` = "/*MUD*/"
            AND `tabSupplier`.`disabled` = 0
            AND `tabSupplier Activity`.`remarks` != "NICHT AKTIV"
        ORDER BY `prox` ASC
        LIMIT 5;
    """.replace("/*MUD*/", mud_activity)
    
    template = "heimbohrtechnik/templates/pages/find_supplier.html"
    
    return find_closest(object_name, query, template)

def find_closest(object_name, query, template):
    # fetch object
    object_doc = frappe.get_doc("Object", object_name)
    # check if GPS is available
    if not object_doc.gps_lat or not object_doc.gps_long:
        # has no gps
        return None
        
    # lat/long approximation
    hotels = frappe.db.sql(query.format(lat=object_doc.gps_lat, lon=object_doc.gps_long), as_dict=True)
    
    #render hotels to dialog
    html = frappe.render_template(template, {'hotels': hotels, 'object_name': object_name})
    
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
    
@frappe.whitelist()
def find_gps_for_address(address):
    if type(address) == str:
        address = frappe.get_doc("Address", address)
        
    gps_coordinates = find_gps_coordinates(address.address_line1, "{0} {1}".format(address.pincode, address.city))
        
    return gps_coordinates

"""
This is a wrapper function that includes both local cache and OSM request delay
"""
def find_gps_coordinates(street, location):
    gps_coordinates = get_gps_coordinates(street, location)
    
    if gps_coordinates and gps_coordinates.get('queued') == 1:
        # wait for query to be executed (1 second)
        sleep(1)
        gps_coordinates = get_gps_coordinates(street, location)
        
    return gps_coordinates
    
def get_gps_coordinates(street, location):
    # if street is a gps_coordinate pair, use this
    gps_match = re.search("^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$", street)
    if gps_match:
        gps_lat_long = gps_match.group(0).split(", ")
        return {'lat': flt(gps_lat_long[0]), 'lon': flt(gps_lat_long[1])}
            
    # use local cache first
    query_string = "{0},{1}".format(street, location) if location else street
    if frappe.db.exists("OSM Cache", query_string):
        gps_data = frappe.get_doc("OSM Cache", query_string)
        if gps_data.gps_lat and gps_data.gps_long:
            return {'lat': gps_data.gps_lat, 'lon': gps_data.gps_long}
        else:
            # check if creation is older than one day and it has a 0 location, reset cache
            if type(gps_data.creation) == str:
                created = datetime.strptime(gps_data.creation[:19], "%Y-%m-%d %H:%M:%S")
            else:
                created = gps_data.creation
            if (datetime.now() - created).days > 1:
                frappe.db.sql("""
                    DELETE FROM `tabOSM Cache`
                    WHERE `name` = "{name}";
                    """.format(name=query_string))
                frappe.db.commit()
            else:
                return None
                
    # create cache record
    gps_cache = frappe.get_doc({
        'doctype': 'OSM Cache',
        'query_string': query_string,
        'gps_lat': 0,
        'gpd_long': 0
    })
    gps_cache.insert(ignore_permissions=True)
    frappe.db.commit()
    
    # if the local cache has no value, locate
    """     ISSUE: sometimes the queued process cannot update the database
    
    enqueue(
        'heimbohrtechnik.heim_bohrtechnik.locator.geolocate',
        queue='short',
        timeout=5000,
        query_string=query_string)
    """
    geolocate(query_string)
    
    return {'queued': 1}
        
def geolocate(query_string):
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    # check if OpenStreetMap was blocked
    if settings.osm_blocked:
        return None

    url = "https://nominatim.openstreetmap.org/search?q={query}&format=json&polygon=1&addressdetails=0".format(query=query_string)
    response = None
    try:
        response = requests.get(url, headers={'referer': 'libracore geolocator'})
        data = response.json()
        gps_coordinates = None
        if len(data) > 0:
            gps_coordinates = {'lat': data[0]['lat'], 'lon': data[0]['lon']}
            # write gps to cache
            gps_cache = frappe.get_doc("OSM Cache", query_string)
            gps_cache.update({
                'gps_lat': data[0]['lat'],
                'gps_long': data[0]['lon']
            })
            gps_cache.save(ignore_permissions=True)
            frappe.db.commit()
        else:
            gps_cache = frappe.get_doc("OSM Cache", query_string)
            gps_cache.add_comment("Info", _("Adresse nicht gefunden"))
            frappe.db.commit()
            
        return gps_coordinates
    except Exception as err:
        # failed to resolve address
        if response and "Access blocked" in response.text:
            settings = frappe.get_doc("Heim Settings", "Heim Settings")
            settings.osm_blocked = 1
            settings.save(ignore_permissions = True)
            frappe.db.commit()
            frappe.throw(response.message)
        else:
            frappe.log_error("{0}, {1}".format(response, err), "Geolocate failed")
        
        return None
