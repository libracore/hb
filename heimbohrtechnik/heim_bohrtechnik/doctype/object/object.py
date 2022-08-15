# -*- coding: utf-8 -*-
# Copyright (c) 2021-2022, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnextswiss.erpnextswiss.swisstopo import GPSConverter
from frappe import _
import string, random
import requests
import json

class Object(Document):
    def before_save(self):
        if not self.object_key:
            self.set_key()
        if self.gps_coordinates and not self.gps_lat:
            self.set_gps()
            
        return
    
    def set_gps(self):
        if self.gps_coordinates:
            parts = self.gps_coordinates.split(",")
            if len(parts) == 2:
                self.gps_lat = float(parts[0].replace("'", ""))
                self.gps_long = float(parts[1].replace("'", ""))
        return
        
    def has_project(self):
        if frappe.db.exists("Project", self.name):
            return 1
        else:
            return 0
    
    def create_project(self):
        if not frappe.db.exists("Project", self.name):
            project = frappe.get_doc({
                "doctype": "Project",
                "name": self.name,
                "project_name": self.name,
                "object": self.name,
                "project_type": "External"
            })
            # add checklist and permits
            for c in self.checklist:
                project.append("checklist", {
                  'activity': c.activity,
                  'supplier': c.supplier,
                  'supplier_name': c.supplier_name  
                })
            for p in self.permits:
                project.append("permits", {
                  'permit': p.permit,
                  'file': p.file
                })
            project.insert()
            frappe.db.commit()
        return
        
    def convert_ch_to_gps(self):
        crds = None
        if self.ch_coordinates and "/" in self.ch_coordinates:
            try:
                parts = self.ch_coordinates.split("/")
                x = int(float(parts[0].replace("'", "").replace(" ", "")))
                y = int(float(parts[1].replace("'", "").replace(" ", "")))
                converter = GPSConverter()
                #lat = converter.CHtoWGSlat(x, y)
                #lng = converter.CHtoWGSlng(x, y)
                lat = converter.LV95ToWGSLatitude(x, y)
                lng = converter.LV95ToWGSLongitude(x, y)
                crds = "{0:,.5f}; {1:,.5f}".format(lat, lng).replace(",", "'").replace(";", ",")
            except Exception as err:
                frappe.msgprint( err, _("Conversion error") )
        return crds
        
    def convert_gps_to_ch(self):
        crds = None
        if self.gps_coordinates and "," in self.gps_coordinates:
            try:
                parts = self.gps_coordinates.split(",")
                lat = float(parts[0].replace(" ", ""))
                lng = float(parts[1].replace(" ", ""))
                converter = GPSConverter()
                #x = int(converter.WGStoCHx(lat, lng))
                #y = int(converter.WGStoCHy(lat, lng))
                x = int(converter.WGStoLV95North(lat, lng))
                y = int(converter.WGSToLV95East(lat, lng))
                crds = "{0:,d} / {1:,d}".format(y, x).replace(",", "'")
            except Exception as err:
                frappe.msgprint( err, _("Conversion error") )
        return crds
    
    def set_key(self):
        self.object_key = get_key()
        return
    
    def get_delivered_mud(self):
        data = frappe.db.sql("""SELECT IFNULL(SUM(`weight`), 0) AS `weight_kg`
            FROM `tabTruck Delivery Object`
            LEFT JOIN `tabTruck Delivery` ON `tabTruck Delivery`.`name` = `tabTruck Delivery Object`.`parent`
            WHERE `tabTruck Delivery`.`docstatus` = 1
              AND `tabTruck Delivery Object`.`object` = '{obj}';""".format(obj=self.name), as_dict=True)
        if len(data) > 0:
            return (data[0]['weight_kg'])
        else:
            return 0
                        
@frappe.whitelist()
def get_key():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))
    
""" 
This function will assign keys to all objects.
"""
def apply_keys():
    objects = frappe.db.sql("""SELECT `name` 
        FROM `tabObject` 
        WHERE `object_key` IS NULL OR `object_key` = "";""", as_dict=True)
    for o in objects:
        o_rec = frappe.get_doc("Object", o['name'])
        o_rec.set_key()
        o_rec.save()
        print("Updated {0}".format(o['name']))
    frappe.db.commit()
    return

"""
This function will find the GPS coordinates from OpenStreetMaps
"""
@frappe.whitelist()
def get_gps(street, location):
    url = "https://nominatim.openstreetmap.org/search?q={street},{location}&format=json&polygon=1&addressdetails=0".format(street=street, location=location)
    response = requests.get(url)
    data = response.json()
    gps_coordinates = None
    if len(data) > 0:
        gps_coordinates = "{0}, {1}".format(data[0]['lat'], data[0]['lon'])
    return gps_coordinates

"""
Helper function to get a specific address type more easily (Jinja env)
"""
def get_object_address(object, address_type):
    o = frappe.get_doc("Object", object)
    address = None
    for r in o.addresses:
        if r.address_type == address_type:
            address = r
            break
    if address and address.contact:
        address.contact_doc = frappe.get_doc("Contact", address.contact)
    if address and address.address:
        address.address_doc = frappe.get_doc("Address", address.address)
    return address

"""
Helper function to get a specific checklist item more easily (Jinja env)
"""
def get_checklist_details(checklist_item, object=None, project=None):
    if not object and not project:
        return None
    if object:
        doc = frappe.get_doc("Object", object)
    else:
        doc = frappe.get_doc("Project", project)
    checklist_details = None
    for r in doc.checklist:
        if r.activity == checklist_item:
            checklist_details = r
            break
    return checklist_details

"""
Helper function to get a specific permit item more easily (Jinja env)
"""
def get_permit_details(permit_item, object=None, project=None):
    if not object and not project:
        return None
    if object:
        doc = frappe.get_doc("Object", object)
    else:
        doc = frappe.get_doc("Project", project)
    permit_details = None
    for r in doc.permits:
        if r.permit == permit_item:
            permit_details = r
            break
    return permit_details
