# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import telnetlib
from frappe.utils import cint
from random import randrange 

class TruckScale(Document):
    pass


@frappe.whitelist()
def get_weight(truck_scale):
    try:
        scale = frappe.get_doc("Truck Scale", truck_scale)                  # read settings
        if cint(scale.random_mode) == 1:
            return randrange(1000, 40000)
        connection = telnetlib.Telnet(scale.host, scale.port, timeout=10)   # connect
        if scale.scale_type == "Pfister":
            connection.write(b"XB\r\n")                                     # send get weight command
        response = connection.read_some()                                   # read response
        parts = response.decode('ascii').split("kg")                        # parse response (something like 1234 kg B)
        weight = float(parts[0])
        connection.close()                                                  # close connection
    except Exception as err:
        weight = -1
        frappe.log_error( "{0}".format(err), "Get weight failed")
    return weight
