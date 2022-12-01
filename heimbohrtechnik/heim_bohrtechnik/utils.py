# Copyright (c) 2021-2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from datetime import datetime, timedelta
import json
from frappe.utils import cint
from erpnextswiss.erpnextswiss.utils import get_numeric_part
from erpnextswiss.erpnextswiss.attach_pdf import execute
from frappe.desk.form.load import get_attachments
from frappe.utils.file_manager import remove_file

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
def get_standard_activities():
    activities = frappe.get_all("Checklist Activity", filters={'is_standard': 1}, fields=['name'], order_by='prio')
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

"""
This function find applicable akonto invoices
"""
@frappe.whitelist()
def get_available_akonto(sales_order):
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
            # add realetd items
            related_items = get_related_items(item)
            for r in related_items:
                items.append({
                    'item_code': r,
                    'qty': p.ews_count,
                    'project': object
                })
                # recursion: in case of staged cementation, check sub-level also
                if cint(obj.staged_cementation) == 1:
                    sub_related_items = get_related_items(r)
                    for sr in sub_related_items:
                        items.append({
                            'item_code': sr,
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
        sales_order = json.loads(sales_order)
    if 'object' in sales_order and sales_order['object']:
        if not frappe.db.exists("Project", sales_order['object']):
            o = frappe.get_doc("Object", sales_order['object'])
            o.create_project()
        # reference customer and sales order
        p = frappe.get_doc("Project", sales_order['object'])
        p.customer = sales_order['customer']
        if frappe.db.exists("Sales Order", sales_order['name']):
            p.sales_order = sales_order['name']
        p.save()
        # update project data
        update_project(p.name)
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
    # find sales order data (Thermozement)
    thermo_item = frappe.get_value("Heim Settings", "Heim Settings", "thermozement_item")
    staged_cementation_item = frappe.get_value("Heim Settings", "Heim Settings", "staged_cementation_item")
    if p.sales_order and frappe.db.exists("Sales Order", p.sales_order):
        so = frappe.get_doc("Sales Order", p.sales_order)
        p.thermozement = 0
        for i in so.items:
            if i.item_code == thermo_item:
                p.thermozement = 1
            elif o and i.item_code == staged_cementation_item:
                o.staged_cementation = 1
        p.save()
        if o:
            o.save()
    return

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
        related_items.append(i.item_code)
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
        WHERE `project_type` = "Internal";
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
Create a full project file
"""
@frappe.whitelist()
def create_full_project_file(project):
    import uuid
    from frappe.utils import get_bench_path, get_files_path
    from PyPDF2 import PdfFileMerger
    from frappe.utils.file_manager import save_file
    from erpnextswiss.erpnextswiss.attach_pdf import create_folder
    
    # first part: order
    html = frappe.get_print("Project", project, print_format="Bohrauftrag")
    pdf = frappe.utils.pdf.get_pdf(html)
    pdf_file = "/tmp/{0}.pdf".format(uuid.uuid4().hex)
    with open(pdf_file, mode='wb') as file:
        file.write(pdf)
    # create merger
    merger = PdfFileMerger()
    merger.append(pdf_file)
    # other pages from construction plans
    p_doc = frappe.get_doc("Project", project)
    if p_doc.plans:
        for plan in p_doc.plans:
            merger.append("{0}/sites/{1}{2}".format(
                get_bench_path(), 
                get_files_path().split("/")[1],
                plan.file))
    # ... and from permits
    if p_doc.permits:
        for permit in p_doc.permits:
            if permit.file and permit.file[-4:].lower() == ".pdf":
                merger.append("{0}/sites/{1}{2}".format(
                    get_bench_path(), 
                    get_files_path().split("/")[1],
                    permit.file))
    
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
        infomail = frappe.get_doc({
            'doctype': 'Infomail',
            'project': c['project'],
            'date': c['communication_date'],
            'sender': c['sender'],
            'recipients': c['recipients'],
            'cc': c['cc'],
            'content': c['content'],
            'communication': c['name']
        })
        infomail.insert(ignore_permissions=True)
    frappe.db.commit()
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
          AND `project` = "{old_project}";
    """.format(purchase_order=purchase_order, project=new_project, old_project=old_project))
    
    doc = frappe.get_doc("Purchase Order", purchase_order)
    doc.add_comment("Info", _("Umbuchen von {0} auf {1}").format(old_project, new_project))
    
    return
