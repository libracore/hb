# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

@frappe.whitelist(allow_guest=True)
def store_measurement(measurement):
    frappe.log_error("{0}".format(measurement))
    return "Thanks"
    
