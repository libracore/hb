# Copyright (c) 2019-2024, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_url_to_form, cint
from heimbohrtechnik.heim_bohrtechnik.utils import clone_attachments
from erpnextswiss.scripts.crm_tools import get_primary_supplier_address, get_primary_supplier_contact
from datetime import datetime

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
                    if supplier == own_trough_supplier:     # prevent using own trough if this team has none
                        supplier = None
                if self.checklist:
                    for c in self.checklist:
                        if c.activity == "Mulde":
                            c.supplier = supplier
                            if supplier:
                                c.supplier_name = frappe.get_value("Supplier", supplier, "supplier_name")
                                update_object_address(self.object, "Mulde", c.supplier, c.supplier_name)
                            else:
                                c.supplier_name = None
    
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

@frappe.whitelist()
def insurance_application(project):
    # load base data
    project_doc = frappe.get_doc("Project", project)
    if not project_doc.object:
        frappe.throw( _("Objekt fehlt in diesem Projekt") )
    object_doc = frappe.get_doc("Object", project_doc.object)
    if not project_doc.sales_order:
        frappe.throw( _("Kundenauftrag fehlt in diesem Projekt") )
    sales_order_doc = frappe.get_doc("Sales Order", project_doc.sales_order)
    
    # find owner data
    for a in object_doc.addresses:
        if a.address_type == "Eigentümer":
            if a.is_simple:
                address_line = (a.simple_address or "").split(",")
                plz_city = address_line[1].strip() if len(address_line) > 1 else ""
                owner = {
                    'name': a.simple_name,
                    'street': address_line[0],
                    'plz': plz_city[0:4],
                    'city': plz_city[5:],
                    'country': 'CH'
                }
            else:
                if a.address:
                    address = frappe.get_doc("Address", a.address)
                    owner = {
                        'name': a.party_name,
                        'street': address.address_line1,
                        'plz': address.pincode,
                        'city': address.city,
                        'country': frappe.get_value("Country", address.country, "code")
                    }
                else:
                    owner = {
                        'name': "",
                        'street': "",
                        'plz': "",
                        'city': "",
                        'country': 'CH'
                    }
    
    # determine insurance
    insurance = {
        'base_package': 1,
        'cancelation_included': 0,
        'owner_insurance': 0
    }
    for i in sales_order_doc.items:
        if i.item_code == "1.01.04.03":
            insurance['owner_insurance'] = 1
        if "Bohrabbruch-Versicherung" in i.item_name:
            insurance['cancelation_included'] = 1
    
    # determine probes
    probes = {
        'below_250': 0,
        'above_250': 0,
        'count': 0
    }
    for p in object_doc.ews_specification:
        if p.ews_depth >= 250:
            probes['above_250'] += p.ews_count
        else:
            probes['below_250'] += p.ews_count
        probes['count'] += p.ews_count
    
    insurance_form_str = "\t{date}\taktiv\t{project_no}\t{object_name}\t{object_street}\t{plz}\t{city}\t{owner_name}\t{owner_street}\t{owner_plz}\t{owner_city}\t{owner_country}\t{start_date}\t{base_package}\t{drilling_count}\t{cancelation_included}\t{owner_insurance}\t{probes_below_250}\t{probes_above_250}".format(
        date=datetime.now().strftime("%d.%m.%Y"),
        project_no=project_doc.name[2:8],
        object_name=project_doc.object_name,
        object_street=project_doc.object_street,
        plz=project_doc.object_location[0:4],
        city=project_doc.object_location[5:],
        owner_name=owner.get("name"),
        owner_street=owner.get("street"),
        owner_plz=owner.get("plz"),
        owner_city=owner.get("city"),
        owner_country=owner.get("country"),
        start_date=project_doc.expected_start_date.strftime("%d.%m.%Y"),
        base_package="ja/oui" if insurance.get('base_package') else "nein/non",
        drilling_count=probes.get('count'),
        cancelation_included="ja/oui" if insurance.get('cancelation_included') else "nein/non",
        owner_insurance="ja/oui" if insurance.get('owner_insurance') else "nein/non",
        probes_below_250=probes.get('below_250'),
        probes_above_250=probes.get('above_250')
    )
    return insurance_form_str
