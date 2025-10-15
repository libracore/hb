# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, get_link_to_form
from frappe import _
import json

class ConstructionSiteDescription(Document):
    def before_save(self):
        # make sure there is a trace to the project
        has_project = False
        if self.project:
            has_project = True
        elif self.object and frappe.db.exists("Project", self.object):
            # fallback to project from object
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
def has_construction_site_description(project):
    docs = frappe.db.sql("""
        SELECT `exact`.`name`
        FROM `tabConstruction Site Description` AS `exact`
        WHERE `exact`.`project` = %(project)s
        UNION SELECT `base`.`name`
        FROM `tabConstruction Site Description` AS `base`
        WHERE SUBSTRING(`base`.`project`, 1, 8) = SUBSTRING(%(project)s, 1, 8);
        """,
        {'project': project},
        as_dict=True
    )
    return [docs[0]] if docs else None
    
"""
Checks, if a constrcution site decsription exists or if not, creates one
"""
@frappe.whitelist()
def find_create_construction_site_description(project):
    docs = has_construction_site_description(project)
    if docs:
        return docs[0]['name']
    else:
        # create new record
        doc = frappe.get_doc({
            'doctype': 'Construction Site Description',
            'project': project,
            'object': frappe.get_value("Project", project, "object")
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
            `tabSubcontracting Order Item`.`remarks` AS `remarks`,
            `tabSubcontracting Order Item`.`wizard_field` AS `wizard_field`,
            `tabSubcontracting Order Item`.`wizard_description_field` AS `wizard_description_field`
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
    probe_count = 1
    long_diameter = ""
    long_meter = 1
    gly_n = ""
    gly_l = ""
    wall_box_type = ""
    mount_type = ""
    round_shaft_type = ""
    orders = []
    for item in order_items:
        if item.get('wizard_field') == "do_probing":
            probe_count = item.get('qty')
        elif (item.get('wizard_field') or "").startswith("do_long"):
            try:
                parts = item.get('description').split(" ")
                long_diameter = parts[-1]
                long_meter = item.get('qty')
            except:
                pass        # probably a content error
        elif item.get('wizard_field') == "do_fill_glycol":
            try:
                parts = item.get('description').split(" ")
                if parts[-2] == "N":
                    gly_n = parts[-1]
                else:
                    gly_l = parts[-1]
            except:
                pass        # probably a content error
        elif item.get('wizard_field') == "do_wall_box":
            try:
                parts = item.get('description').split(" ")
                wall_box_type = parts[1]
            except:
                pass        # probably a content error
        elif item.get('wizard_field') == "do_mount":
            try:
                parts = item.get('description').split(" ")
                mount_type = parts[1]
            except:
                pass        # probably a content error
        elif item.get('wizard_field') == "do_round_shaft":
            try:
                parts = item.get('description').split(" ")
                round_shaft_type = parts[1]
            except:
                pass        # probably a content error
                    
        for field in fields:
            # set additional parameters
            if field.get('fieldname') == "probe_count":
                field['default'] = probe_count
            elif field.get('fieldname') == "long_diameter":
                field['default'] = long_diameter
            elif field.get('fieldname') == "long_meter":
                field['default'] = long_meter
            elif field.get('fieldname') == "fill_ethglyn":
                field['default'] = gly_n
            elif field.get('fieldname') == "fill_ethglyl":
                field['default'] = gly_l
            elif field.get('fieldname') == "wall_box_type":
                field['default'] = wall_box_type
            elif field.get('fieldname') == "mount_type":
                field['default'] = mount_type
            elif field.get('fieldname') == "round_shaft_type":
                field['default'] = round_shaft_type
                    
            if field.get('fieldname') == item.get('wizard_description_field'):
                # update remarks
                field.update({
                    'subcontracting_order': item.get('subcontracting_order'),
                    'order_detail': item.get('order_detail'),
                    'bold': 1,
                    'default': item.get('remarks')
                })
            elif field.get('fieldname') == item.get('wizard_field'):
                # field for item found: update
                field.update({
                    'subcontracting_order': item.get('subcontracting_order'),
                    'order_detail': item.get('order_detail'),
                    'bold': 1
                })
                if field.get('fieldtype') == "Check":
                    field['default'] = 1
            elif field.get('fieldname') == 'html_head':
                if item.get("subcontracting_order") not in orders:
                    orders.append(item.get("subcontracting_order"))
                    headline = _("Aufträge: {0}").format(", ".join([
                        get_link_to_form("Subcontracting Order", o, o) for o in orders
                    ]))
                    field['options'] = headline
                    
        
        
            
    return fields

"""
Save/update wizard form to subcontracting orders
"""
@frappe.whitelist()
def save_subcontracting_wizard(project, fields, values):
    if type(fields) == str:
        fields = json.loads(fields)
    if type(values) == str:
        values = json.loads(values)
        
    subcontracting_order = None
    for field in fields:
        fieldname = field.get('fieldname')
        params = None
        # probing / Sondierung
        if fieldname == "do_probing" and values.get(fieldname):
            params = {
                'qty': values.get("probe_count"),
                'remarks': values.get("remarks_probing"),
                'description': field.get('label'),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_probing"
            }
        elif fieldname == "do_empty_tube" and values.get(fieldname):
            params = {
                'qty': values.get("probe_count"),
                'remarks': values.get("remarks_probing"),
                'description': field.get('label'),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_probing"
            }
        # open ditch / Graben öffnen
        elif fieldname == "do_open_ditch" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_open_ditch"),
                'description': field.get('label'),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_open_ditch"
            }
        # close ditch / Graben schliessen
        elif fieldname == "do_close_ditch" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_close_ditch"),
                'description': field.get('label'),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_close_ditch"
            }
        elif fieldname == "do_close_ditch_extend" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_close_ditch"),
                'description': field.get('label'),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_close_ditch"
            }
        elif fieldname == "do_close_ditch_tar" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_close_ditch"),
                'description': field.get('label'),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_close_ditch"
            }
        # core / Kernbohrung
        elif fieldname == "do_core_80" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_core"),
                'description': "Kernbohrung {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_core"
            }
        elif fieldname == "do_core_100" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_core"),
                'description': "Kernbohrung {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_core"
            }
        elif fieldname == "do_core_125" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_core"),
                'description': "Kernbohrung {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_core"
            }
        elif fieldname == "do_core_150" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_core"),
                'description': "Kernbohrung {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_core"
            }
        elif fieldname == "do_core_200" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_core"),
                'description': "Kernbohrung {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_core"
            }
        elif fieldname == "do_core_250" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_core"),
                'description': "Kernbohrung {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_core"
            }
        # pressure rings / Pressringe
        elif fieldname == "do_pring_8050" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        elif fieldname == "do_pring_10050" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        elif fieldname == "do_pring_10063" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        elif fieldname == "do_pring_10075" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        elif fieldname == "do_pring_12575" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        elif fieldname == "do_pring_150250" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        elif fieldname == "do_pring_15075" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        elif fieldname == "do_pring_15090" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_pring"),
                'description': "Pressring {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_pring"
            }
        # extension / Verlängerung
        elif fieldname == "do_long_404050H" and values.get(fieldname):
            params = {
                'qty': values.get('long_meter'),
                'remarks': values.get("remarks_long"),
                'description': "Verlängerung {0} {1}".format(field.get('label'), values.get('long_diameter')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_long"
            }
        elif fieldname == "do_long_323240H" and values.get(fieldname):
            params = {
                'qty': values.get('long_meter'),
                'remarks': values.get("remarks_long"),
                'description': "Verlängerung {0} {1}".format(field.get('label'), values.get('long_diameter')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_long"
            }
        elif fieldname == "do_long_404050V" and values.get(fieldname):
            params = {
                'qty': values.get('long_meter'),
                'remarks': values.get("remarks_long"),
                'description': "Verlängerung {0} {1}".format(field.get('label'), values.get('long_diameter')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_long"
            }
        elif fieldname == "do_long_323240V" and values.get(fieldname):
            params = {
                'qty': values.get('long_meter'),
                'remarks': values.get("remarks_long"),
                'description': "Verlängerung {0} {1}".format(field.get('label'), values.get('long_diameter')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_long"
            }
        elif fieldname == "do_long_323240V" and values.get(fieldname):
            params = {
                'qty': values.get('long_meter'),
                'remarks': values.get("remarks_long"),
                'description': "Verlängerung {0} {1}".format(field.get('label'), values.get('long_diameter')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_long"
            }
        # filling / Befüllung
        elif fieldname == "do_fill_water" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_fill"),
                'description': field.get('label'),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_fill"
            }
        elif fieldname == "do_fill_glycol" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_fill"),
                'description': "{0} {1} {2}".format(
                    field.get('label'), 
                    "Ethylenglykol N" if values.get("fill_ethglyn") else "Ethylenglykol L",
                    values.get("ethglyn") if values.get("fill_ethglyn") else values.get("fill_ethglyl")
                ),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_fill"
            }
        # wall box / Wandbox
        elif fieldname == "do_wall_box" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_wall"),
                'description': "{0} {1}".format(field.get('label'), values.get('wall_box_type')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_wall"
            }
        elif fieldname == "do_mount" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_wall"),
                'description': "{0} {1}".format(field.get('label'), values.get('mount_type')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_wall"
            }
        elif fieldname == "do_round_shaft" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_wall"),
                'description': "{0} {1}".format(field.get('label'), values.get('round_shaft_type')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_wall"
            }
        elif fieldname == "do_passable" and values.get(fieldname):
            params = {
                'qty': 1,
                'remarks': values.get("remarks_wall"),
                'description': "Rundschacht {0}".format(field.get('label')),
                'wizard_field': fieldname, 
                'wizard_description_field': "remarks_wall"
            }
            
        if params:
            subcontracting_order = update_activity(
                project=project, 
                qty=params.get('qty'), 
                description=params.get('description'), 
                subcontracting_order=field.get('subcontracting_order') or subcontracting_order,
                subcontracting_order_detail=field.get('order_detail'), 
                remarks=params.get('remarks'),
                wizard_field=params.get('wizard_field'), 
                wizard_description_field=params.get('wizard_description_field')
            )
    return
    
    
def update_activity(project, qty, description, subcontracting_order=None, \
    subcontracting_order_detail=None, remarks=None, wizard_field=None, wizard_description_field=None):
    if subcontracting_order_detail:
        # existing record, update
        frappe.db.sql("""
                UPDATE `tabSubcontracting Order Item`
                SET 
                    `qty` = %(qty)s,
                    `description` = %(description)s,
                    `remarks` = %(remarks)s,
                    `wizard_field` = %(wizard_field)s,
                    `wizard_description_field` = %(wizard_description_field)s
                WHERE `name` = %(name)s;
            """,
            {
                'qty': qty,
                'description': description,
                'remarks': remarks,
                'wizard_field': wizard_field,
                'wizard_description_field': wizard_description_field,
                'name': subcontracting_order_detail
            }
        )
        subcontracting_order = frappe.get_value("tabSubcontracting Order Item", subcontracting_order_detail, "parent")
    else:
        if subcontracting_order:
            # append to existing
            order_doc = frappe.get_doc("Subcontracting Order", subcontracting_order)
        else:
            # create new subcontracting order
            order_doc = frappe.get_doc({
                'doctype': "Subcontracting Order", 
                'project': project,
                'object': frappe.get_value("Project", project, "object"),
                'order_description': "Verlängerung"
            })
        order_doc.append("items", {
            'qty': qty,
            'description': description,
            'remarks': remarks,
            'wizard_field': wizard_field,
            'wizard_description_field': wizard_description_field
        })
        order_doc.save(ignore_permissions=True)
        subcontracting_order = order_doc.name
    frappe.db.commit()
    return subcontracting_order
    
"""
Field structure for the subcontracting wizard
"""
@frappe.whitelist()
def get_subcontracing_fields():
    fields = [
            { 'fieldtype': "HTML", 'fieldname': "html_head"},
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
