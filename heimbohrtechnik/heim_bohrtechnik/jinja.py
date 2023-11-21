# Copyright (c) 2021-2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import json

"""
Return the structured data for the pressure check QR
"""
def get_project_pressure(project):
    project_doc = frappe.get_doc("Project", project)
    object_doc = frappe.get_doc("Object", project_doc.object)
    data = {
        'project': project,
        'name': project_doc.object_name,
        'street': project_doc.object_street,
        'location': project_doc.object_location,
        'gps_coordinates': object_doc.gps_coordinates,
        'probes': []
    }
    for probe in object_doc.ews_specification:
        data['probes'].append({
            'count': probe.ews_count,
            'probe_type': probe.probe_type,
            'depth': probe.ews_depth,
            'diameter': probe.ews_diameter,
            'filling': "Thermozement" if project_doc.thermozement else "Zement, Bentonit"
            
        })
    
    #content = frappe.render_template("templates/includes/pressure_check_qr.html", data)
    content = "{0}".format(data)
    
    return content 

"""
Return a list of sales invoices to a sales order
"""
def get_sales_invoices_for_order(sales_order_name):
    invoice_dict = frappe.db.sql("""
        SELECT `tabSales Invoice Item`.`parent`
        FROM `tabSales Invoice Item`
        WHERE `tabSales Invoice Item`.`sales_order` = "{sales_order}"
        GROUP BY `tabSales Invoice Item`.`parent`
        ORDER BY `tabSales Invoice Item`.`parent` ASC;
        """.format(sales_order=sales_order_name), as_dict=True)
        
    invoices = []
    for i in invoice_dict:
        invoices.append(i.get("parent"))
        
    return invoices

"""
Return a list of sales invoices items for a list of sales invoices
"""
def get_sales_invoice_positions(sales_invoices):
    if type(sales_invoices) == str:
        sales_invoices = json.loads(sales_invoices)
        
    invoice_positions = frappe.db.sql("""
        SELECT *
        FROM `tabSales Invoice Item`
        WHERE `tabSales Invoice Item`.`parent` IN ("{invoices}")
        ORDER BY `tabSales Invoice Item`.`parent` ASC, `tabSales Invoice Item`.`idx` ASC;
        """.format(invoices="\",\"".join(sales_invoices)), as_dict=True)
        
        
    return invoice_positions
