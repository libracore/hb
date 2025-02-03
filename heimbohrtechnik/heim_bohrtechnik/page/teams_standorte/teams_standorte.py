import frappe
from frappe import _

@frappe.whitelist()
def get_teams_and_locations():
    return