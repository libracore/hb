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
# app_include_css = "/assets/heimbohrtechnik/css/heimbohrtechnik.css"
# app_include_js = "/assets/heimbohrtechnik/js/heimbohrtechnik.js"
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
    "Quotation": "public/js/quotation.js",
    "Sales Order": "public/js/sales_order.js",
    "Delivery Note": "public/js/delviery_note.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Project": "public/js/project.js",
    "Item Price": "public/js/item_price.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
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
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"heimbohrtechnik.tasks.all"
# 	],
# 	"daily": [
# 		"heimbohrtechnik.tasks.daily"
# 	],
# 	"hourly": [
# 		"heimbohrtechnik.tasks.hourly"
# 	],
# 	"weekly": [
# 		"heimbohrtechnik.tasks.weekly"
# 	]
# 	"monthly": [
# 		"heimbohrtechnik.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "heimbohrtechnik.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "heimbohrtechnik.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "heimbohrtechnik.task.get_dashboard_data"
# }

# hook for migrate cleanup tasks
after_migrate = [
    'heimbohrtechnik.heim_bohrtechnik.updater.cleanup_languages'
]
