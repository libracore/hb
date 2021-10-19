# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

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
        if o.activity == config.mud_activity:
            if o.invoice_to:
                customer = o.invoice_to
    # create new invoice
    new_sinv = frappe.get_doc({
        'doctype': 'Sales Invoice',
        'company': config.company,
        'customer': customer,
        'object': object
    })
    # get delivieries and add as positions
    invoiceable_deliveries = get_deliveries(object)
    if invoiceable_deliveries and len(invoiceable_deliveries) > 0:
        for i in invoiceable_deliveries:
            new_sinv.append('items', {
                'item_code': config.mud_item,
                'qty': i['weight'] / 1000,
                'description': "{date}: {truck}".format(date=i['date'], truck=i['truck']),
                'truck_delivery': i['delivery'],
                'truck_delivery_detail': i['detail']
            })
        # insert the new sales invoice
        new_sinv.insert()
        
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
          AND `tabSales Invoice Item`.`name` IS NULL;""".format(object=object)
    invoicable_deliveries = frappe.db.sql(sql_query, as_dict=True)
    return invoicable_deliveries

def has_invoiceable_mud(object):
    invoiceable_deliveries = get_deliveries(object)
    if invoiceable_deliveries and len(invoiceable_deliveries) > 0:
        return True
    else:
        return False
