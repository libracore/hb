# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint
from frappe import _

class ConstructionSiteDescription(Document):
    def before_save(self):
        # make sure there is a trace to the project
        has_project = False
        if self.object and frappe.db.exists("Project", self.object):
            self.project = self.object
            has_project = True
        # create required fields
        if cint(self.internal_crane_required) == 1:
            check_object_checklist(self.project if has_project else self.object, frappe.get_cached_value("Heim Settings", "Heim Settings", "int_crane_activity"), has_project)
        if cint(self.external_crane_required) == 1:
            check_object_checklist(self.project if has_project else self.object, frappe.get_cached_value("Heim Settings", "Heim Settings", "crane_activity"), has_project)
        if cint(self.requires_traffic_control) == 1:
            check_object_checklist(self.project if has_project else self.object, frappe.get_cached_value("Heim Settings", "Heim Settings", "traffic_control_activity"), has_project)
        # public area
        if cint(self.use_public_area) == 1:
            check_object_permit(self.project if has_project else self.object, frappe.get_cached_value("Heim Settings", "Heim Settings", "road_block_permit"), has_project)
        # water supply address
        if cint(self.hydrant) == 1:
            check_object_address(self.object, "Wasserversorger")
            
            
        return

"""
Checks, if an is in an object/project and add it if not
"""
def check_object_address(obj, address_type):
    o_doc = frappe.get_doc("Object", obj)
    has_address = False
    for adr in o_doc.addresses:
        if adr.address_type == address_type:
            has_address = True
            break
    
    if not has_address:
        o_doc.append('addresses', {
            'address_type': address_type
        })
        o_doc.save(ignore_permissions=True)
        
    return

"""
Checks, if a checklist item is in an object/project and add it if not
"""
def check_object_checklist(obj, activity_type, has_project, supplier=None):
    if has_project:
        doc = frappe.get_doc("Project", obj)
    else:
        doc = frappe.get_doc("Object", obj)
    has_entry = False
    for chk in doc.checklist:
        if chk.activity == activity_type:
            has_entry = True
            if supplier:
                chk.supplier = supplier
                chk.supplier_name = frappe.get_value("Supplier", supplier, "supplier_name")
                chk.save(ignore_permissions=True)
            break
    
    if not has_entry:
        entry = {
            'activity': activity_type
        }
        if supplier:
            entry['supplier'] = supplier
            entry['supplier_name'] = frappe.get_value("Supplier", supplier, "supplier_name")
        doc.append('checklist', entry)
        doc.save(ignore_permissions=True)
        
    return
    
"""
Checks, if a permit is in an object/project and add it if not
"""
def check_object_permit(obj, permit, has_project):
    if has_project:
        doc = frappe.get_doc("Project", obj)
    else:
        doc = frappe.get_doc("Object", obj)
    has_entry = False
    for pm in doc.permits:
        if pm.permit == permit:
            has_entry = True
            break
    
    if not has_entry:
        doc.append('permits', {
            'permit': permit
        })
        doc.save(ignore_permissions=True)
        
    return

"""
Checks, if a constrcution site decsription is available and returns the descriptions
"""
@frappe.whitelist()
def has_construction_site_description(object):
    docs = frappe.get_all("Construction Site Description", filters={'object': object}, fields=['name'])
    return docs
    
"""
Checks, if a constrcution site decsription exists or if not, creates one
"""
@frappe.whitelist()
def find_create_construction_site_description(object):
    docs = has_construction_site_description(object)
    if len(docs) > 0:
        return docs[0]['name']
    else:
        # create new record
        doc = frappe.get_doc({
            'doctype': 'Construction Site Description',
            'object': object
        })
        doc.insert()
        return doc.name

"""
Build the subcontracting order map
"""
@frappe.whitelist()
def get_subcontracting_order_map(project):
    order_items = frappe.db.sql("""
        SELECT
            `tabSubcontracting Order`.`name` AS `subcontracting_order`,
            `tabSubcontracting Order Item`.`name` AS `order_detail`,
            `tabSubcontracting Order Item`.`qty` AS `qty`,
            `tabSubcontracting Order Item`.`description` AS `description`,
            `tabSubcontracting Order Item`.`remarks` AS `remarks`
        FROM `tabSubcontracting Order Item`
        LEFT JOIN `tabSubcontracting Order` ON `tabSubcontracting Order`.`name` = `tabSubcontracting Order Item`.`parent`
        WHERE `tabSubcontracting Order`.`project` = %(project)s;
        """,
        {'project': project},
        as_dict=True
    )
    
    # fetch fields
    fields = get_subcontracing_fields()
    
    # apply values
    for item in order_items:
        for field in fields:
            if field.get('label') == item.get('description'):
                field.update({
                    'subcontracting_order': item.get('subcontracting_order'),
                    'order_detail': item.get('order_detail'),
                    'bold': 1
                })
                if field.get('fieldtype') == "Check":
                    field['default'] = 1
                
                break   # field found - skip to next item
                
    return fields
    
"""
Field structure for the subcontracting wizard
"""
@frappe.whitelist()
def get_subcontracing_fields():
    fields = [
            # Bohrpunkt Sondieren
            { 'fieldtype': "Section Break", 'fieldname': "sec_probing", 'label': _("Bohrpunkt Sondieren") },
            { 'fieldtype': "Data", 'fieldname': "remarks_probing", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_probing_1" },
            { 'fieldtype': "Check", 'fieldname': "do_probing", 'label': _("Bohrpunkt Sondieren") },
            { 'fieldtype': "Check", 'fieldname': "do_empty_tube", 'label': _("mit Leerrohr einbauen d300mm Rohr") },
            { 'fieldtype': "Column Break", 'fieldname': "col_probing_2" },
            { 'fieldtype': "Int", 'fieldname': "probe_count", 'label': _("Anzahl Sonden"), 'default': 1 },
            # Graben öffnen
            { 'fieldtype': "Section Break", 'fieldname': "sec_open_ditch", 'label': _("Graben öffnen") },
            { 'fieldtype': "Data", 'fieldname': "remarks_open_ditch", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_open_ditch_1" },
            { 'fieldtype': "Check", 'fieldname': "do_open_ditch", 'label': _("Graben öffnen und einsanden") },
            { 'fieldtype': "Column Break", 'fieldname': "col_open_ditch_2"},
            # Graben schliessen
            { 'fieldtype': "Section Break", 'fieldname': "sec_close_ditch", 'label': _("Graben schliessen") },
            { 'fieldtype': "Data", 'fieldname': "remarks_close_ditch", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_close_ditch_1" },
            { 'fieldtype': "Check", 'fieldname': "do_close_ditch", 'label': _("Graben schliessen, Grobplanie") },
            { 'fieldtype': "Check", 'fieldname': "do_close_ditch_extend", 'label': _("Graben schliessen und Verbundsteine setzen") },
            { 'fieldtype': "Check", 'fieldname': "do_close_ditch_tar", 'label': _("Graben schliessen und Teerbelag erstellen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_close_ditch_2" },
            # Kernbohrung
            { 'fieldtype': "Section Break", 'fieldname': "sec_core", 'label': _("Kernbohrung") },
            { 'fieldtype': "Data", 'fieldname': "remarks_core", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_core_1" },
            { 'fieldtype': "Check", 'fieldname': "do_core_80", 'label': _("Ø 80mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_100", 'label': _("Ø 100mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_125", 'label': _("Ø 125mm") },
            { 'fieldtype': "Column Break", 'fieldname': "col_core_2" },
            { 'fieldtype': "Check", 'fieldname': "do_core_150", 'label': _("Ø 150mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_200", 'label': _("Ø 200mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_250", 'label': _("Ø 250mm") },
            # Pressringe
            { 'fieldtype': "Section Break", 'fieldname': "sec_core", 'label': _("Pressringe") },
            { 'fieldtype': "Data", 'fieldname': "remarks_pring", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_pring_1" },
            { 'fieldtype': "Check", 'fieldname': "do_pring_8050", 'label': _("Ø 80/50mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_10050", 'label': _("Ø 100/50mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_10063", 'label': _("Ø 100/63mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_10075", 'label': _("Ø 100/75mm") },
            { 'fieldtype': "Column Break", 'fieldname': "col_pring_2" },
            { 'fieldtype': "Check", 'fieldname': "do_pring_12575", 'label': _("Ø 125/75mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_150250", 'label': _("Ø 150/2x50mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_15075", 'label': _("Ø 150/75mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_15090", 'label': _("Ø 150/90mm") },
            # Verlängerung
            { 'fieldtype': "Section Break", 'fieldname': "sec_long", 'label': _("Verlängerung") },
            { 'fieldtype': "Data", 'fieldname': "remarks_long", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_long_1" },
            { 'fieldtype': "Check", 'fieldname': "do_long_404050H", 'label': _("40/40/50 Verlängern bis Hauseintritt") },
            { 'fieldtype': "Check", 'fieldname': "do_long_323240H", 'label': _("32/32/40 Verlängern bis Hauseintritt") },
            { 'fieldtype': "Check", 'fieldname': "do_long_404050V", 'label': _("40/40/50 Verlängern bis Verteiler/Sammler im Haus") },
            { 'fieldtype': "Check", 'fieldname': "do_long_323240V", 'label': _("32/32/40 Verlängern bis Verteiler/Sammler im Haus") },
            { 'fieldtype': "Column Break", 'fieldname': "col_long_2" },
            { 'fieldtype': "Select", 'fieldname': "long_diameter", 'options': "\nd50mm\nd63mm\nd75mm\nd90mm\nd110mm\nd140mm\nd160mm\nd180mm\nd200mm\nd220mm\nd250mm", 'label': _("Hauptleitung bis Eintritt oder Zwischenraum verlegen") },
            { 'fieldtype': "Int", 'fieldname': "long_meter", 'label': _("Laufmeter"), 'default': 1 },
            # Anlage befüllen
            { 'fieldtype': "Section Break", 'fieldname': "sec_fill", 'label': _("Anlage befüllen") },
            { 'fieldtype': "Data", 'fieldname': "remarks_fill", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_fill_1" },
            { 'fieldtype': "Check", 'fieldname': "do_fill_water", 'label': _("Anlage mit Wasser befüllen") },
            { 'fieldtype': "Check", 'fieldname': "do_fill_glycol", 'label': _("Anlage mit Glykol befüllen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_fill_2" },
            { 'fieldtype': "Select", 'fieldname': "fill_ethglyn", 'options': "\n20%\n25%\n30%", 'label': _("Ethylenglykol N (Konzentrat)") },
            { 'fieldtype': "Select", 'fieldname': "fill_ethglyl", 'options': "\n20%\n25%\n30%", 'label': _("Ethylenglykol L (Konzentrat)") },
            # Wandbox / Rundschacht
            { 'fieldtype': "Section Break", 'fieldname': "sec_wall", 'label': _("Wandbox / Rundschacht") },
            { 'fieldtype': "Data", 'fieldname': "remarks_wall", 'label': _("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_wall_1" },
            { 'fieldtype': "Check", 'fieldname': "do_wall_box", 'label': _("Wandbox") },
            { 'fieldtype': "Select", 'fieldname': "wall_box_type", 'options': "\n2-Fach\n3-Fach\n4-Fach\n5-Fach", 'label': _("Wandboxart") },
            { 'fieldtype': "Check", 'fieldname': "do_mount", 'label': _("Montageblock") },
            { 'fieldtype': "Select", 'fieldname': "mount_type", 'options': "\n2-Fach\n3-Fach\n4-Fach\n5-Fach", 'label': _("Montageblockart") },
            { 'fieldtype': "Column Break", 'fieldname': "col_wall_2" },
            { 'fieldtype': "Check", 'fieldname': "do_round_shaft", 'label': _("Rundschacht") },
            { 'fieldtype': "Select", 'fieldname': "round_shaft_type", 'options': "\n2-Fach\n3-Fach\n4-Fach\n5-Fach", 'label': _("Rundschachtart") },
            { 'fieldtype': "Check", 'fieldname': "do_passable", 'label': _("Befahrbar") }
        ]
    return fields
