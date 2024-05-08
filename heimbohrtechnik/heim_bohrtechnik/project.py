# Copyright (c) 2019-2023, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_url_to_form, cint
from heimbohrtechnik.heim_bohrtechnik.utils import clone_attachments
from erpnextswiss.scripts.crm_tools import get_primary_supplier_address, get_primary_supplier_contact

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
                set_internal_trough = -1
                for c in range(0, len(self.checklist)):
                    if self.checklist[c].activity == "Mulde":
                        set_internal_trough = c
                    elif self.checklist[c].activity == "Schlammentsorgung" and self.checklist[c].supplier == mud_from_trough:
                        set_internal_trough = -1        # reset in case trough from mud supplier
                if set_internal_trough >= 0:
                    frappe.db.set_value("Object", self.object, "old_trough_supplier", self.checklist[set_internal_trough].supplier, update_modified = False)
                    frappe.db.commit()
                    self.checklist[set_internal_trough].supplier = own_trough_supplier
                    supplier_name = frappe.get_value("Supplier", own_trough_supplier, "supplier_name")
                    self.checklist[set_internal_trough].supplier_name = supplier_name
                    update_object_address(self.object, "Mulde", own_trough_supplier, supplier_name)
        else:
            # verify if an external trough is used
            reset_trough_supplier = False
            if self.checklist:
                for c in self.checklist:
                    if c.activity == "Mulde":
                        if c.supplier == own_trough_supplier:
                            reset_trough_supplier = True
            if reset_trough_supplier:
                # if possible, revert to external trough supplier
                supplier = frappe.get_value("Object", self.object, "old_trough_supplier")
                if supplier:
                    if self.checklist:
                        for c in self.checklist:
                            if c.activity == "Mulde":
                                c.supplier = supplier
                                c.supplier_name = frappe.get_value("Supplier", supplier, "supplier_name")
                                update_object_address(self.object, "Mulde", c.supplier, c.supplier_name)
    
    # bugfix: prevent 0 to null conversions
    if cint(self.actual_time) == 0:
        self.actual_time = 0
    if cint(self.total_costing_amount) == 0:
        self.total_costing_amount = 0
    if cint(self.total_expense_claim) == 0:
        self.total_expense_claim = 0
    if cint(self.total_billable_amount) == 0:
        self.total_billable_amount = 0
        
    return

def update_object_address(object_name, address_type, supplier, supplier_name):
    address_doc = get_primary_supplier_address(supplier)
    contact_doc = get_primary_supplier_contact(supplier)
    frappe.db.sql("""
        UPDATE `tabObject Address`
        SET 
            `party` = "{supplier}",
            `party_name` = "{supplier_name}",
            `address` = "{address}",
            `contact` = "{contact}",
            `address_display` = "{address_display}",
            `contact_name` = "{contact_name}",
            `phone` = "{phone}",
            `email` = "{email}"
        WHERE
            `parent` = "{object_name}"
            AND `parenttype` = "Object"
            AND `address_type` = "{address_type}"
            AND `party` != "{supplier}"     /* restrict: only update */
        ;
        """.format(
            supplier=supplier, 
            supplier_name=supplier_name,
            address=address_doc.name if address_doc else "",
            contact=contact_doc.name if contact_doc else "",
            address_display=get_address_display(address_doc) if address_doc else "",
            contact_name="{0} {1}".format(contact_doc.first_name or "", contact_doc.first_name or "") if contact_doc else "",
            phone=contact_doc.phone if contact_doc else "",
            email=contact_doc.email_id if contact_doc else "",
            object_name=object_name,
            address_type=address_type
        )
    )
    return
            
def get_address_display(address):
    if type(address) == str:
        address = frappe.get_doc("Address", address)
        
    template = frappe.get_all("Address Template", filters={'is_default': 1}, fields=['name', 'template'])
    if not template or len(template) == 0:
        return None
        
    address_display = frappe.render_template(template[0]['template'], address.as_dict())
    
    return address_display
    
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
