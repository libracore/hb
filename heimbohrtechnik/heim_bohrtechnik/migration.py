# Copyright (c) 2021-2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from heimbohrtechnik.heim_bohrtechnik.dataparser import get_projects
from heimbohrtechnik.heim_bohrtechnik.utils import update_project
from erpnextswiss.scripts.crm_tools import get_primary_supplier_address, get_primary_customer_address
from datetime import datetime
import cgi

ROW_SEPARATOR = "\n"
CELL_SEPARATOR = ";"

"""
This function can bulk import supplier files
"""
def update_suppliers(filename, service_type):
    REMARK=0                
    SUPPLIER_NAME=1
    ADDRESS_2=2
    CONTACT=3
    STREET=4
    PINCODE=5
    CITY=6
    CANTON=7
    PHONE=8
    MAIL=9
    MOBILE=10
    # read input file
    file = open(filename, "rU")
    data = file.read()   # .decode('utf-8')
    rows = data.split(ROW_SEPARATOR)
    print("Rows: {0}".format(len(rows)))
    for i in range(0, len(rows)):
        print("Row: {0}".format( rows[i]))
        cells = rows[i].split(CELL_SEPARATOR)

        if len(cells) > 1:
            print("Cells: {0}".format(len(cells)))
            # check if item exists
            print("Checking " + get_field(cells[SUPPLIER_NAME]))
            
            docs = frappe.get_all("Supplier", filters={'supplier_name': get_field(cells[SUPPLIER_NAME])}, fields=['name'])
            if docs and len(docs) > 0:
                # find and update supplier
                doc = frappe.get_doc("Supplier", docs[0]['name'])
            else:
                # create supplier
                doc = frappe.get_doc({
                    'doctype': 'Supplier',
                    'supplier_name': get_field(cells[SUPPLIER_NAME]),
                    'supplier_group': "Lieferant",
                    'supplier_type': "Company"
                })
                doc.insert()
            doc.append("capabilities", {'activity': service_type, 'remarks': get_field(cells[REMARK])})
            doc.save()
                
            if get_field(cells[STREET]):
                # check and update address
                sql_query = """SELECT `tabAddress`.`name`
                        FROM `tabDynamic Link` 
                        LEFT JOIN `tabAddress` ON `tabDynamic Link`.`parent` = `tabAddress`.`name`
                        WHERE `link_doctype` = 'Supplier'
                          AND `link_name` = "{supplier}"
                          AND `address_line1` = "{street}"
                        ORDER BY `tabAddress`.`is_primary_address` DESC;""".format(supplier=doc.name, street=get_field(cells[STREET]))
                addresses = frappe.db.sql(sql_query, as_dict=True)
                if addresses and len(addresses)  > 0:
                    # update address
                    address = frappe.get_doc("Address", addresses[0]['name'])
                    address.address_line2 = get_field(cells[ADDRESS_2])
                    address.pincode = get_field(cells[PINCODE])
                    address.plz = get_field(cells[PINCODE])
                    address.city = get_field(cells[CITY])
                    address.state = get_field(cells[CANTON])
                    address.is_primary_address = 1
                    address.save()
                else:
                    address = frappe.get_doc({
                        'doctype': 'Address',
                        'address_type': "Billing",
                        'address_line1': get_field(cells[STREET]),
                        'address_line2': get_field(cells[ADDRESS_2]),
                        'pincode': get_field(cells[PINCODE]),
                        'plz': get_field(cells[PINCODE]),
                        'city': get_field(cells[CITY]),
                        'state': get_field(cells[CANTON])
                    })
                    address.append('links', {
                        'link_doctype': "Supplier",
                        'link_name': doc.name
                    })
                    address.insert()
                
            # check and update contact
            first_name = None
            last_name = None
            gender = None
            name_parts = get_field(cells[CONTACT]).split(" ")
            if len(name_parts) >2:
                first_name = name_parts[1]
                last_name = name_parts[2]
                if "H" in name_parts[0]:
                    gender = "Männlich"
                else:
                    gender = "Weiblich"
            if first_name and last_name:
                sql_query = """SELECT `tabContact`.`name`
                        FROM `tabDynamic Link` 
                        LEFT JOIN `tabContact` ON `tabDynamic Link`.`parent` = `tabContact`.`name`
                        WHERE `link_doctype` = 'Supplier'
                          AND `link_name` = "{supplier}"
                          AND `last_name` = "{last_name}"
                        ;""".format(supplier=doc.name, last_name=last_name)
                contacts = frappe.db.sql(sql_query, as_dict=True)
                if contacts and len(contacts)  > 0:
                    # update contact
                    contact = frappe.get_doc("Contact", contacts[0]['name'])
                else:
                    contact = frappe.get_doc({
                        'doctype': 'Contact',
                        'first_name': first_name,
                        'last_name': last_name,
                        'gender': gender
                    })
                    contact.append('links', {
                        'link_doctype': "Supplier",
                        'link_name': doc.name
                    })
                    contact.insert()
                    
                contact.first_name = first_name
                if get_field(cells[MAIL]):
                    contact.email_ids = []
                    contact.append('email_ids', {
                        'email_id': get_field(cells[MAIL]),
                        'is_primary': 1
                    })
                if get_field(cells[PHONE]) or get_field(cells[MOBILE]):
                    contact.phone_nos = []
                    if get_field(cells[PHONE]):
                        contact.append('phone_nos', {
                            'phone': get_field(cells[PHONE]),
                            'is_primary_phone': 1
                        })
                    if get_field(cells[MOBILE]):
                        contact.append('phone_nos', {
                            'phone': get_field(cells[MOBILE]),
                            'is_primary_mobile_no': 1
                        })
                contact.save()
            
            print("Updated {supplier}".format(supplier=doc.name))
    return

# removes the quotation marks from a cell
def get_field(content):
    return content.replace("\"", "")

# read projects
def load_projects(filename):
    teams_with_projects = get_projects(filename)
    for team in teams_with_projects:
        # resolve team name
        team_name = frappe.db.sql("""SELECT `name` FROM `tabDrilling Team` WHERE `name` LIKE "%{0}%" LIMIT 1;""".format(team['drilling_team']), as_dict=True)[0]['name']
        for project in team['projects']:
            print("Project data: {0}".format(project))
            # clean up project name
            project['name'] = (project['name'] or "").strip()
            # check if object exists
            if frappe.db.exists("Object", project['name']) or frappe.db.exists("Object", "P-{0}".format(project['name'])):  # retrofit, check new number where P- was left out on Excel
                if frappe.db.exists("Object", project['name']):
                    existing_object = frappe.get_doc("Object", project['name'])
                else:
                    existing_object = frappe.get_doc("Object", "P-{0}".format(project['name']))
                if project['object_street']:
                    existing_object.object_street=cgi.escape(str(project['object_street'] or "??")).replace("\"", "")
                if project['object_name']:
                    existing_object.object_name=cgi.escape(str(project['object_name'] or "??")).replace("\"", "")
                if project['object_city']:
                    existing_object.object_location = cgi.escape(str(project['object_city'] or "??")).replace("\"", "")
                    # break down location into plz, city, canton
                    try:
                        location_parts = (str(project['object_city'] or "??")).split(" ")
                        existing_object.plz = location_parts[0]
                        existing_object.kanton = location_parts[-1]
                        existing_object.city = " ".join(location_parts[1:-1])
                    except:
                        pass
                existing_object.save()
            else:
                # brute force insert to override naming series
                frappe.db.sql("""INSERT INTO `tabObject`
                    (`name`,
                    `creation`,
                    `modified`,
                    `modified_by`,
                    `owner`,
                    `docstatus`,
                    `object_name`,
                    `object_location`,
                    `object_street`)
                    VALUES
                    ("{name}",
                    "{creation}",
                    "{creation}",
                    "Administrator",
                    "Administrator",
                    0,
                    "{object_name}",
                    "{object_location}",
                    "{object_street}");""".format(name=project['name'],
                        creation=datetime.now(), object_name=cgi.escape(project['object_name'] or "??").replace("\"", ""),
                        object_location=cgi.escape(project['object_city'] or "??").replace("\"", ""), 
                        object_street=cgi.escape(project['object_street'] or "??").replace("\"", "")))
                        
            # check if project exists
            if frappe.db.exists("Project", project['name']) or frappe.db.exists("Project", "P-{0}".format(project['name'])):
                # existing project, update
                if frappe.db.exists("Project", "P-{0}".format(project['name'])):
                    existing_project = frappe.get_doc("Project", "P-{0}".format(project['name']))
                else:
                    existing_project = frappe.get_doc("Project", project['name'])
                # find customer
                customer_matches = frappe.get_all("Customer", filters={'customer_name': project['customer_name']}, fields=['name'])
                if customer_matches and len(customer_matches) > 0:
                    existing_project.customer = customer_matches[0]['name']
                else:
                    # fallback: try to wilcard-match customer
                    customer_matches = frappe.db.sql("""SELECT `name`
                        FROM `tabCustomer`
                        WHERE `customer_name` LIKE "%{0}%";""".format(str(project['customer_name']).replace("\"", "")), as_dict=True)
                    if customer_matches and len(customer_matches) > 0:
                        existing_project.customer = customer_matches[0]['name']
                    else:
                        print("Cannot match {0} in {1}".format(project['customer_name'], project['name']))
                existing_project.project_type = "External"
                existing_project.expected_start_date = project['start_date']
                existing_project.expected_end_date = project['end_date']
                existing_project.drilling_team = team_name
                existing_project.start_half_day = "VM" if project['start_date_vm'] else "NM"
                existing_project.end_half_day = "VM" if project['end_date_vm'] else "NM"
                existing_project.status = project['status']
                existing_project.object = existing_object.name
                existing_project.object_street=cgi.escape(str(project['object_street'] or "??")).replace("\"", "")
                existing_project.manager = find_manager((project['object_project_manager'] or "")[0:2])
                existing_project.save()
                print("Updated project {0}".format(project['name']))
            else:
                # this project is not yet in the database, create
                # check if this should be on a P- object
                if frappe.db.exists("Object", "P-{0}".format(project['name'])):
                    name = "P-{0}".format(project['name'])
                else:
                    name = project['name']
                new_project = frappe.get_doc({
                    'doctype': 'Project',
                    'project_name': name,
                    'drilling_team': team_name,
                    'expected_start_date': project['start_date'],
                    'expected_end_date': project['end_date'],
                    'start_half_day': "VM" if project['start_date_vm'] else "NM",
                    'end_half_day': "VM" if project['end_date_vm'] else "NM",
                    'status': project['status'],
                    'object': name,
                    'object_street': cgi.escape(str(project['object_street'] or "??")).replace("\"", ""),
                    'project_type': "External",
                    'manager': find_manager((project['object_project_manager'] or "")[0:2])
                })
                # find customer
                customer_matches = frappe.get_all("Customer", filters={'customer_name': project['customer_name']}, fields=['name'])
                if customer_matches and len(customer_matches) > 0:
                    new_project.customer = customer_matches[0]['name']
                new_project.insert()
                print("Created project {0}".format(project['name']))
            frappe.db.commit()

# this is a manual patch to correct older discount configurations (hotfix 2021-12-08)
def patch_discount_positions():
    # fetch wrong markups
    markups = frappe.db.sql("""
        SELECT * 
        FROM `tabDiscount Position` 
        WHERE `parentfield` = "markup_positions";""", 
        as_dict=True)
    
    for m in markups:
        print("Moving {0} from {1}".format(m['name'], m['parent']))
        # copy to new table
        frappe.db.sql("""
        INSERT INTO `tabMarkup Position`
        (`name`,
        `creation`,
        `modified`,
        `modified_by`,
        `owner`,
        `docstatus`,
        `parent`,
        `parentfield`,
        `parenttype`,
        `idx`,
        `description`,
        `bkp`,
        `basis`,
        `amount`,
        `percent`)
        VALUES
        ("{name}",
        "{creation}",
        "{modified}",
        "{modified_by}",
        "{owner}",
        {docstatus},
        "{parent}",
        "{parentfield}",
        "{parenttype}",
        {idx},
        "{description}",
        "{bkp}",
        {basis},
        {amount},
        {percent});
        """.format(
        name=m['name'],
        creation=m['creation'],
        modified=m['modified'],
        modified_by=m['modified_by'],
        owner=m['owner'],
        docstatus=m['docstatus'],
        parent=m['parent'],
        parentfield=m['parentfield'],
        parenttype=m['parenttype'],
        idx=m['idx'],
        description=m['description'],
        bkp=m['bkp'],
        basis=m['basis'],
        amount=m['amount'],
        percent=m['percent']
        ))
        # delete old record
        frappe.db.sql("""DELETE FROM `tabDiscount Position`
            WHERE `name` = "{name}";""".format(name=m['name']))
    frappe.db.commit()
    print("done")
    return

"""
This function goes through projects and cleans the links.
"""
def clean_project_object_links():
    projects = frappe.get_all("Project", fields=['name'])
    count = 0;
    for p in projects:
        count += 1
        print("Processing {0} ({1}%)".format(p['name'], int(100 * count/len(projects))))
        p_doc = frappe.get_doc("Project", p['name'])
        # check objetc link
        if p_doc.object and not frappe.db.exists("Object", p_doc.object):
            print("link broken, try to repair")
            matches = frappe.db.sql("""SELECT `name` 
                FROM `tabObject` 
                WHERE `name` LIKE "%{0}";""".format(p_doc.object), as_dict=True)
            if len(matches) == 1:
                print("found {0}".format(matches[0]['name']))
                p_doc.object = matches[0]['name']
                p_doc.save()
        # check sales order validity
        if p_doc.sales_order:
            so_doc = frappe.get_doc("Sales Order", p_doc.sales_order)
            if so_doc.docstatus == 2:
                # cancelled, find valid revision
                valid_sos = frappe.db.sql("""SELECT `name` FROM `tabSales Order` WHERE `name` LIKE "{0}%" and `docstatus` < 2;""".format(p_doc.sales_order), as_dict=True)
                if len(valid_sos) > 0:
                    p_doc.sales_order = valid_sos[0]['name']
                    p_doc.save() 
                    print("updated sales order {0}: {1}".format(p_doc.name, p_doc.sales_order))
    print("done")
    frappe.db.commit()
    return
        
def set_supplier_first_address():
    suppliers = frappe.get_all("Supplier", filters={'disabled': 0}, fields=['name'])
    for supplier in suppliers:
        s = frappe.get_doc("Supplier", supplier['name'])
        address = get_primary_supplier_address(s.name)
        if address:
            s.hauptadresse = "{0}, {1} {2}".format(address.address_line1 or "", address.pincode or "", address.city or "")
            s.save()
            print("Updated {0}".format(s.name))
    return
    
def set_customer_first_address():
    customers = frappe.get_all("Customer", filters={'disabled': 0}, fields=['name'])
    for customer in customers:
        c = frappe.get_doc("Customer", customer['name'])
        address = get_primary_customer_address(c.name)
        if address:
            c.hauptadresse = "{0}, {1} {2}".format(address.address_line1 or "", address.pincode or "", address.city or "")
            c.save()
            print("Updated {0}".format(c.name))
    return

def update_object_lat_long():
    objects = frappe.get_all("Object", filters=[['gps_coordinates', 'LIKE', '%,%']], fields=['name'])
    count = 0
    for o in objects:
        count += 1
        print("Processing {0} ({1})".format(o['name'], 100 * count / len(objects)))
        o_doc = frappe.get_doc("Object", o['name'])
        o_doc.set_gps()
        o_doc.save()
    frappe.db.commit()
    print("done")
    return

def update_gps_from_address():
    from heimbohrtechnik.heim_bohrtechnik.doctype.object.object import get_gps
    objects = frappe.db.sql("""SELECT `name` FROM `tabObject` 
        WHERE `object_street` IS NOT NULL
          AND `object_location` IS NOT NULL
          AND (`gps_coordinates` IS NULL
           OR `gps_coordinates` = ""); """, as_dict=True)
    count = 0
    for o in objects:
        count += 1
        print("Processing {0} ({1}%)".format(o['name'], int(100 * count / len(objects))))
        o_doc = frappe.get_doc("Object", o['name'])
        gps_coordinates = get_gps(o_doc.object_street, o_doc.object_location)
        o_doc.gps_coordinates = gps_coordinates
        o_doc.ch_coordinates = o_doc.convert_gps_to_ch()
        o_doc.save()
    frappe.db.commit()
    print("done")
    return

def update_projects():
    projects = frappe.get_all("Project", fields=['name'])
    count = 0
    for p in projects:
        count += 1
        print("Processing {0} ({1}%)".format(p['name'], int(100 * count / len(projects))))
        update_project(p['name'])
        p_doc = frappe.get_doc("Project", p['name'])
        if p_doc.expected_end_date and p_doc.expected_end_date < datetime.now().date() and p_doc.status == "Open":
            p_doc.status = "Completed"
        try:
            p_doc.save()
        except Exception as err:
            print(err)
    frappe.db.commit()
    print("done")
    return

def find_manager(short_name):
    matches = frappe.db.sql("""SELECT `name`
        FROM `tabUser`
        WHERE `username` LIKE "{short_name}";""".format(short_name=short_name), as_dict=True)
    if len(matches) > 0:
        return matches[0]['name']
    else: 
        return None
