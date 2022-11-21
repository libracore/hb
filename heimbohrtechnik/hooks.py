# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "heimbohrtechnik"
app_title = "Heim Bohrtechnik"
app_publisher = "libracore AG"
app_description = "ERPNext Apps"
app_icon = "octicon octicon-pulse"
app_color = "#0075b8"
app_email = "info@libracore.com"
app_license = "AGPL"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/heimbohrtechnik/css/heimbohrtechnik.css"
app_include_js = [
    "/assets/heimbohrtechnik/js/heim_common.js"
    ]
# include js, css files in header of web template
# web_include_css = "/assets/heimbohrtechnik/css/heimbohrtechnik.css"
# web_include_js = "/assets/heimbohrtechnik/js/heimbohrtechnik.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Contact": "public/js/contact.js",
    "Customer": "public/js/customer.js",
    "Supplier": "public/js/supplier.js",
    "Quotation": "public/js/quotation.js",
    "Sales Order": "public/js/sales_order.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Purchase Invoice": "public/js/purchase_invoice.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Project": "public/js/project.js",
    "Item": "public/js/item.js",
    "Item Price": "public/js/item_price.js",
    "Payment Reminder": "public/js/payment_reminder.js"
}
doctype_list_js = {
    "Item Price" : "public/js/item_price_list.js"
}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# additional Jinja environment
jenv = {
    "methods": [
        "get_object_reference_address:heimbohrtechnik.heim_bohrtechnik.utils.get_object_reference_address",
        "get_object_address:heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_object_address",
        "get_object_addresses:heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_object_addresses",
        "get_checklist_details:heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_checklist_details",
        "get_permit_details:heimbohrtechnik.heim_bohrtechnik.doctype.object.object.get_permit_details"
    ]
}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#    "Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "heimbohrtechnik.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "heimbohrtechnik.install.before_install"
# after_install = "heimbohrtechnik.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "heimbohrtechnik.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#     "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#     "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Project": {
         "before_save": "heimbohrtechnik.heim_bohrtechnik.project.before_save"
    }
 }

# Scheduled Tasks
# ---------------

scheduler_events = {
#     "all": [
#         "heimbohrtechnik.tasks.all"
#     ],
     "daily": [
         "heimbohrtechnik.heim_bohrtechnik.data_maintenance.link_sales_orders_to_projects",
         "heimbohrtechnik.heim_bohrtechnik.data_maintenance.remove_bohrplaner_prints"
     ]
#     "hourly": [
#         "heimbohrtechnik.tasks.hourly"
#     ],
#     "weekly": [
#         "heimbohrtechnik.tasks.weekly"
#     ]
#     "monthly": [
#         "heimbohrtechnik.tasks.monthly"
#     ]
}

# Testing
# -------

# before_tests = "heimbohrtechnik.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "heimbohrtechnik.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#     "Task": "heimbohrtechnik.task.get_dashboard_data"
# }

# hook for migrate cleanup tasks
after_migrate = [
    'heimbohrtechnik.heim_bohrtechnik.updater.cleanup_languages',
    'heimbohrtechnik.heim_bohrtechnik.updater.assert_kg',
    'heimbohrtechnik.heim_bohrtechnik.updater.diable_prepared_report',
    'heimbohrtechnik.heim_bohrtechnik.updater.create_folder'
]
