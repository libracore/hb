# -*- coding: utf-8 -*-
# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint

class HPTReportFile(Document):
    pass

@frappe.whitelist()
def get_hpt_reports(project, device_type=None, passed=None):
    filters = {'project': project}
    if device_type:
        filters['device_type'] = device_type
    if passed:
        filters['passed'] = cint(passed)
    
    reports = frappe.get_all("HPT Report File", filters=filters, fields=['name', 'file_name', 'project', 'hole_id', 'report_name', 'file_id'])
    
    return reports
