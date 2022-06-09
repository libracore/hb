# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.mapper import get_mapped_doc
from datetime import datetime, timedelta

@frappe.whitelist()
def get_standard_permits():
    permits = frappe.get_all("Permit Type", filters={'is_standard': 1}, fields=['name'])
    standard_permits = []
    for p in permits:
        standard_permits.append(p['name'])
    return standard_permits

@frappe.whitelist()
def get_mandatory_permits():
    permits = frappe.get_all("Permit Type", filters={'is_mandatory': 1}, fields=['name'])
    mandatory_permits = []
    for p in permits:
        mandatory_permits.append(p['name'])
    return mandatory_permits

@frappe.whitelist()
def get_standard_activities():
    activities = frappe.get_all("Checklist Activity", filters={'is_standard': 1}, fields=['name'])
    standard_activities = []
    for a in activities:
        standard_activities.append(a['name'])
    return standard_activities

@frappe.whitelist()
def get_object_description(object_name):
    obj = frappe.get_doc("Object", object_name)
    data = {
        'object': obj.as_dict()
    }
    html = frappe.render_template("heimbohrtechnik/templates/includes/object_description.html", data)
    return html

@frappe.whitelist()
def get_project_description(project):
    if frappe.db.exists("Project", project):
        p_doc = frappe.get_doc("Project", project)
    else:
        return get_object_description(project)
    o_doc = frappe.get_doc("Object", project)
    data = {
        'object': o_doc.as_dict(),
        'project': p_doc.as_dict()
    }
    html = frappe.render_template("heimbohrtechnik/templates/includes/project_description.html", data)
    return html

@frappe.whitelist()
def get_object_pincode_details(object):
    pincode = frappe.get_value("Object", object, 'plz')
    if pincode:
        pincodes = frappe.db.get_all("Pincode", filters={'pincode': pincode}, fields=['name'])
        if len(pincodes) > 0:
            details = frappe.get_doc("Pincode", pincodes[0]['name'])
            return {
                'plz': details.pincode, 
                'city': details.city, 
                'bohrmeterpreis': details.bohrmeterpreis,
                'arteser': details.arteser,
                'hinweise': details.hinweise
            }
        else:
            return

@frappe.whitelist()
def create_akonto(sales_order):
    akonto = get_mapped_doc("Sales Order", sales_order, 
        {
            "Sales Order": {
                "doctype": "Akonto Invoice",
                "field_map": {
                    "name": "sales_order",
                    "net_total": "no_item_net_amount"
                }
            },
            "Sales Taxes and Charges": {
                "doctype": "Sales Taxes and Charges",
                "add_if_empty": True
            },
            "Sales Order Item": {
                "doctype": "Akonto Invoice Item"
            },
            "Markup Position": {
                "doctype": "Markup Position"
            },
            "Discount Position": {
                "doctype": "Discount Position"
            }
        }
    )
    akonto.set_missing_values()
    return akonto

@frappe.whitelist()
def get_object_reference_address(object, address_type):
    entry = frappe.db.sql("""SELECT *
        FROM `tabObject Address` 
        WHERE `parent` = "{object}" 
          AND `address_type` = "{address_type}"
        ;""".format(object=object, address_type=address_type), as_dict=True)
    if len(entry) > 0:
        if entry[0]['is_simple']:
            address = "{0}<br>{1}".format(entry[0]['simple_name'], entry[0]['simple_address'])
        else:
            address = "{0}<br>".format(entry[0]['party_name'] or "")
            if entry[0]['address']:
                adr_doc= frappe.get_doc("Address", entry[0]['address'])
                address_template = frappe.db.sql("""
                    SELECT `template`
                    FROM `tabAddress Template`
                    WHERE `is_default` = 1;""", as_dict=True)[0]['template']
                address += frappe.render_template(address_template, adr_doc.as_dict())
    else:
        address = None
    return address

@frappe.whitelist()
def cancel_mudex_invoice(reference):
    open_pinvs = frappe.get_all("Purchase Invoice", filters={'bill_no': reference, 'docstatus': 1}, fields=['name'])
    if open_pinvs and len(open_pinvs) > 0:
        pinv = frappe.get_doc("Purchase Invoice", open_pinvs[0]['name'])
        pinv.cancel()
        frappe.db.commit()
        return pinv.name
    return None

@frappe.whitelist()
def get_object_geographic_environment(object_name=None, radius=0.1):
    if frappe.db.exists("Object", object_name):
        obj = frappe.get_doc("Object", object_name)
        data = {
            'object': object_name,
            'gps_lat': obj.gps_lat,
            'gps_long': obj.gps_long
        }
    else:
        data = {
            'object': "HB-AG",
            'gps_lat': 47.37767,
            'gps_long': 9.56121
        }
    
    data['environment'] = frappe.db.sql("""
        SELECT 
            `name` AS `object`, 
            `gps_lat` AS `gps_lat`, 
            `gps_long` AS `gps_long`,
            (SELECT `rate`
             FROM `tabQuotation Item`
             LEFT JOIN `tabQuotation` ON `tabQuotation`.`name` = `tabQuotation Item`.`parent`
             WHERE `tabQuotation`.`docstatus` = 1
               AND `tabQuotation`.`object` = `tabObject`.`name`
               AND `tabQuotation Item`.`item_code` = "1.01.03.01"
             ORDER By `tabQuotation`.`modified` DESC
             LIMIT 1) AS `rate`,
            (SELECT `name`
             FROM `tabSales Order`
             WHERE `tabSales Order`.`docstatus` = 1
               AND `tabSales Order`.`object` = `tabObject`.`name`
             ORDER By `tabSales Order`.`modified` DESC
             LIMIT 1) AS `sales_order`
        FROM `tabObject`
        WHERE 
            `gps_lat` >= ({gps_lat} - {lat_offset})
            AND `gps_lat` <= ({gps_lat} + {lat_offset})
            AND `gps_long` >= ({gps_long} - {long_offset})
            AND `gps_long` <= ({gps_long} + {long_offset})
            AND `name` != "{reference}";
    """.format(reference=object_name, gps_lat=data['gps_lat'], lat_offset=float(radius),
        gps_long=data['gps_long'], long_offset=(2 * float(radius))), as_dict=True)
    
    return data
    
"""
Prepare a purchase order for the probes for an object
"""
@frappe.whitelist()
def order_ews(object):
    obj = frappe.get_doc("Object", object)
    # check if there are probes defined
    if not obj.ews_specification or len(obj.ews_specification) == 0:
        return {'error': "No EWS Details", 'po': None}
    # find probe items
    items = []
    for p in obj.ews_specification:
        item = find_item_for_ews(p.ews_depth, p.ews_diameter, p.ews_wall_strength)
        if item:
            items.append({
                'item_code': item,
                'qty': p.ews_count,
                'project': object
            })
            # add injection tube
            injection_tube = frappe.get_value("Item", item, "injektionsrohr")
            if injection_tube:
                items.append({
                    'item_code': injection_tube,
                    'qty': p.ews_count,
                    'project': object
                })
    if len(items) == 0:
        return {'error': "No suitable EWS found", 'po': None}
    # schedule date: Friday before start (weekday: Monday = 0
    start_date = frappe.get_value("Project", object, "expected_start_date") or datetime.today()
    schedule_date = start_date - timedelta(days = 3 + start_date.weekday())
    # create purchase order
    po = frappe.get_doc({
        'doctype': "Purchase Order",
        'items': items,
        'schedule_date': schedule_date,
        'supplier': get_default_supplier(items[0]['item_code']),
        'object': object        
    })
    
    po.flags.ignore_mandatory = True
    po.insert(ignore_permissions=True)
    frappe.db.commit()
    return {'error': None, 'po': po.name}

# get default supplier from first item supplier (not company defaults, as not company specific)
def get_default_supplier(item):
    i = frappe.get_doc("Item", item)
    if i.supplier_items and len(i.supplier_items) > 0:
        return i.supplier_items[0].supplier
    else:
        return None

def find_item_for_ews(depth, diameter, wall_strength, material=None):
    conditions = ""
    if material:
        conditions = """AND `material` LIKE "%{material}%" """.format(material=material)
    sql_query = """SELECT
            `item_code`
        FROM `tabItem`
        WHERE 
            `diameter` = {diameter}
            AND `wall_strength` >= {wall_strength}
            AND `length` >= {depth}
            {conditions}
        ORDER BY `wall_strength` ASC, `length` ASC
        LIMIT 1;""".format(depth=depth, diameter=diameter, wall_strength=wall_strength, conditions=conditions)
        
    hits = frappe.db.sql(sql_query, as_dict=True)
    if len(hits) > 0:
        return hits[0]['item_code']
    else:
        return None
