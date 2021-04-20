# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnextswiss.erpnextswiss.swisstopo import GPSConverter
from frappe import _

class Object(Document):
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
              'permit': p.permit
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
