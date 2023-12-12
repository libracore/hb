# Copyright (c) 2019-2023, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_url_to_form, cint
from heimbohrtechnik.heim_bohrtechnik.utils import clone_attachments

own_trough_supplier = "L-04052"         # when switching to an internal trough team, use this internal trough
mud_from_trough = "L-03749"             # if this supplier is set for the mud, do not override trough

def before_save(self, method):
    # perform checklist controls
    if self.checklist:
        for c in self.checklist:
            # define trough count/size in case of internal troughs
            if c.activity == "Mulde" and c.supplier in [own_trough_supplier, "L-81511"]:
                c.trough_count = 1
                c.trough_size = "±25m³"
            
            # set trough and mud date
            if c.activity in ["Mulde", "Schlammentsorgung"]:
                c.appointment = self.expected_start_date

    # check if the drilling team has an internal trough
    if self.drilling_team and self.object:
        if cint(frappe.get_value("Drilling Team", self.drilling_team, "has_trough")):
            # drilling team has a trought: set internal
            if self.checklist:
                set_internal_trough = False
                for c in range(0, len(self.checklist)):
                    if self.checklist[c].activity == "Mulde":
                        set_internal_trough = c
                    elif self.checklist[c].activity == "Schlammentsorgung" and self.checklist[c].supplier == mud_from_trough:
                        set_internal_trough = False
                if set_internal_trough:
                    self.checklist[set_internal_trough].supplier = own_trough_supplier
                    self.checklist[set_internal_trough].supplier_name = frappe.get_value("Supplier", own_trough_supplier, "supplier_name")
                    
                        
        else:
            # if possible, revert to external trough supplier
            supplier = None
            object_trough_supplier = frappe.db.sql("""
                SELECT `party`, `party_name`
                FROM `tabObject Address`
                WHERE `parent` = "{obj}"
                  AND `address_type` = "Mulde"
                  AND `party` IS NOT NULL
                """.format(obj=self.object), as_dict=True)
            if len(object_trough_supplier) > 0:
                if self.checklist:
                    for c in self.checklist:
                        if c.activity == "Mulde":
                            c.supplier = object_trough_supplier[0]['party']
                            c.supplier_name = object_trough_supplier[0]['party_name']
    
    # butgfix: prevent 0 to null conversions
    if cint(self.actual_time) == 0:
        self.actual_time = 0
    if cint(self.total_costing_amount) == 0:
        self.total_costing_amount = 0
    if cint(self.total_expense_claim) == 0:
        self.total_expense_claim = 0
    if cint(self.total_billable_amount) == 0:
        self.total_billable_amount = 0
        
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
    clone_attachments("Project", project, "Project", new_project.name)
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
