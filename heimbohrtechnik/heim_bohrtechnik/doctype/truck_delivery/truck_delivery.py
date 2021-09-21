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
Run this function when cancelling a sales invoice to remove the links on the linked deliveries
"""
@frappe.whitelist()
def remove_sinv_links(sinv):
    linked_deliveries = frappe.get_all("Truck Delivery", filters={'sales_invoice': sinv}, fields=['name'])
    for d in linked_deliveries:
        doc = frappe.get_doc("Truck Delivery", d['name'])
        doc.sales_invoice = None
        doc.save()
    return
    
"""
Use this function to get all deliveries to be invoiced
"""
@frappe.whitelist()
def get_deliveries(object, sales_invoice):
    invoicable_deliveries = frappe.get_all("Truck Delivery", 
        filters={'object': object, 'docstatus': 1, 'sales_invoice': None},
        fields=['name', 'net_weight', 'date', 'truck', 'invoicing_item'])
    for i in invoicable_deliveries:
        doc = frappe.get_doc("Truck Delivery", i['name'])
        doc.sales_invoice = sales_invoice
        doc.save()
    return invoicable_deliveries
    
