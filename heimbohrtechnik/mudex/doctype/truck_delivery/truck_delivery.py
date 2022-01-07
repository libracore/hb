# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime

class TruckDelivery(Document):
    def on_submit(self): 
        if self.net_weight < 1:
            frappe.throw( _("There is no valid weight recorded."), _("No weight") )
        return
    
    def validate(self):
        # compute unallocated weight
        unallocated_weight = self.net_weight
        for o in self.objects:
            unallocated_weight -= o.weight or 0
        # allocate remainder to last row
        if len(self.objects) < 1:
            frappe.throw( _("Please provide an object"), _("Object missing") )
        self.objects[-1].weight = (self.objects[-1].weight or 0) + unallocated_weight
        # collection information mails
        objects = []
        for o in self.objects:
            if o.object:
                objects.append("'{0}'".format(o.object))
        objects = ", ".join(objects)
        self.information_email = get_object_information_email(objects)
        return

"""
Create an invoice from all open positions of an object
"""
@frappe.whitelist()
def create_invoice(object):
    config = frappe.get_doc("MudEx Settings", "MudEx Settings")
    # find customer: either from Object or default
    o = frappe.get_doc("Object", object)
    customer = config.default_customer_for_mud
    for c in o.checklist:
        if c.activity == config.mud_activity:
            if c.invoice_to:
                customer = c.invoice_to
    # find taxes from customer record
    tax_templates = frappe.get_all('Party Account', 
        filters={'parent': customer, 'company': config.company},
        fields=['default_sales_taxes_and_charges'])
    if tax_templates and len(tax_templates) > 0:
        tax_template = tax_templates[0]['default_sales_taxes_and_charges']
    else:
        tax_template = None
    # set default cost center from company
    cost_center = frappe.get_value("Company", config.company, "cost_center")
    # get project link
    if frappe.db.exists("Project", object):
        project = object
    else:
        project = None
    # create new invoice
    new_sinv = frappe.get_doc({
        'doctype': 'Sales Invoice',
        'company': config.company,
        'customer': customer,
        'object': object,
        'taxes_and_charges': tax_template,
        'tax_id': frappe.get_value("Customer", customer, "tax_id"),
        'cost_center': cost_center,
        # 'project': project,               # do not link to project, as project customer is end customer (will create a validation error)
        'naming_series': 'RE-MX-.YY.#####',
        'title': 'Rechnung'
    })
    # apply taxes
    if tax_template:
        tax_details = frappe.get_doc("Sales Taxes and Charges Template", tax_template)
        for t in tax_details.taxes:
            new_sinv.append('taxes', {
                'charge_type': t.charge_type,
                'account_head': t.account_head,
                'description': t.description,
                'rate': t.rate
            })
    # get deliveries and add as positions
    invoiceable_deliveries = get_deliveries(object)
    if invoiceable_deliveries and len(invoiceable_deliveries) > 0:
        for i in invoiceable_deliveries:
            d = i['date']                       # datetime.strptime(str(i['date'])[:19], "%Y-%m-%d %H:%M:%S")
            new_sinv.append('items', {
                'item_code': config.mud_item,
                'qty': i['weight'] / 1000,
                'description': "{date}: {truck}".format(date=d.strftime("%d.%m.%Y, %H:%M"), truck=i['truck']),
                'truck_delivery': i['delivery'],
                'truck_delivery_detail': i['detail'],
                'cost_center': cost_center
            })
        # insert the new sales invoice
        new_sinv.insert()
        # submit directly internal/default customer
        if customer == config.default_customer_for_mud:
            new_sinv.submit()
            # create mathing purchase invoice
            pinv_company = new_sinv.customer_name
            pinv_supplier = frappe.get_all("Supplier", 
                filters={'supplier_name': config.company}, fields=['name'])[0]['name']
            pinv_cost_center = frappe.get_value("Company", pinv_company, "cost_center")
            # find taxes from customer record
            pinv_tax_templates = frappe.get_all('Party Account', 
                filters={'parent': pinv_supplier, 'company': pinv_company},
                fields=['default_purchase_taxes_and_charges'])
            if pinv_tax_templates and len(pinv_tax_templates) > 0:
                pinv_tax_template = pinv_tax_templates[0]['default_purchase_taxes_and_charges']
            else:
                pinv_tax_template = None
            # create new purchase invoice
            new_pinv = frappe.get_doc({
                'doctype': 'Purchase Invoice',
                'company': pinv_company,
                'supplier': pinv_supplier,
                'bill_no': new_sinv.name,
                'bill_date': new_sinv.posting_date,
                'due_date': new_sinv.due_date,
                'object': new_sinv.object,
                'project': new_sinv.project,
                'cost_center': pinv_cost_center,
                'taxes_and_charges': pinv_tax_template,
                'disable_rounded_total': 1
            })
            # add item positions
            for i in new_sinv.items:
                new_pinv.append('items', {
                    'item_code': i.item_code,
                    'qty': i.qty,
                    'description': i.description,
                    'rate': i.rate,
                    'cost_center': pinv_cost_center
                })
            # apply taxes
            if pinv_tax_template:
                pinv_tax_details = frappe.get_doc("Purchase Taxes and Charges Template", pinv_tax_template)
                for t in pinv_tax_details.taxes:
                    new_pinv.append('taxes', {
                        'charge_type': t.charge_type,
                        'account_head': t.account_head,
                        'description': t.description,
                        'rate': t.rate
                    })
            # insert
            new_pinv.insert()
            new_pinv.submit()
        return new_sinv.name
    else:
        frappe.throw( _("Nothng to invoice") )

"""
Use this function to get all deliveries to be invoiced
"""
@frappe.whitelist()
def get_deliveries(object):
    sql_query = """SELECT `tabTruck Delivery Object`.`name` AS `detail`, 
            `tabTruck Delivery`.`name` AS `delivery`, 
            `tabTruck Delivery Object`.`weight` AS `weight`,
            `tabTruck Delivery`.`truck` AS `truck`,
            `tabTruck Delivery`.`date` AS `date`
        FROM `tabTruck Delivery Object`
        LEFT JOIN `tabTruck Delivery` ON `tabTruck Delivery`.`name` = `tabTruck Delivery Object`.`parent`
        LEFT JOIN `tabSales Invoice Item` ON 
            (`tabTruck Delivery Object`.`name` = `tabSales Invoice Item`.`truck_delivery_detail`
             AND `tabSales Invoice Item`.`docstatus` = 1)
        WHERE `tabTruck Delivery`.`docstatus` = 1
          AND `tabTruck Delivery Object`.`object` = "{object}"
          AND `tabSales Invoice Item`.`name` IS NULL
        ORDER BY `tabTruck Delivery`.`date` ASC;""".format(object=object)
    invoicable_deliveries = frappe.db.sql(sql_query, as_dict=True)
    return invoicable_deliveries

@frappe.whitelist()
def has_invoiceable_mud(object):
    invoiceable_deliveries = get_deliveries(object)
    if invoiceable_deliveries and len(invoiceable_deliveries) > 0:
        return True
    else:
        return False

def get_object_information_email(objects):
    mud_activity = frappe.get_value("MudEx Settings", "MudEx Settings", "mud_activity")
    sql_query = """SELECT GROUP_CONCAT(`information_to`) AS `information_email`
        FROM `tabProject Checklist`
        WHERE `parent` IN ({objects})
          AND `activity` = "{activity}";""".format(objects=objects, activity=mud_activity)
    #frappe.throw(sql_query)
    data = frappe.db.sql(sql_query, as_dict=True)
    if data and len(data) > 0:
        return data[0]['information_email']
    else:
        return None
