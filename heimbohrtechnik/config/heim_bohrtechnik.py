from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
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
                   "name": "Supplier",
                   "label": _("Supplier"),
                   "description": _("Supplier")
                },
                {
                   "type": "doctype",
                   "name": "Object",
                   "label": _("Object"),
                   "description": _("Object")
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
            "label": _("Planning"),
            "icon": "fa fa-bank",
            "items": [
                {
                   "type": "page",
                   "name": "drill-planner",
                   "label": _("Drill Planner"),
                   "description": _("Drill Planner")
                },
                {
                   "type": "doctype",
                   "name": "Project",
                   "label": _("Project"),
                   "description": _("Project")
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
            "label": _("Settings"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "doctype",
                   "name": "Drilling Team",
                   "label": _("Drilling Team"),
                   "description": _("Drilling Team")
                },
                {
                   "type": "doctype",
                   "name": "Drilling Equipment",
                   "label": _("Drilling Equipment"),
                   "description": _("Drilling Equipment")
                },
                {
                   "type": "doctype",
                   "name": "Permit Type",
                   "label": _("Permit Type"),
                   "description": _("Permit Type")
                },
                {
                   "type": "doctype",
                   "name": "Checklist Activity",
                   "label": _("Checklist Activity"),
                   "description": _("Checklist Activity")
                },
                {
                   "type": "doctype",
                   "name": "Drilling Type",
                   "label": _("Drilling Type"),
                   "description": _("Drilling Type")
                },
                {
                   "type": "doctype",
                   "name": "Pressure Level",
                   "label": _("Pressure Level"),
                   "description": _("Pressure Level")
                },
                {
                   "type": "doctype",
                   "name": "BKP Group",
                   "label": _("BKP Group"),
                   "description": _("BKP Group")
                },
                {
                   "type": "doctype",
                   "name": "Raw Material",
                   "label": _("Raw Material"),
                   "description": _("Raw Material")
                },
                {
                   "type": "doctype",
                   "name": "Heim Settings",
                   "label": _("Heim Settings"),
                   "description": _("Heim Settings")
                }
            ]
        }
    ]
