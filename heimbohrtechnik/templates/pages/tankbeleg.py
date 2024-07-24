# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import datetime
from frappe.utils import cint, flt
from frappe.utils.file_manager import save_file
import base64

@frappe.whitelist(allow_guest=True)
def insert_receipt(truck, key, date, amount, payment, currency, kilometer, liter, operating_hours=0):
    if not verify_key(truck, key):
        frappe.throw( _("Invalid key") )
    
    receipt = frappe.get_doc({
        'doctype': 'Gas Receipt',
        'date': date,
        'truck': truck,
        'amount': amount,
        'payment': payment,
        'currency': currency,
        'kilometer': kilometer,
        'operating_hours': operating_hours,
        'liter': liter
    })
    try:
        receipt.insert(ignore_permissions=True)
        return receipt.name
    except Exception as err:
        frappe.throw( _("Failed to insert receipt: {0}").format(err) )

    
@frappe.whitelist(allow_guest=True)
def upload_picture(truck, key, receipt, picture_data):
    if not verify_key(truck, key):
        frappe.throw( _("Invalid key") )
    if not frappe.db.exists("Gas Receipt", receipt):
        frappe.throw( _("Receipt not found") )
    
    #base64 decode string
    file_data = picture_data.split(",")[1]
    decoded_data = base64.b64decode(file_data)

    sf = save_file("{receipt}.jpg".format(receipt=receipt), decoded_data, "Gas Receipt", receipt, is_private=1)

    # enable the receipt in the form
    frappe.db.sql("""
        UPDATE `tabGas Receipt`
        SET `image` = "{url}"
        WHERE `name` = "{receipt}"
        """.format(url=sf.file_url, receipt=receipt))

    return sf
    
"""
Check if the provided key is valid
"""
def verify_key(truck, key):
    truck_key = frappe.get_value("Truck", truck, "key")
    if not truck_key or key != truck_key:
        return False
    else:
        return True
