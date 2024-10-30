# Copyright (c) 2021-2024, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from datetime import datetime, timedelta
import json
import re
import uuid
from PyPDF2 import PdfFileMerger
from frappe.utils import cint, flt, get_bench_path, get_files_path
from frappe.utils.file_manager import save_file
from erpnextswiss.erpnextswiss.utils import get_numeric_part
from erpnextswiss.erpnextswiss.attach_pdf import execute, create_folder
from frappe.desk.form.load import get_attachments
from frappe.utils.file_manager import remove_file
from frappe.core.doctype.communication.email import make as make_email
from heimbohrtechnik.heim_bohrtechnik.nextcloud import write_project_file_from_local_file
from heimbohrtechnik.heim_bohrtechnik.timeshepherd import create_project
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
from heimbohrtechnik.heim_bohrtechnik.date_controller import move_project, get_duration_days
from heimbohrtechnik.heim_bohrtechnik.locator import get_gps_coordinates

@frappe.whitelist()
def get_standard_permits(pincode=None):
    permits = frappe.get_all("Permit Type", filters={'is_standard': 1}, fields=['name'])
    standard_permits = []
    if pincode:
        pincode = int(pincode)
    for p in permits:
        permit = frappe.get_doc("Permit Type", p['name'])
        if pincode and permit.pincodes and len(permit.pincodes) > 0:
            # only insert this if it is in range
            for plz in permit.pincodes:
                if pincode >= plz.from_pincode and pincode <= plz.to_pincode:
                    standard_permits.append(p['name'])
                    break
        else:
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
def get_standard_activities(pincode=None):
    activities = frappe.get_all("Checklist Activity", filters={'is_standard': 1}, fields=['name'], order_by='prio')
    standard_activities = []
    if pincode:
        pincode = cint(pincode)
    for a in activities:
        append_activity = False
        if pincode:
            activity = frappe.get_doc("Checklist Activity", a['name'])
            if activity.pincodes and len(activity.pincodes) > 0:
                # only insert this if it is in range
                for plz in activity.pincodes:
                    if pincode >= plz.from_pincode and pincode <= plz.to_pincode:
                        append_activity = True
                        break
            else:
                append_activity = True
        else:
            append_activity = True
            
        if append_activity:
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
                "doctype": "Sales Invoice",
                "field_map": {
                    "name": "sales_order",
                    "net_total": "no_item_net_amount"
                }
            },
            "Sales Taxes and Charges": {
                "doctype": "Sales Taxes and Charges",
                "add_if_empty": True
            }
        }
    )
    akonto.append('items', {
        'item_code': frappe.get_value("Heim Settings", "Heim Settings", "akonto_item"),
        'qty': 1,
        'rate': 10000,
        'sales_order': sales_order
    })
    akonto.title = "Akonto-Rechnung"
    akonto.set_missing_values()
    return akonto

@frappe.whitelist()
def create_part_invoice(sales_order):
    sinv = make_sales_invoice(sales_order)
    sinv.title = "Teilrechnung"
    return sinv
    
@frappe.whitelist()
def create_final_invoice(sales_order):
    sinv = make_sales_invoice(sales_order)
    sinv.title = "Schlussrechnung"
    return sinv
    
"""
This function find applicable akonto invoices
"""
@frappe.whitelist()
def get_available_akonto(sales_order=None):
    if not sales_order:
        return []
    from heimbohrtechnik.heim_bohrtechnik.report.offene_akonto_rechnungen.offene_akonto_rechnungen import get_data
    akonto = get_data({'sales_order': sales_order})
    return akonto

"""
This function will transfer the previous akonto amount to the revenue
"""
@frappe.whitelist()
def book_akonto(sales_invoice, net_amount):
    sinv = frappe.get_doc("Sales Invoice", sales_invoice)
    akonto_item = frappe.get_doc("Item", frappe.get_value("Heim Settings", "Heim Settings", "akonto_item"))
    akonto_account = None
    for d in akonto_item.item_defaults:
        if d.company == sinv.company:
            akonto_account = d.income_account
    if not akonto_account:
        frappe.throw("Please define an income account for the Akonto Item")

    revenue_account = frappe.get_value("Company", sinv.company, "default_income_account")
    if not revenue_account:
        frappe.throw("Please define a default revenue account for {0}".format(sinv.company))
        
    jv = frappe.get_doc({
        'doctype': 'Journal Entry',
        'posting_date': sinv.posting_date,
        'company': sinv.company,
        'accounts': [
            {
                'account': akonto_account,
                'debit_in_account_currency': net_amount
            },{
                'account': revenue_account,
                'credit_in_account_currency': net_amount
            }
        ],
        'user_remark': "Akonto from {0}".format(sales_invoice)
    })
    jv.insert(ignore_permissions=True)
    jv.submit()
    frappe.db.commit()
    return jv.name

@frappe.whitelist()
def cancel_akonto(sales_invoice):
    company = frappe.get_value("Sales Invoice", sales_invoice, "company")
    jvs = frappe.get_all("Journal Entry", 
        filters={'company': company, 'docstatus': 1, 'user_remark': "Akonto from {0}".format(sales_invoice)},
        fields=['name']
    )
    
    cancelled = []
    for jv in jvs:
        doc = frappe.get_doc("Journal Entry", jv['name'])
        doc.cancel()
        cancelled.append(jv['name'])
        
    frappe.db.commit()
    return cancelled
    
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
    from heimbohrtechnik.heim_bohrtechnik.invoicing import cancel_related_pinv
    cancel_related_pinv(reference)
    return None

@frappe.whitelist()
def get_object_geographic_environment(object_name=None, radius=0.1, address=None, quotations=False, only_projects=False, \
    hide_object=False, hide_quotation=False, hide_order=False, hide_completed=False):
    data = None
    if address:
        # find gps from address
        gps = get_gps_coordinates(address, None)
        if gps:
            data = {
                'object': address,
                'gps_lat': gps['lat'],
                'gps_long': gps['lon']
            }
    elif frappe.db.exists("Object", object_name):
        obj = frappe.get_doc("Object", object_name)
        data = {
            'object': object_name,
            'gps_lat': obj.gps_lat,
            'gps_long': obj.gps_long
        }
    
    # default of no center is defined
    if not data:
        data = {
            'object': "HB-AG",
            'gps_lat': 47.37767,
            'gps_long': 9.56121
        }
    
    qtn_column = ""
    if cint(quotations):
        qtn_column = """,
            (SELECT `tabQuotation`.`name`
             FROM `tabQuotation`
             WHERE `tabQuotation`.`object` = `tabObject`.`name`
               AND `docstatus` = 1 
             ORDER BY `tabQuotation`.`modified` DESC
             LIMIT 1) AS `quotation`"""
    projects_filter = ""
    if cint(only_projects):
        projects_filter += " AND `tabProject`.`name` IS NOT NULL "
    #if cint(hide_object):
    #    projects_filter += " AND `tabObject`.`qtn_meter_rate` IS NOT NULL "
    #if cint(hide_quotation): 
    #    projects_filter += " AND `tabProject`.`sales_order` IS NOT NULL "
    #if cint(hide_order): 
    #    projects_filter += " AND (`tabProject`.`sales_order` IS NULL OR `completed` = 1) "
    #if cint(hide_completed):
    #    projects_filter += " AND (`tabProject`.`expected_end_date` > CURDATE() OR `tabProject`.`expected_end_date` IS NULL) "
    data['environment'] = frappe.db.sql("""
        SELECT 
            `tabObject`.`name` AS `object`, 
            `tabObject`.`gps_lat` AS `gps_lat`, 
            `tabObject`.`gps_long` AS `gps_long`,
            `tabObject`.`qtn_meter_rate` AS `rate`,
            `tabObject`.`drilling_method` AS `drilling_method`,
            `tabObject`.`arteser` AS `arteser`,
            `tabProject`.`sales_order` AS `sales_order`,
            `tabProject`.`expected_start_date` AS `start_date`,
            `tabProject`.`expected_end_date` AS `end_date`,
            IF (`tabProject`.`expected_start_date` <= CURDATE() AND `tabProject`.`expected_end_date` >= CURDATE(), 1, 0) AS `active`,
            IF (`tabProject`.`expected_end_date` < CURDATE(), 1, 0) AS `completed`,
            `tabProject`.`cloud_url` AS `cloud_url`,
            `tabLayer Directory`.`name` AS `sv`,
            `tabLayer Directory`.`to_depth` AS `to_depth`
            {quotations}
        FROM `tabObject`
        LEFT JOIN `tabProject` ON `tabProject`.`object` = `tabObject`.`name`
        LEFT JOIN `tabLayer Directory` ON (
            `tabLayer Directory`.`object` = `tabObject`.`name`
            AND `tabLayer Directory`.`docstatus` < 2)
        WHERE 
            `tabObject`.`gps_lat` >= ({gps_lat} - {lat_offset})
            AND `tabObject`.`gps_lat` <= ({gps_lat} + {lat_offset})
            AND `tabObject`.`gps_long` >= ({gps_long} - {long_offset})
            AND `tabObject`.`gps_long` <= ({gps_long} + {long_offset})
            AND `tabObject`.`name` != "{reference}"
            {projects_filter}
        GROUP BY `tabObject`.`name`;
    """.format(reference=object_name, gps_lat=data['gps_lat'], lat_offset=float(radius),
        gps_long=data['gps_long'], long_offset=(2 * float(radius)),
        quotations=qtn_column, projects_filter=projects_filter), as_dict=True)
    
    # apply hide filters
    if cint(hide_object) or cint(hide_quotation) or cint(hide_order) or cint(hide_completed):
        filtered_data = []
        for d in data['environment']:
            if cint(hide_object) and flt(d['rate']) == 0 and not d['sales_order']:
                # hide_object selected and has no rate nor sales order
                continue
            if cint(hide_quotation) and flt(d['rate']) != 0 and not d['sales_order']:
                # hide_quotation selected and this has a quotation but no sales order
                continue
            if cint(hide_order) and not cint(d['completed']) and d['sales_order']:
                # hide_order selected and not completed but has an order
                continue
            if cint(hide_completed) and cint(d['completed']):
                # hide_completed selected and completed
                continue
            # no condition applied: use this
            filtered_data.append(d)
            
        data['environment'] = filtered_data

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
        item = find_item_for_ews(p.ews_depth, p.ews_diameter, p.ews_wall_strength, material=p.ews_material, probe_type=p.probe_type)
        if item:
            items.append({
                'item_code': item,
                'qty': p.ews_count,
                'project': object
            })
            # add realetd items
            related_items = get_related_items(item)
            for r in related_items:
                items.append({
                    'item_code': r.get('item_code'),
                    'qty': p.ews_count * (r.get('qty') or 1),
                    'project': object
                })
                # recursion: in case of staged cementation, check sub-level also
                if cint(obj.staged_cementation) == 1:
                    sub_related_items = get_related_items(r.get('item_code'))
                    for sr in sub_related_items:
                        items.append({
                            'item_code': sr.get('item_code'),
                            'qty': p.ews_count * (sr.get('qty') or 1),
                            'project': object
                        })
                    
    if len(items) == 0:
        return {'error': "No suitable EWS found", 'po': None}
    # schedule date: Thursday before start (weekday: Monday = 0
    start_date = frappe.get_value("Project", object, "expected_start_date") or datetime.today()
    schedule_date = start_date - timedelta(days = 4 + start_date.weekday())
    if schedule_date < datetime.today().date():
        schedule_date = datetime.today()
    supplier = get_default_supplier(items[0]['item_code'])
    currency = frappe.get_value("Supplier", supplier, "default_currency") or frappe.defaults.get_global_default("currency")
    # create purchase order
    po = frappe.get_doc({
        'doctype': "Purchase Order",
        'items': items,
        'schedule_date': schedule_date,
        'supplier': supplier,
        'object': object,
        'currency': currency
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

def find_item_for_ews(depth, diameter, wall_strength, material=None, probe_type=None):
    conditions = ""
    if material:
        conditions += """AND (`tabItem`.`raw_material` = "{material}" OR `tabItem`.`raw_material` IS NULL) """.format(material=material)
    if probe_type:
        conditions += """AND (`tabItem`.`probe_type` = "{probe_type}" OR `tabItem`.`probe_type` IS NULL) """.format(probe_type=probe_type)
    
    sql_query = """SELECT
            `tabItem`.`item_code`
        FROM `tabItem`
        LEFT JOIN `tabItem Default` ON `tabItem Default`.`parent` = `tabItem`.`name` AND `tabItem Default`.`parenttype` = "Item"
        WHERE 
            `tabItem`.`diameter` = {diameter}
            AND `tabItem`.`wall_strength` >= {wall_strength}
            AND `tabItem`.`length` >= {depth}
            {conditions}
        ORDER BY 
            `tabItem`.`probe_type` DESC,        /* first find suitable probe type */
            `tabItem`.`raw_material` DESC,      /* ..or suitable material */
            `tabItem`.`wall_strength` ASC,      /* closest wall strength */
            `tabItem`.`length` ASC,             /* then the shortest possible length */
            `tabItem Default`.`default_supplier` ASC        /* and ideally from the preferred supplier (lowest supplier ID) */
        LIMIT 1;""".format(depth=depth, diameter=diameter, wall_strength=wall_strength, conditions=conditions)
    
    hits = frappe.db.sql(sql_query, as_dict=True)
    if len(hits) > 0:
        return hits[0]['item_code']
    else:
        return None

@frappe.whitelist()
def mutate_prices(selected, discount, markup):
    if type(selected) == str:
        selected = json.loads(selected)
    
    for s in selected:
        price = frappe.get_doc("Item Price", s['name'])
        if price.base_rate:
            price.discount = float(discount)
            price.cost_markup = float(markup)
            
            rate = ((price.base_rate * (((price.discount or 0) + 100) / 100)) \
                    * (((price.cost_markup or 0) + 100) / 100))                 \
                    * (((price.skonto_discount or 0) + 100) / 100)
            price.price_list_rate = rate
            price.save()
            
    frappe.db.commit()
    return
    
"""
Create separate invoice from sales order
"""
@frappe.whitelist()
def create_empty_invoice_from_order(sales_order, target_doc=None):
    def postprocess(source, target):
        set_missing_values(source, target)

    def set_missing_values(source, target):
        target.is_pos = 0
        target.run_method("set_missing_values")

        
    invoice = get_mapped_doc("Sales Order", sales_order, {
        "Sales Order": {
            "doctype": "Sales Invoice",
            "field_map": {
                "name": "sales_order",
                "net_total": "no_item_net_amount"
            }
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        }
    }, target_doc, postprocess)
    return invoice

"""
Create a project if required from sales order
"""
@frappe.whitelist()
def check_create_project(sales_order):
    if type(sales_order) == str:
        if frappe.db.exists("Sales Order", sales_order):
            sales_order = frappe.get_doc("Sales Order", sales_order).as_dict()
        else:
            sales_order = json.loads(sales_order)
    if 'object' in sales_order and sales_order['object']:
        if not frappe.db.exists("Project", sales_order['object']):
            o = frappe.get_doc("Object", sales_order['object'])
            o.create_project(sales_order.get('name'))
        # reference customer and sales order
        p = frappe.get_doc("Project", sales_order['object'])
        p.customer = sales_order['customer']
        if frappe.db.exists("Sales Order", sales_order['name']) and (not p.sales_order or p.sales_order[:10] == sales_order['name'][:10]):
            p.sales_order = sales_order['name']
        p.save()
        # update project data
        update_project(p.name)
        # trigger project creation in timeshepherd
        create_project(p.name)
    return

"""
Update project data
"""
def update_project(project):
    p = frappe.get_doc("Project", project)
    if p.object:
        o = frappe.get_doc("Object", p.object)
    else:
        o = None
    # find sales order data
    items = {
        'thermo': frappe.get_value("Heim Settings", "Heim Settings", "thermozement_item"),
        'staged_cementation': frappe.get_value("Heim Settings", "Heim Settings", "staged_cementation_item"),
        'internal_crane': frappe.get_value("Heim Settings", "Heim Settings", "internal_crane_item"),
        'external_crane': frappe.get_value("Heim Settings", "Heim Settings", "external_crane_item"),
        'self_crane': frappe.get_value("Heim Settings", "Heim Settings", "self_crane_item"),
        'carrymax': frappe.get_value("Heim Settings", "Heim Settings", "carrymax_item")
    }
    activities = {
        'internal_crane': frappe.get_value("Heim Settings", "Heim Settings", "int_crane_activity"),
        'external_crane': frappe.get_value("Heim Settings", "Heim Settings", "crane_activity"),
        'carrymax': frappe.get_value("Heim Settings", "Heim Settings", "carrymax_activity")
    }
    
    if p.sales_order and frappe.db.exists("Sales Order", p.sales_order):
        so = frappe.get_doc("Sales Order", p.sales_order)
        p.thermozement = 0
        has_internal_crane = False
        has_external_crane = False
        has_self_crane = False
        has_carrymax = False
        for i in so.items:
            if i.item_code == items['thermo']:
                p.thermozement = 1
            elif o and i.item_code == items['staged_cementation']:
                o.staged_cementation = 1
            elif i.item_code == items['internal_crane']:
                has_internal_crane = True
            elif i.item_code == items['self_crane']:
                has_self_crane = True
            elif i.item_code.startswith(items['external_crane']):
                has_external_crane = True
            elif i.item_code == items['carrymax']:
                has_carrymax = True
                
        if has_internal_crane:
            p = set_checklist_activity(p, activities['internal_crane'])
        if has_external_crane:
            p = set_checklist_activity(p, activities['external_crane'])
        if has_carrymax:
            p = set_checklist_activity(p, activities['carrymax'])
        if has_self_crane:
            p = set_checklist_activity(p, activities['external_crane'])
            
        p.save()
        if o:
            o.save()
    return

"""
Check if a project has an activity if not add it
"""
def set_checklist_activity(project_doc, activity):
    occurs = False
    for a in project_doc.checklist:
        if a.activity == activity:
            occures = True
            break
    if not occurs:
        project_doc.append("checklist", {
            'activity': activity
        })
    return project_doc
    
"""
Get warranty accrual from sales order
"""
@frappe.whitelist()
def get_warranty_accural_percent(sales_order):
    return frappe.get_value("Sales Order", sales_order, "garantierueckbehalt")
    
""" 
Get warranty accruals that have been applied in a sales order
"""
@frappe.whitelist()
def get_applied_warranty_accruals(sales_order):
    amount = frappe.db.sql("""
        SELECT IFNULL(SUM(`tabDiscount Position`.`amount`), 0) AS `amount`
        FROM `tabDiscount Position`
        WHERE `tabDiscount Position`.`parent` IN (
            SELECT `tabSales Invoice Item`.`parent`
            FROM `tabSales Invoice Item`
            WHERE `tabSales Invoice Item`.`sales_order` = "{sales_order}"
              AND `tabSales Invoice Item`.`docstatus` = 1
            GROUP BY `tabSales Invoice Item`.`parent`
          )
          AND `tabDiscount Position`.`description` LIKE "%Garantierückbehalt%";
        """.format(sales_order=sales_order), as_dict=True)[0]['amount']
    return amount

"""
Return the related item list for an item
"""
def get_related_items(item_code):
    item = frappe.get_doc("Item", item_code)
    related_items = []
    for i in item.related_items:
        related_items.append({
            'item_code': i.item_code,
            'qty': i.qty or 1
        })
    return related_items

"""
Compile recipients for drilling notice
"""
@frappe.whitelist()
def get_drill_notice_recipients(project, address_types):
    if type(address_types) == str:
        address_types = json.loads(address_types)
    recipients = {'recipients': [], 'cc': []}
    p_doc = frappe.get_doc("Project", project)
    # drilling manager
    if p_doc.drilling_team:
        recipients['cc'].append(frappe.get_value("Drilling Team", p_doc.drilling_team, "email"))
    if p_doc.manager:
        recipients['cc'].append(p_doc.manager)
    # addresses
    o_doc = frappe.get_doc("Object", p_doc.object)
    for a in o_doc.addresses:
        if a.address_type in address_types:
            if a.is_simple == 0 and a.email:
                recipients['recipients'].append(a.email)
            elif a.is_simple == 1 and a.simple_email:
                recipients['recipients'].append(a.simple_email)
    return recipients

"""
Get next available internal project number
"""
@frappe.whitelist()
def get_next_internal_project_number():
    last_internal_project = frappe.db.sql("""
        SELECT MAX(`name`) AS `name`
        FROM `tabProject`
        WHERE `project_type` = "Internal"
          AND LENGTH(`name`) = 12;
    """, as_dict=True)
    if len(last_internal_project) == 0:
        return "P-INT-000001"
    else:
        n = int(get_numeric_part(last_internal_project[0]['name']))
        return "P-INT-{num:06d}".format(num=n+1)
        
"""
Update attached drilling instruction pdf
"""
@frappe.whitelist()
def update_attached_project_pdf(project):
    # check if this is already attached
    attachments = get_attachments("Project", project)
    for a in attachments:
        if a.file_name == "{0}.pdf".format(project):
            remove_file(a.name, "Project", project)
    # create and attach
    execute("Project", project, title=project, print_format="Bohrauftrag")
    return

"""
Update attached drilling instruction pdf
"""
@frappe.whitelist()
def update_attached_sv_ib_pdf(project):
    # check if this is already attached
    attachments = get_attachments("Project", project)
    street = frappe.get_value("Project", project, "object_street")
    location = frappe.get_value("Project", project, "object_location")
    
    # clean old files
    for a in attachments:
        if a.file_name.startswith("SV-P-") or a.file_name.startswith("IB-P-"):
            remove_file(a.name, "Project", project)
        
    # SV 
    title = ("SV-{0} {1}, {2}.pdf".format(project, street, location)).replace("/", ",")
    # create and attach
    execute("Project", project, title=project, print_format="SV combined", file_name=title)
    
    # IB 
    title = ("IB-{0} {1}, {2}.pdf".format(project, street, location)).replace("/", ",")
    # create and attach
    execute("Project", project, title=project, print_format="IB combined", file_name=title)
    return

"""
Update attached construction site description pdf
"""
@frappe.whitelist()
def update_attached_csd_pdf(construction_site_description):
    # check if this is already attached
    attachments = get_attachments("Construction Site Description", construction_site_description)
    title = "{0}.pdf".format(construction_site_description)
    project = frappe.get_value("Construction Site Description", construction_site_description, "project")
    for a in attachments:
        if a.file_name.startswith(construction_site_description):
            remove_file(a.name, "Construction Site Description", construction_site_description)
    # create and attach
    execute("Construction Site Description", construction_site_description, title=project, print_format="Baustellenbeschreibung", file_name=title)
    return
    
""" 
Create a full project file
"""
@frappe.whitelist()
def create_full_project_file(project):   
    # first part: order
    html = frappe.get_print("Project", project, print_format="Bohrauftrag")
    pdf = frappe.utils.pdf.get_pdf(html, print_format="Bohrauftrag")
    pdf_file = "/tmp/{0}.pdf".format(uuid.uuid4().hex)
    with open(pdf_file, mode='wb') as file:
        file.write(pdf)
    # create merger
    merger = PdfFileMerger(strict=False)                    # accept technically incorrect PDFs
    merger.append(pdf_file)
    # other pages from construction plans
    p_doc = frappe.get_doc("Project", project)
    if p_doc.plans:
        for plan in p_doc.plans:
            if plan.file and plan.file[-4:].lower() == ".pdf":
                try:
                    merger.append("{0}/sites/{1}{2}".format(
                        get_bench_path(), 
                        get_files_path().split("/")[1],
                        plan.file))
                except Exception as err:
                    frappe.throw( _("Fehler bei Plan {0}: {1}").format(plan.file, err), _("Fehler beim Erstellen"))
    # ... and from permits
    if p_doc.permits:
        for permit in p_doc.permits:
            if permit.file and permit.file[-4:].lower() == ".pdf":
                try:
                    merger.append("{0}/sites/{1}{2}".format(
                        get_bench_path(), 
                        get_files_path().split("/")[1],
                        permit.file))
                except Exception as err:
                    frappe.throw( _("Fehler bei Bewilligung {0}: {1}").format(permit.file, err), _("Fehler beim Erstellen"))

    tmp_name = "/tmp/project-dossier-{0}.pdf".format(uuid.uuid4().hex)
    merger.write(tmp_name)
    merger.close()
    cleanup(pdf_file)
        
    # attach
    # check if this is already attached
    target_name = "Dossier_{name}.pdf".format(name=project.replace(" ", "-").replace("/", "-"))
    attachments = get_attachments("Project", project)
    for a in attachments:
        if a.file_name == target_name:
            remove_file(a.name, "Project", project)
    
    with open(tmp_name, mode='rb') as file:
        combined_pdf = file.read()
    cleanup(tmp_name)
    
    # create and attach
    folder = create_folder("Dossier", "Home")
    save_file(target_name, combined_pdf, "Project", project, folder, is_private=True)

    # set project file as created
    if not p_doc.project_file_created:
        p_doc.project_file_created = 1
        p_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    return

"""
Create a print version and include the construction plans from the project
"""
@frappe.whitelist()
def create_subcontracting_order_pdf(subcontracting_order):  
    # first part: print format
    html = frappe.get_print("Subcontracting Order", subcontracting_order, print_format="Verlängerungsauftrag")
    pdf = frappe.utils.pdf.get_pdf(html, print_format="Verlängerungsauftrag")
    pdf_file = "/tmp/{0}.pdf".format(uuid.uuid4().hex)
    with open(pdf_file, mode='wb') as file:
        file.write(pdf)
    # create merger
    merger = PdfFileMerger(strict=False)                    # accept technically incorrect PDFs
    merger.append(pdf_file)
    # other pages from construction plans (project)
    p_doc = frappe.get_doc("Project", frappe.get_value("Subcontracting Order", subcontracting_order, "project"))
    if p_doc.plans:
        for plan in p_doc.plans:
            merger.append("{0}/sites/{1}{2}".format(
                get_bench_path(), 
                get_files_path().split("/")[1],
                plan.file))
    # other pages from construction plans (subcontracting order)
    s_doc = frappe.get_doc("Subcontracting Order", subcontracting_order)
    if s_doc.plans:
        for plan in s_doc.plans:
            merger.append("{0}/sites/{1}{2}".format(
                get_bench_path(), 
                get_files_path().split("/")[1],
                plan.file))
                
    tmp_name = "/tmp/project-dossier-{0}.pdf".format(uuid.uuid4().hex)
    merger.write(tmp_name)
    merger.close()
    cleanup(pdf_file)
    
    # attach
    # check if this is already attached
    target_name = "{name}.pdf".format(name=subcontracting_order.replace(" ", "-").replace("/", "-"))
    attachments = get_attachments("Subcontracting Order", subcontracting_order)
    for a in attachments:
        if a.file_name == target_name:
            remove_file(a.name, "Subcontracting Order", subcontracting_order)
    
    with open(tmp_name, mode='rb') as file:
        combined_pdf = file.read()
    cleanup(tmp_name)
    
    # create and attach
    folder = create_folder("Subcontracting Order", "Home")
    save_file(target_name, combined_pdf, "Subcontracting Order", subcontracting_order, folder, is_private=True)
        
    return
    
def cleanup(fname):
    import os
    if os.path.exists(fname):
        os.remove(fname)
    
"""
Return other invoiced markup/discounts in the same sales order
"""
@frappe.whitelist()
def get_invoiced_markup_discounts(sales_order):
    positions = frappe.db.sql("""
        SELECT `description`, `percent`, `amount`, `parent`
        FROM `tabMarkup Position`
        WHERE `parent` IN 
            (SELECT `parent`
            FROM `tabSales Invoice Item` 
            WHERE `sales_order` = "{sales_order}"
              AND `docstatus` < 2
              AND `percent` = 0
            GROUP BY `parent`)
        UNION SELECT `description`, `percent`, `amount`, `parent`
        FROM `tabDiscount Position`
        WHERE `parent` IN 
            (SELECT `parent`
            FROM `tabSales Invoice Item` 
            WHERE `sales_order` = "AB-2200469"
              AND `docstatus` < 2
              AND `percent` = 0
            GROUP BY `parent`);""".format(sales_order=sales_order), as_dict=True)
    return positions

"""
Find conversations from Infomails and create infomail records
"""
def check_infomails():
    new_communications = frappe.db.sql("""
        SELECT 
            `tabCommunication`.`name`,
            `tabCommunication`.`subject`,
            `tabCommunication`.`sender`,
            `tabCommunication`.`recipients`,
            `tabCommunication`.`cc`,
            `tabCommunication`.`reference_name` AS `project`,
            `tabCommunication`.`content`,
            `tabCommunication`.`communication_date`
        FROM `tabCommunication`
        LEFT JOIN `tabInfomail` ON `tabInfomail`.`communication` = `tabCommunication`.`name`
        WHERE 
            `reference_doctype` = "Project"
            AND `sent_or_received` = "Sent"
            AND `tabInfomail`.`name` IS NULL
            AND `subject` LIKE "Bohrstart%";
    """, as_dict=True)
    for c in new_communications:
        # this communication has not been linked yet - create infomal record
        create_infomail(
            project=c['project'],
            communication_date=c['communication_date'],
            sender=c['sender'],
            recipients=c['recipients'],
            cc=c['cc'],
            content=c['content'],
            communication=c['name']
        )
        # check if there are additional projects
        projects = re.findall(r"P-[0-9]{6}", c['subject'])
        for p in projects:
            if p != c['project'] and frappe.db.exists("Project", p):
                create_infomail(
                    project=p,
                    communication_date=c['communication_date'],
                    sender=c['sender'],
                    recipients=c['recipients'],
                    cc=c['cc'],
                    content=c['content'],
                    communication=c['name']
                )
    frappe.db.commit()
    return

def create_infomail(project, communication_date, sender, recipients, cc, content, communication):
    infomail = frappe.get_doc({
        'doctype': 'Infomail',
        'project': project,
        'date': communication_date,
        'sender': sender,
        'recipients': recipients,
        'cc': cc,
        'content': content,
        'communication': communication
    })
    infomail.insert(ignore_permissions=True)
    return
        
"""
Check that public access requests that have been mailed are marked as sent
"""
def check_sent_public_access_requests():
    unsent_requests = frappe.db.sql(""" 
        SELECT `name`
        FROM `tabRequest for Public Area Use`
        WHERE `sent` = 0;""", as_dict=True)
        
    for request in unsent_requests:
        communications = frappe.db.sql("""
            SELECT 
                `tabCommunication`.`name`
            FROM `tabCommunication`
            WHERE 
                `reference_doctype` = "Request for Public Area Use"
                AND `sent_or_received` = "Sent"
                AND `reference_name` = "{request_name}";""".format(request_name=request['name']), as_dict=True)
        if communications and len(communications) > 0:
            r = frappe.get_doc("Request for Public Area Use", request['name'])
            r.sent = 1
            r.save()
            frappe.db.commit()
    return

"""
Check if there are projects/objects of the same root
"""
@frappe.whitelist()
def has_siblings(doctype, name):
    siblings = frappe.db.sql("""
        SELECT `name`
        FROM `tab{dt}`
        WHERE 
            `name` LIKE "{dn_pre}%"
            AND `name` != "{dn}";""".format(dt=doctype, dn_pre=name[:8], dn=name), as_dict=True)
    return siblings

"""
This function move a purchase order to another project
"""
@frappe.whitelist()
def reassign_project(purchase_order, old_project, new_project):
    frappe.db.sql("""
        UPDATE `tabPurchase Order Item`
        SET `project` = "{project}"
        WHERE `parent` = "{purchase_order}"
          /* AND `project` = "{old_project}" */;
    """.format(purchase_order=purchase_order, project=new_project, old_project=old_project))
    if "P-" in new_project:
        frappe.db.sql("""
            UPDATE `tabPurchase Order`
            SET `object` = "{project}"
            WHERE `name` = "{purchase_order}";
        """.format(purchase_order=purchase_order, project=new_project))
    
    # consider downstream documents
    if "P-" in new_project:
        # find purchase receipts
        purchase_receipts = frappe.db.sql("""
            SELECT `parent` 
            FROM `tabPurchase Receipt Item`
            WHERE `purchase_order` = "{purchase_order}"
            ;
        """.format(purchase_order=purchase_order), as_dict=True)
        
        for pr in purchase_receipts:
            frappe.db.sql("""
                UPDATE `tabPurchase Receipt`
                SET `object` = "{project}"
                WHERE `name` = "{purchase_receipt}";
            """.format(purchase_receipt=pr['parent'], project=new_project))
        
            frappe.db.sql("""
                UPDATE `tabPurchase Receipt Item`
                SET `project` = "{project}"
                WHERE `parent` = "{purchase_receipt}"
                ;
            """.format(purchase_receipt=pr['parent'], project=new_project))
        
    doc = frappe.get_doc("Purchase Order", purchase_order)
    doc.add_comment("Info", _("Umbuchen von {0} auf {1}").format(old_project, new_project))
    
    return

"""
Create an email to request a Google Review
"""
@frappe.whitelist()
def request_google_review(project):
    p_doc = frappe.get_doc("Project", project)
    default_sender = frappe.get_all("Email Account", 
        filters={'enable_outgoing': 1, 'default_outgoing': 1}, 
        fields=['name', 'email_id'])
        
    if not p_doc.review_email or len(default_sender) == 0:
        frappe.throw("Kann Mail nicht senden")
        return
    
    # mark sending date stamp
    p_doc.review_date = datetime.now().strftime("%Y-%m-%d") 
    p_doc.save()
    frappe.db.commit()
    
    # send mail
    make_email(
        recipients=p_doc.review_email,
        sender=default_sender[0]['email_id'],
        subject="Projektabschluss {0}".format(project),
        content="""
        <p>Sehr geehrte Damen und Herren,</p>
        <p>Wir danken Ihnen von ganzem Herzen für Ihren Auftrag und hoffen, dass Sie mit unserer Arbeit zufrieden sind.</p>
        <p>Abschliessend möchten wir Sie bitten, eine konstruktive Bewertung für mögliche Neukunden zu hinterlassen, 
        damit diese sich ein Bild von unserem Unternehmen aus Kundensicht machen können. 
        Bitte nehmen Sie sich dafür ein paar Minuten Zeit und nutzen Sie einfach den untenstehenden Link.</p>
        <p><br></p>
        <p><a href="https://g.page/r/CSV3lLBR34VnEBM/review">https://g.page/r/CSV3lLBR34VnEBM/review</a></p>
        <p><br></p>
        <p>Wir danken Ihnen schon jetzt sehr und wünschen Ihnen im Namen der ganzen Firma besinnliche Weihnachtstage sowie einen guten Rutsch in ein gesundes neues Jahr.</p>
        <p>Freundliche Grüsse</p>
        <p><br></p>
        <p>Heim Bohrtechnik AG</p>
        """,
        doctype="Project",
        name=project,
        attachments=[],
        send_email=True
    )
    
    return

def clone_attachments(source_dt, source_name, target_dt, target_name):
    attachments = frappe.get_all("File", 
        filters={'attached_to_doctype': source_dt, 'attached_to_name': source_name},
        fields=['name']
    )
    for a in attachments:
        source = frappe.get_doc("File", a['name']).as_dict()            # pull original file
        clone = frappe.get_doc(source)                                  # create new record
        clone.attached_to_doctype = target_dt                           # map to target
        clone.attached_to_name = target_name
        clone.insert()                                                  # insert
        
    frappe.db.commit()
    
    return
    
@frappe.whitelist()
def quick_entry_purchase_invoice(company, supplier, date, bill_no, item, 
    amount, cost_center, taxes_and_charges, project=None, remarks=None):
    
    pinv = frappe.get_doc({
        'doctype': 'Purchase Invoice',
        'company': company,
        'supplier': supplier,
        'posting_date': date, 
        'project': project, 
        'bill_no': bill_no, 
        'cost_center': cost_center, 
        'taxes_and_charges': taxes_and_charges, 
        'terms': remarks,
        'remarks': remarks,
        'title': frappe.get_value("Supplier", supplier, "supplier_name")
    })
    
    pinv.append("items", {
        'item_code': item,
        'qty': 1,
        'rate': amount,
        'amount': amount
    })
    
    if project:
        p_doc = frappe.get_doc("Project", project)
        pinv.object = p_doc.object
    
    taxes = frappe.get_doc("Purchase Taxes and Charges Template", taxes_and_charges)
    for t in taxes.taxes:
        pinv.append("taxes", t)
        
    pinv.set_missing_values()
    pinv.calculate_taxes_and_totals()
    pinv.flags.ignore_validate = True
    pinv.save()
    
    return pinv.name

"""
Identify the header information from the last "Bohranzeige" sent for a project
"""
@frappe.whitelist()
def find_bohranzeige_mail_header(project):
    # first, find drilling notices for this project
    dns = frappe.get_all("Bohranzeige", filters={'project': project}, fields=['name', 'bewilligung'])
    header = {
        'date': None,
        'recipients': None,
        'cc': None,
        'permit': None
    }
    if len(dns) > 0:
        for dn in dns:
            # find communication
            comms = frappe.get_all("Communication", 
                filters={'reference_name': dn['name'], 'reference_doctype': 'Bohranzeige'}, 
                fields=['name', 'communication_date', 'recipients', 'cc'])
            if len(comms) > 0:
                if not header['date'] or comms[0]['communication_date'] > header['date']:
                    header['date'] = comms[0]['communication_date']
                    header['recipients'] = comms[0]['recipients']
                    header['cc'] = comms[0]['cc']
            
            header['permit'] = dn['bewilligung']
            
    return header

"""
This is a hack because description could not have been formated (always dropped on save)
"""
def item_description_save(item, event):
    if item.new_description:
        item.description = item.new_description
    else:
        item.descritpion = item.item_name
    return

@frappe.whitelist()
def find_supplier_item(item_code, supplier, idx=None):
    try:
        supplier_items = frappe.db.sql("""
            SELECT `supplier_part_no`
            FROM `tabItem Supplier`
            WHERE `parenttype` = "Item"
              AND `parent` = "{item_code}"
              AND `supplier` = "{supplier}";
        """.format(item_code=item_code, supplier=supplier), as_dict=True)
        if len(supplier_items) > 0:
            return {'supplier_part_no': supplier_items[0]['supplier_part_no'], 'idx': idx}
        else:
            return {'supplier_part_no': None, 'idx': idx}
    except:
        return {'supplier_part_no': None, 'idx': idx}
    
@frappe.whitelist()
def get_drilling_meters_per_day(project, objekt, start_date, start_hd, end_date, end_hd):
    #get project duration in workdays
    duration = get_duration_days(start_date, start_hd, end_date, end_hd)
    
    #get total drilling meter from object
    sql_query = """
        SELECT SUM(`ews_count` * `ews_depth`) AS `meter`
        FROM `tabObject EWS`
        WHERE `parent` = '{objekt}'
        """.format(objekt=objekt)
    meter = frappe.db.sql(sql_query, as_dict=True)
    
    #get drilling meter per day
    meter_per_day = meter[0]['meter'] / duration

    #send information if drilling meter per day are below 150
    if meter_per_day < 150:
        frappe.msgprint("Achtung! Das Projekt {proj} hat durchschnittlich nur {mpd} Bohrmeter pro Tag.".format(proj=project, mpd=int(meter_per_day)))
    
    return duration, meter_per_day

"""
Get an object with all addresses as full dicts
"""
@frappe.whitelist()
def get_object_with_addresses(obj):
    obj_dict = frappe.get_doc("Object", obj).as_dict()
    
    if "addresses" in obj_dict:
        for a in obj_dict.addresses:
            if a['address']:
                a['address_doc'] = frappe.get_doc("Address", a['address']).as_dict()
    
    return obj_dict
    
"""
Find SV for a project and attach to a sales invoice
"""
@frappe.whitelist()
def find_and_attach_sv(object_name, sales_invoice):
    # find SV attachments
    projects = frappe.get_all("Project", filters={'object': object_name}, fields=['name'])
    
    for p in projects:
        attached_sv_files = frappe.db.sql("""
            SELECT `name`
            FROM `tabFile`
            WHERE `file_name` LIKE "SV-{project}%"
              AND `attached_to_name` = "{project}"
              AND `attached_to_doctype` = "Project";
            """.format(project=p['name']), as_dict=True)
        
        for sv in attached_sv_files:
            sv_file = frappe.get_doc("File", sv['name'])
            new_attachment = frappe.get_doc(sv_file.as_dict())
            new_attachment.update({
                'name': None,
                'attached_to_name': sales_invoice,
                'attached_to_doctype': "Sales Invoice"
            })
            try:
                new_attachment.insert()
                frappe.db.commit()
            except Exception as err:
                frappe.log_error(err, "find_and_attach_sv error")
                
    return
            

"""
Purchase Order from stock: create Purchase Receipt and close both order and receipt
"""
@frappe.whitelist()
def po_from_stock(purchase_order):
    if type(purchase_order) == str:
        purchase_order = frappe.get_doc("Purchase Order", purchase_order)
    
    # create purchase receipt
    purchase_receipt = frappe.get_doc(make_purchase_receipt(purchase_order.name))
    purchase_receipt.insert()
    purchase_receipt.submit()
    
    # close purchase receipt and order
    purchase_receipt.update_status("Closed")
    purchase_order.update_status("Closed")
    frappe.db.commit()
    
    return

"""
Find default trough size
"""
@frappe.whitelist()
def get_default_trough_size(supplier):
    trough_activity = frappe.get_value("Heim Settings", "Heim Settings", "trough_activity")
    defaults = frappe.db.sql("""
        SELECT `default_trough_size`
        FROM `tabSupplier Activity`
        WHERE 
            `parenttype` = "Supplier"
            AND `parentfield` = "capabilities"
            AND `activity` = "{activity}"
            AND `parent` = "{supplier}"
        ;""".format(activity=trough_activity, supplier=supplier),
        as_dict=True)
        
    if len(defaults) > 0:
        return defaults[0]['default_trough_size']
    else:
        return None
        
