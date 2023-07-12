# Copyright (c) 2021-2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt
import frappe

@frappe.whitelist()
def get_supplier(supplier):
    document = frappe.get_doc("Supplier", supplier)
    return document
