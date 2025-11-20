# -*- coding: utf-8 -*-
# Copyright (c) 2021-2025, libracore and contributors
# License: AGPL v3. See LICENCE

import frappe
from frappe import _
import json
import datetime
from frappe.utils import cint, flt

def validate_credentials(truck, customer, key):
    truck = frappe.get_doc("Truck", truck)
    if truck.customer == customer:
        if key == truck.key:
            return True
        else:
            return False
    else:
        return False

@frappe.whitelist(allow_guest=True)
def insert_delivery(truck, customer, full_weight, empty_weight, net_weight, traces, item, key):
    if not validate_credentials(truck, customer, key):
        return {'delivery': 'Invalid Key'}
        
    # prepare values
    trace = json.loads(traces)
    for t in trace:
        t['weight'] = float(t['weight'])
    truck_doc = frappe.get_doc("Truck", truck)
    config = frappe.get_doc("MudEx Settings", "MudEx Settings")
    customer_doc = frappe.get_doc("Customer", customer)
    
    # create new record
    delivery = frappe.get_doc({
        'doctype': 'Delivery Note',
        'company': config.company,
        'posting_date': datetime.datetime.now().date(),
        'posting_time': datetime.datetime.now().time(),
        'customer': customer,
        'customer_name': customer_doc.customer_name,
        'selling_price_list': config.sales_price_list,
        'naming_series': "LS-MX-.YY.#####"
    })
    
    item_doc = frappe.get_doc("Item", item)
    delivery.append("items", {
        'item_code': item,
        'description': """<b>{truck_description} ({truck})</b><br>
            Tara: {tara} kg<br>
            Vollgewicht: {full} kg<br>
            Nettogewicht: {net} kg<br>
            Waage: {scale}""".format(
                truck=truck,
                truck_description=truck_doc.title,
                tara="{:,d}".format(cint(empty_weight)).replace(",", "'"),
                full="{:,d}".format(cint(full_weight)).replace(",", "'"),
                net="{:,d}".format(cint(net_weight)).replace(",", "'"),
                scale=config.default_scale
            ),
        'qty': float(net_weight)
    })
    delivery.set_missing_values()
    delivery = delivery.insert(ignore_permissions=True)
    delivery.submit()
    return {'delivery': delivery.name}
