# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from dataparser import get_projects

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
def load_projects(fielname):
    teams_with_projects = get_projects(filename)
    for team in teams_with_projects:
        for project in team['projects']:
            # check if project exists
            if frappe.db.exists("Project", project['name']):
                # existing project, update
                
            else:
                # this project is not yet in the database, create
                new_project = frappe.get_doc({
                    'doctype': 'Project',
                    'project_title': project['name'],
                    'drilling_team': team['drilling_team'],
                    'expected_start_date': project['start_date'],
                    'expected_end_date': project['end_date']
                    'start_half_day': "VM" if project['start_date_vm'] else "NM",
                    'end_half_day': "VM" if project['end_date_vm'] else "NM",
                    'status': project['status']
                })
                new_project.insert()
                print("Created project{0}".format(project['name']))
                frappe.db.commit()
