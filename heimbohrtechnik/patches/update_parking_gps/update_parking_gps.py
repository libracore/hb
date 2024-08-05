import frappe
from time import sleep
import heimbohrtechnik.heimbohrtechnik.heim_bohrtechnik

def execute():
    query = """
        SELECT 
            `name`, 
            `street`, 
            `pincode`, 
            `city`, 
            `canton`,
            `gps_latitude`,
            `gps_longitude`
        FROM `tabParking`;
    """

    parkings = frappe.db.sql(query, as_dict=True)

    for parking in parkings:
        if not parking['gps_latitude'] or not parking['gps_longitude']:
            gps_coordinates = heimbohrtechnik.heimbohrtechnik.heim_bohrtechnik.locator.get_gps_coordinates(parking['street'], "{0} {1}".format(parking['pincode'], parking['city']))
        
            if gps_coordinates and gps_coordinates.get('queued') == 1:
                # wait for query to be executed (1 second)
                sleep(1)
                gps_coordinates = heimbohrtechnik.heimbohrtechnik.heim_bohrtechnik.locator.get_gps_coordinates(parking['street'], "{0} {1}".format(parking['pincode'], parking['city']))

            if not gps_coordinates:
                continue
            
            parking['gps_latitude'] = gps_coordinates['lat']
            parking['gps_longitude'] = gps_coordinates['lon']

            # update parking in database
            frappe.db.sql("""
                UPDATE `tabParking`
                SET `gps_latitude` = {lat}, `gps_longitude` = {lon}
                WHERE `name` = "{name}";
                """.format(lat=gps_coordinates['lat'], lon=gps_coordinates['lon'], name=parking['name']))
            frappe.db.commit()
    return