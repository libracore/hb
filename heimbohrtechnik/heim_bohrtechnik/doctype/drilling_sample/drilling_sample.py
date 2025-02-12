# -*- coding: utf-8 -*-
# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class DrillingSample(Document):
	pass

@frappe.whitelist(allow_guest=True)
def fetch_project_data(project_name):
	project_data = {}
	project = frappe.get_doc("Project", project_name)
	project_data["expected_start_date"] = project.expected_start_date
	project_data["expected_end_date"] = project.expected_end_date

	object_data = frappe.get_doc("Object", project.object)
	project_data["object"] = object_data.name

	address = object_data.object_street + ", " + object_data.plz + " " + object_data.city
	project_data["address"] = address

	geology_office_addresses = object_data.addresses
	for address in geology_office_addresses:
		if address.address_type == "Geologe":
			split_address = address.address_display.split("<br>")
			if len(split_address) == 5:
				address_string = split_address[1] + ", " + split_address[2] + ", " + split_address[3]
			else:
				address_string = split_address[1] + ", " + split_address[2]
			project_data["geology_office"] = address_string
			project_data["geology_office_name"] = split_address[0]
	return project_data