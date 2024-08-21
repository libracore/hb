# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from heimbohrtechnik.heim_bohrtechnik.locator import find_gps_coordinates

class Parking(Document):
    def before_save(self):
        if not self.gps_latitude or not self.gps_longitude:
            self.update_gps()
        
        return
        
    def update_gps(self):
        gps_coordinates = find_gps_coordinates(self.street, "{0} {1}".format(self.pincode, self.city))
    
        if not gps_coordinates:
            return
        
        self.gps_latitude = gps_coordinates.get('lat')
        self.gps_longitude = gps_coordinates.get('lon')

        # update parking in database
        frappe.db.sql("""
            UPDATE `tabParking`
            SET `gps_latitude` = {lat}, `gps_longitude` = {lon}
            WHERE `name` = "{name}";
            """.format(lat=gps_coordinates.get('lat'), lon=gps_coordinates.get('lon'), name=self.name))
        frappe.db.commit()
        
        return
