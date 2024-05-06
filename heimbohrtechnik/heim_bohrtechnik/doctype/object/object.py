# -*- coding: utf-8 -*-
# Copyright (c) 2021-2023s, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnextswiss.erpnextswiss.swisstopo import GPSConverter
from frappe import _
import string, random
import json
from heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_description.construction_site_description import check_object_checklist
from frappe.utils import get_url_to_form
from heimbohrtechnik.heim_bohrtechnik.nextcloud import create_project_folder, get_cloud_url, upload_attachments
from heimbohrtechnik.heim_bohrtechnik.utils import clone_attachments
from heimbohrtechnik.heim_bohrtechnik.locator import get_gps_coordinates

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
    
    def create_project(self, sales_order=None):
        if not frappe.db.exists("Project", self.name):
            project = frappe.get_doc({
                "doctype": "Project",
                "name": self.name,
                "project_name": self.name,
                "object": self.name,
                "project_type": "External",
                "cloud_url": get_cloud_url(self.name)
            })
            # add checklist and permits
            has_int_crane = False
            has_ext_crane = False
            for c in self.checklist:
                project.append("checklist", {
                  'activity': c.activity,
                  'supplier': c.supplier,
                  'supplier_name': c.supplier_name  
                })
                if c.activity == "Kran extern":
                    has_ext_crane = True
                elif c.activity == "Kran intern":
                    has_int_crane = True
                    
            for p in self.permits:
                project.append("permits", {
                  'permit': p.permit,
                  'file': p.file
                })
            # check sales order positions to extend checklist
            so_doc = None
            if sales_order and frappe.db.exists("Sales Order", sales_order):
                so_doc = frappe.get_doc("Sales Order", sales_order)
                needs_int_crane = False
                needs_ext_crane = False
                for item in so_doc.items:
                    if item.item_code == "1.01.02.04":
                        needs_int_crane = True
                    elif item.item_name == "Kranarbeit mit Subunternehmer":
                        needs_ext_crane = True
                        
                
                if needs_int_crane and not has_int_crane:
                    project.append("checklist", {
                      'activity': "Kran intern"
                    })
                elif needs_ext_crane and not has_ext_crane:
                    project.append("checklist", {
                      'activity': "Kran extern"
                    })
                    
                    
            project.insert()
            frappe.db.commit()
            # create nextcloud folder
            create_project_folder(project.name)
            # upload attachments from sales order and quotation
            if so_doc:
                upload_attachments("Sales Order", sales_order, self.name)
                if so_doc.items[0].prevdoc_docname:
                    upload_attachments("Quotation", so_doc.items[0].prevdoc_docname, self.name)
            
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
    
    def get_ews_details(self):
        if len(self.ews_specification) == 0:
            return ""

        v = self.ews_specification[0];
        details = ""
        if self.ews_specification:
            if v.ews_diameter_unit == "Zoll":
                # for springs
                details = "{0}x {1}m {2} {3}".format((v.ews_count or "?"),
                    (v.ews_depth or "?"), (v.ews_diameter or "?"), (v.ews_diameter_unit or ""))
                if len(self.ews_specification) > 1:
                    v = self.ews_specification[1]
                    details += ", {0}x {1}m {2} {3}".format((v.ews_count or "?"),
                        (v.ews_depth or "?"), (v.ews_diameter or "?"), (v.ews_diameter_unit or ""))
            else:
                detail_list = []
                for s in self.ews_specification:
                    _details = "{0}x{1}-{2}".format((s.ews_count or "?"),
                        (s.ews_depth or "?"), (s.ews_diameter or "?"))
                    if s.pressure_level and "PN16" not in s.pressure_level:
                        _details += " {0}".format((s.pressure_level or "").split("/")[0])
                    if self.drilling_type == "Brunnen":
                        _details = "Brunnen " + _details
                    # probe highlighting
                    if "Vario" in (s.probe_type or ""):
                        _details += """ <span style="color: red;"><b>Vario</b></span>"""
                    elif "REX" in (s.probe_type or ""):
                        _details += """ <span style="color: red;"><b>REX</b></span>"""
                    elif "hipress" in (s.probe_type or ""):
                        _details += """ <span style="color: red;"><b>hipress</b></span>"""
                    elif "vertex" in (s.probe_type or ""):
                        _details += """ <span style="color: red;"><b>vertex</b></span>"""
                    elif "powerwave" in (s.probe_type or ""):
                        _details += """ <span style="color: red;"><b>powerwave</b></span>"""
                    elif "Flux" in (s.probe_type or ""):
                        _details += """ <span style="color: red;"><b>Flux</b></span>"""
                    elif "\"RT\"" in (s.probe_type or ""):
                        _details += """ <span style="color: red;"><b>RT</b></span>"""
                    
                    detail_list.append(_details)
                details = ", ".join(detail_list)
        return details
        
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
    data = get_gps_coordinates(street, location)
    gps_coordinates = None
    if data and len(data) > 0:
        if 'queued' in data:
            gps_coordinates = "queued"
        else:
            gps_coordinates = "{0}, {1}".format(data['lat'], data['lon'])
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
Helper function to get a multiple specific address type more easily (Jinja env)
"""
def get_object_addresses(object, address_type):
    o = frappe.get_doc("Object", object)
    addresses = []
    for r in o.addresses:
        if r.address_type == address_type:
            addresses.append(r.as_dict())
            if r.contact:
                addresses[-1]['contact_doc'] = frappe.get_doc("Contact", r.contact)
            if r.address:
                addresses[-1]['address_doc'] = frappe.get_doc("Address", r.address)
    return addresses
    
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

"""
Update project checklist from address
"""
@frappe.whitelist()
def update_project_checklist(obj, activity_type, supplier):
    if frappe.db.exists("Project", obj):
        check_object_checklist(obj, activity_type, has_project=True, supplier=supplier)
    return

"""
Split one object into a sub-object
"""
@frappe.whitelist()
def split_object(object_name):
    # create new object
    new_object = frappe.copy_doc(frappe.get_doc("Object", object_name), ignore_no_copy = False)
    new_object.save()
    # move to target name (=original name -revision)
    if object_name[-2:-1] == "-":
        target_name = "{0}-{1}".format(object_name[:-2],
            (int(object_name[-1:]) + 1))
    else:
        target_name = object_name + "-1"
    frappe.rename_doc("Object", new_object.name, target_name)
    
    frappe.db.commit()
    
    clone_attachments("Object", object_name, "Object", target_namee)
    
    return {'object': target_name, 'uri': get_url_to_form("Object", target_name)}
