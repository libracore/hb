from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("MudEx"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "doctype",
                   "name": "Truck Delivery",
                   "label": _("Truck Delivery"),
                   "description": _("Truck Delivery")
                },
                {
                   "type": "doctype",
                   "name": "Truck Planning",
                   "label": _("Truck Planning"),
                   "description": _("Truck Planning")
                },
                {
                   "type": "doctype",
                   "name": "Truck Scale",
                   "label": _("Truck Scale"),
                   "description": _("Truck Scale")
                },
                {
                   "type": "doctype",
                   "name": "pH Sensor",
                   "label": _("pH Sensor"),
                   "description": _("pH Sensor")
                },
                {
                    "type": "report",
                    "name": "Mud to invoice",
                    "doctype": "Truck Delivery",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Mud per Week",
                    "doctype": "Truck Delivery",
                    "is_query_report": True,
                }
            ]
        },
        {
            "label": _("Core Data"),
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
                   "name": "Truck",
                   "label": _("Truck"),
                   "description": _("Truck")
                },
                {
                   "type": "doctype",
                   "name": "Supplier",
                   "label": _("Supplier"),
                   "description": _("Supplier")
                },
                {
                   "type": "doctype",
                   "name": "Object",
                   "label": _("Object"),
                   "description": _("Object")
                },
                {
                   "type": "doctype",
                   "name": "Item",
                   "label": _("Item"),
                   "description": _("Item")
                }
            ]
        },
        {
            "label": _("Selling"),
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
            "label": _("Banking"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "page",
                   "name": "bank_wizard",
                   "label": _("Bank Wizard"),
                   "description": _("Bank Wizard")
                },
                {
                   "type": "doctype",
                   "name": "Payment Proposal",
                   "label": _("Payment Proposal"),
                   "description": _("Payment Proposal")
                },
                {
                    "type": "report",
                    "name": "General Ledger",
                    "doctype": "GL Entry",
                    "is_query_report": True,
                }
            ]
        },
        {
            "label": _("Banking"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "doctype",
                   "name": "MudEx Settings",
                   "label": _("MudEx Settings"),
                   "description": _("MudEx Settings")
                }
            ]
        }
    ]
