# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnextswiss.erpnextswiss.swisstopo import GPSConverter
from frappe import _
import string, random

class Object(Document):
    def before_save(self):
        if not self.object_key:
            self.set_key()
        return
    
    def has_project(self):
        if frappe.db.exists("Project", self.name):
            return 1
        else:
            return 0
    
    def create_project(self):
        project = frappe.get_doc({
            "doctype": "Project",
            "name": self.name,
            "project_name": self.name,
            "object": self.name
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
        return
        
    def convert_ch_to_gps(self):
        crds = None
        if self.ch_coordinates and "/" in self.ch_coordinates:
            try:
                parts = self.ch_coordinates.split("/")
                x = int(parts[0].replace("'", "").replace(" ", ""))
                y = int(parts[1].replace("'", "").replace(" ", ""))
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
            return (data[0]['weight_kg'] / 1000)
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
        print("Updated {0}".format(o['name']))
    frappe.db.commit()
    return
