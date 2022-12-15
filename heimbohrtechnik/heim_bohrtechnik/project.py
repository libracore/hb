# Copyright (c) 2019-2022, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_url_to_form

def before_save(self, method):
    # perform checklist controls
    if self.checklist:
        for c in self.checklist:
            # define trough count/size in case of internal troughs
            if c.activity == "Mulde" and c.supplier in ["L-04052", "L-81511"]:
                c.trough_count = 1
                c.trough_size = "±25m³"
            
            # set trough and mud date
            if c.activity in ["Mulde", "Schlammentsorgung"]:
                c.appointment = self.expected_start_date

    return
    
@frappe.whitelist()
def split_project(project):
    new_project = frappe.copy_doc(frappe.get_doc("Project", project), ignore_no_copy = False)
    if new_project.project_name[-2:-1] == "-":
        new_project.project_name = "{0}-{1}".format(new_project.project_name[:-2],
            (int(new_project.project_name[-1:]) + 1))
    else:
        new_project.project_name += "-1"
    new_project.save()
    frappe.db.commit()
    return {'project': new_project.name, 'uri': get_url_to_form("Project", new_project.name)}

@frappe.whitelist()
def mark_as_sent(project):
    p_doc = frappe.get_doc("Project", project)
    p_doc.drill_notice_sent = 1
    p_doc.save()
    frappe.db.commit()
    return

@frappe.whitelist()
def mark_trough_as_ordered(project):
    p_doc = frappe.get_doc("Project", project)
    p_doc.trough_ordered = 1
    p_doc.save()
    frappe.db.commit()
    return
