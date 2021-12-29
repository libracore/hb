# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from heimbohrtechnik.heim_bohrtechnik.dataparser import get_projects
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
            # check if object exists
            if frappe.db.exists("Object", project['name']) or frappe.db.exists("Object", "P-{0}".format(project['name'])):  # retrofit, check new number where P- was left out on Excel
                if frappe.db.exists("Object", project['name']):
                    existing_object = frappe.get_doc("Object", project['name'])
                else:
                    existing_object = frappe.get_doc("Object", "P-{0}".format(project['name']))
                user = frappe.get_all("User", filters={'username': project['object_project_manager']}, fields=['name'])
                if user and len(user) > 0:
                    user = user[0]['name']
                    existing_object.manager = user
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
            if frappe.db.exists("Project", project['name']):
                # existing project, update
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
                existing_project.object = project['name']
                existing_project.save()
                print("Updated project {0}".format(project['name']))
            else:
                # this project is not yet in the database, create
                new_project = frappe.get_doc({
                    'doctype': 'Project',
                    'project_name': project['name'],
                    'drilling_team': team_name,
                    'expected_start_date': project['start_date'],
                    'expected_end_date': project['end_date'],
                    'start_half_day': "VM" if project['start_date_vm'] else "NM",
                    'end_half_day': "VM" if project['end_date_vm'] else "NM",
                    'status': project['status'],
                    'object': project['name'],
                    'project_type': "External"
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
