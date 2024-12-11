from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Sales"),
            "icon": "fa fa-tools",
            "items": [
                {
                   "type": "doctype",
                   "name": "Customer",
                   "label": _("Customer"),
                   "description": _("Customer")
                },
                {
                   "type": "doctype",
                   "name": "Item",
                   "label": _("Item"),
                   "description": _("Item")
                },
                {
                   "type": "doctype",
                   "name": "Quotation",
                   "label": _("Quotation"),
                   "description": _("Quotation")
                },
                {
                   "type": "doctype",
                   "name": "Sales Order",
                   "label": _("Sales Order"),
                   "description": _("Sales Order")
                },
                {
                   "type": "doctype",
                   "name": "Sales Invoice",
                   "label": _("Sales Invoice"),
                   "description": _("Sales Invoice")
                }
            ]
        },
        {
            "label": _("Buying"),
            "icon": "fa fa-tools",
            "items": [
                {
                   "type": "doctype",
                   "name": "Supplier",
                   "label": _("Supplier"),
                   "description": _("Supplier")
                },
                {
                   "type": "doctype",
                   "name": "Request for Quotation",
                   "label": _("Request for Quotation"),
                   "description": _("Request for Quotation")
                },
                {
                   "type": "doctype",
                   "name": "Supplier Quotation",
                   "label": _("Supplier Quotation"),
                   "description": _("Supplier Quotation")
                },
                {
                   "type": "doctype",
                   "name": "Purchase Order",
                   "label": _("Purchase Order"),
                   "description": _("Purchase Order")
                },
                {
                   "type": "doctype",
                   "name": "Purchase Receipt",
                   "label": _("Purchase Receipt"),
                   "description": _("Purchase Receipt")
                },
                {
                   "type": "doctype",
                   "name": "Purchase Invoice",
                   "label": _("Purchase Invoice"),
                   "description": _("Purchase Invoice")
                }
            ]
        },
        {
            "label": _("Manufacturing"),
            "icon": "fa fa-tools",
            "items": [
                {
                   "type": "doctype",
                   "name": "Item",
                   "label": _("Item"),
                   "description": _("Item")
                },
                {
                   "type": "doctype",
                   "name": "BOM",
                   "label": _("BOM"),
                   "description": _("BOM")
                }
            ]
        },
        {
            "label": _("Settings"),
            "icon": "fa fa-tools",
            "items": [
                {
                   "type": "doctype",
                   "name": "HPT Settings",
                   "label": _("HPT Settings"),
                   "description": _("HPT Settings")
                },
                {
                   "type": "doctype",
                   "name": "Probe",
                   "label": _("Probe"),
                   "description": _("Probe")
                },
                {
                   "type": "doctype",
                   "name": "Brand",
                   "label": _("Brand"),
                   "description": _("Brand")
                },
                {
                   "type": "doctype",
                   "name": "Pressure Level",
                   "label": _("Pressure Level"),
                   "description": _("Pressure Level")
                },
                {
                   "type": "doctype",
                   "name": "Raw Material",
                   "label": _("Material"),
                   "description": _("Material")
                },
            ]
        }
    ]
