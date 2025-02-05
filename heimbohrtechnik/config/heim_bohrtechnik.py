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
                },
                {
                   "type": "doctype",
                   "name": "Item",
                   "label": _("Item"),
                   "description": _("Item")
                },
                {
                   "type": "doctype",
                   "name": "Item Price",
                   "label": _("Item Price"),
                   "description": _("Item Price")
                },
                {
                   "type": "doctype",
                   "name": "Pricing Rule",
                   "label": _("Pricing Rule"),
                   "description": _("Pricing Rule")
                },
                {
                    "type": "report",
                    "name": "Pricing Analysis",
                    "doctype": "Item Price",
                    "is_query_report": True
                },
                {
                   "type": "doctype",
                   "name": "Pincode",
                   "label": _("Pincode"),
                   "description": _("Pincode")
                },
                {
                   "type": "doctype",
                   "name": "Parking",
                   "label": _("Parking"),
                   "description": _("Parking")
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
                   "name": "Drilling Request",
                   "label": _("Drilling Request"),
                   "description": _("Drilling Request")
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
                   "name": "Delivery Note",
                   "label": _("Delivery Note"),
                   "description": _("Delivery Note")
                },
                {
                   "type": "doctype",
                   "name": "Sales Invoice",
                   "label": _("Sales Invoice"),
                   "description": _("Sales Invoice")
                },
                {
                    "type": "report",
                    "name": "Offene Akonto-Rechnungen",
                    "doctype": "Sales Invoice",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Sales Pipeline",
                    "doctype": "Customer",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Follow-Up Overview",
                    "doctype": "Quotation",
                    "is_query_report": True,
                },
                {
                   "type": "doctype",
                   "name": "Abo",
                   "label": _("Abo"),
                   "description": _("Abo")
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
                   "description": _("Purchase invoice")
                },
                {
                    "type": "report",
                    "name": "Versicherungsanmeldung",
                    "doctype": "Project",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Sondenbestellung",
                    "doctype": "Project",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Sondenparkplatz",
                    "doctype": "Purchase Order",
                    "is_query_report": True,
                },
                {
                   "type": "doctype",
                   "name": "ZUGFeRD Wizard",
                   "label": _("ZUGFeRD Wizard"),
                   "description": _("ZUGFeRD Wizard")
                },
                {
                   "type": "page",
                   "name": "invoice-review",
                   "label": _("Invoice Review"),
                   "description": _("Invoice Review")
                },
                {
                   "type": "page",
                   "name": "approval-manager",
                   "label": _("Approval Manager"),
                   "description": _("Approval Manager")
                }
            ]
        },
        {
            "label": _("Planning"),
            "icon": "fa fa-bank",
            "items": [
                {
                   "type": "page",
                   "name": "bohrplaner",
                   "label": _("Bohrplaner"),
                   "description": _("Bohrplaner")
                },
                {
                   "type": "doctype",
                   "name": "Project",
                   "label": _("Project"),
                   "description": _("Project")
                },
                {
                   "type": "page",
                   "name": "object-overview",
                   "label": _("Object Overview"),
                   "description": _("Object Overview")
                },
                {
                   "type": "page",
                   "name": "teams-standorte",
                   "label": _("Teams Standorte"),
                   "description": _("Teams Standorte")
                },
                {
                   "type": "doctype",
                   "name": "Bohranzeige",
                   "label": _("Bohranzeige"),
                   "description": _("Bohranzeige")
                },
                {
                   "type": "doctype",
                   "name": "Construction Site Delivery",
                   "label": _("Construction Site Delivery"),
                   "description": _("Construction Site Delivery")
                },
                {
                   "type": "doctype",
                   "name": "Subcontracting Order",
                   "label": _("Subcontracting Order"),
                   "description": _("Subcontracting Order")
                },
                {
                   "type": "doctype",
                   "name": "MFK",
                   "label": _("MFK"),
                   "description": _("MFK")
                },
                {
                    "type": "report",
                    "name": "Road Block List",
                    "doctype": "Request for Public Area Use",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Absperrmaterial",
                    "doctype": "Construction Site Description",
                    "is_query_report": True,
                },
                {
                    "type": "report",
                    "name": "Subcontracting Control",
                    "doctype": "Subcontracting Order",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Impact Analysis",
                    "doctype": "Drilling Move Log",
                    "is_query_report": True
                }
            ]
        },
        {
            "label": _("Finanzbuchhaltung"),
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
                    "name": "General Ledger HBAG",
                    "doctype": "GL Entry",
                    "is_query_report": True,
                },
                {
                   "type": "doctype",
                   "name": "Purchase Invoice",
                   "label": _("Purchase Invoice"),
                   "description": _("Purchase Invoice")
                },
                {
                   "type": "doctype",
                   "name": "Payment Entry",
                   "label": _("Payment Entry"),
                   "description": _("Payment Entry")
                },
                {
                   "type": "doctype",
                   "name": "Journal Entry",
                   "label": _("Journal Entry"),
                   "description": _("Journal Entry")
                },
                {
                   "type": "doctype",
                   "name": "Payment Reminder",
                   "label": _("Payment Reminder"),
                   "description": _("Payment Reminder")
                },
                {
                    "type": "report",
                    "name": "Account Sheets HBAG",
                    "doctype": "GL Entry",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Mahnliste",
                    "doctype": "Sales Invoice",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Kundenauszug",
                    "doctype": "Customer",
                    "label": _("Kunden- und Lieferantenauszug"),
                    "is_query_report": True
                }
            ]
        },
        {
            "label": _("Expense Claims"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "doctype",
                   "name": "Expense Receipt",
                   "label": _("Expense Receipt"),
                   "description": _("Expense Receipt")
                },
                {
                   "type": "doctype",
                   "name": "Gas Receipt",
                   "label": _("Gas Receipt"),
                   "description": _("Gas Receipt")
                },
                {
                   "type": "doctype",
                   "name": "Expense Claim",
                   "label": _("Expense Claim"),
                   "description": _("Expense Claim")
                },
                {
                    "type": "report",
                    "name": "Tankliste",
                    "doctype": "Gas Receipt",
                    "label": _("Tankliste"),
                    "is_query_report": True
                }
            ]
        },
        {
            "label": _("Human Resources"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "doctype",
                   "name": "Employee",
                   "label": _("Employee"),
                   "description": _("Employee")
                },
                {
                   "type": "doctype",
                   "name": "Expense Claim",
                   "label": _("Expense Claim"),
                   "description": _("Expense Claim")
                },
                {
                   "type": "doctype",
                   "name": "Payroll Entry",
                   "label": _("Payroll Entry"),
                   "description": _("Payroll Entry")
                },
                {
                   "type": "doctype",
                   "name": "Salary Slip",
                   "label": _("Salary Slip"),
                   "description": _("Salary Slip")
                },
                {
                   "type": "doctype",
                   "name": "Salary Certificate",
                   "label": _("Salary Certificate"),
                   "description": _("Salary Certificate")
                },
                {
                   "type": "doctype",
                   "name": "Salary Structure Assignment",
                   "label": _("Salary Structure Assignment"),
                   "description": _("Salary Structure Assignment")
                },
                {
                   "type": "doctype",
                   "name": "Salary Structure",
                   "label": _("Salary Structure"),
                   "description": _("Salary Structure")
                },
                {
                   "type": "doctype",
                   "name": "Salary Component",
                   "label": _("Salary Component"),
                   "description": _("Salary Component")
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
                   "name": "Probe Type",
                   "label": _("Probe Type"),
                   "description": _("Probe Type")
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
                   "name": "Signature",
                   "label": _("Signature"),
                   "description": _("Signature")
                },
                {
                   "type": "doctype",
                   "name": "Truck",
                   "label": _("Truck"),
                   "description": _("Truck")
                },
                {
                   "type": "doctype",
                   "name": "Truck Load Type",
                   "label": _("Truck Load Type"),
                   "description": _("Truck Load Type")
                },
                {
                   "type": "doctype",
                   "name": "Drilling Method",
                   "label": _("Drilling Method"),
                   "description": _("Drilling Method")
                },
                {
                   "type": "doctype",
                   "name": "Heim Settings",
                   "label": _("Heim Settings"),
                   "description": _("Heim Settings")
                },
                {
                   "type": "doctype",
                   "name": "Timeshepherd Settings",
                   "label": _("Timeshepherd Settings"),
                   "description": _("Timeshepherd Settings")
                },
                {
                   "type": "doctype",
                   "name": "Email Footer Template",
                   "label": _("Email Footer Template"),
                   "description": _("Email Footer Template")
                },
                {
                   "type": "doctype",
                   "name": "Holiday List",
                   "label": _("Holiday List"),
                   "description": _("Holiday List")
                },
                {
                   "type": "doctype",
                   "name": "Regional Holidays",
                   "label": _("Regional Holidays"),
                   "description": _("Regional Holidays")
                },
                {
                   "type": "doctype",
                   "name": "Subcontracting Order Template",
                   "label": _("Subcontracting Order Template"),
                   "description": _("Subcontracting Order Template")
                },
                {
                   "type": "doctype",
                   "name": "Daily Feedback Description",
                   "label": _("Daily Feedback Description"),
                   "description": _("Daily Feedback Description")
                }
            ]
        },
        {
            "label": _("Evaluations"),
            "icon": "fa fa-money",
            "items": [
                {
                    "type": "report",
                    "name": "Drilling Rate Evaluation",
                    "doctype": "Object",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Artikelzusammenfassung",
                    "doctype": "Item",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Drilling Capacity Overview",
                    "doctype": "Project",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Drilling Review",
                    "doctype": "Project",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Feedback Drilling Meter",
                    "doctype": "Feedback Drilling Meter",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Drilling Statistics",
                    "doctype": "Project",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Project Geographic Optimisation",
                    "doctype": "Project",
                    "is_query_report": True
                },
                {
                    "type": "report",
                    "name": "Customer sales trend",
                    "doctype": "Customer",
                    "is_query_report": True
                }
            ]
        },
        {
            "label": _("Kleidermagazin"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "doctype",
                   "name": "Item",
                   "label": _("Item"),
                   "description": _("Item")
                },
                {
                   "type": "doctype",
                   "name": "Stock Entry",
                   "label": _("Stock Entry"),
                   "description": _("Stock Entry")
                },
                {
                    "type": "page",
                    "name": "stock-balance",
                    "label": _("Stock Summary"),
                    "dependencies": ["Item"],
                },
                {
                    "type": "report",
                    "name": "Materialbezugsliste",
                    "doctype": "Stock Entry",
                    "is_query_report": True
                }
            ]
        },
        {
            "label": _("Maintenance"),
            "icon": "fa fa-money",
            "items": [
                {
                   "type": "doctype",
                   "name": "Maintenance Report",
                   "label": _("Maintenance Report"),
                   "description": _("Maintenance Report")
                },
                {
                    "type": "report",
                    "name": "Maintenance Matrix",
                    "doctype": "Maintenance Report",
                    "is_query_report": True
                }
            ]
        },
        {
            "label": _("Datenpflege"),
            "icon": "fa fa-money",
            "items": [
                {
                    "type": "report",
                    "name": "Objekte ohne GPS-Position",
                    "doctype": "Object",
                    "is_query_report": True
                }
            ]
        }
    ]
