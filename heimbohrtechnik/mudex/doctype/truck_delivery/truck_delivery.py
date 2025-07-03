# -*- coding: utf-8 -*-
# Copyright (c) 2021-2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime
from erpnextswiss.erpnextswiss.attach_pdf import attach_pdf, execute
from frappe.utils.file_manager import add_attachments
from heimbohrtechnik.heim_bohrtechnik.invoicing import create_pinv_from_sinv

PH_ITEMS = {
    '11': '2.01.01.05',
    '9': '2.01.01.04'
}

class TruckDelivery(Document):
    def on_submit(self): 
        if self.net_weight < 1:
            frappe.throw( _("There is no valid weight recorded."), _("No weight") )
        
        # check and hook into ph Sensor
        ph_sensor_name = frappe.get_value("MudEx Settings", "MudEx Settings", "default_ph_sensor")
        if ph_sensor_name:
            frappe.db.sql("""
                UPDATE `tabpH Sensor`
                SET `update_dt` = "{dt}", `update_dn` = "{dn}"
                WHERE `name` = "{name}";
                """.format(dt=self.doctype, dn=self.name, name=ph_sensor_name)
            )
            frappe.db.commit()
        return
    
    def before_save(self):
        # assure value range of pH
        if self.ph > 14:
            self.ph = 14
        elif self.ph < 0:
            self.ph = 0
        return
        
    def validate(self):
        # compute unallocated weight
        unallocated_weight = self.net_weight
        for o in self.objects:
            unallocated_weight -= o.weight or 0
        # allocate remainder to last row
        if len(self.objects) < 1:
            frappe.throw( _("Please provide an object"), _("Object missing") )
        self.objects[-1].weight = (self.objects[-1].weight or 0) + unallocated_weight
        # collection information mails
        objects = []
        for o in self.objects:
            if o.object:
                objects.append("'{0}'".format(o.object))
        objects = ", ".join(objects)
        self.information_email = get_object_information_email(objects)
        return

"""
Create an invoice from all open positions of an object
"""
@frappe.whitelist()
def create_invoice(object):
    config = frappe.get_doc("MudEx Settings", "MudEx Settings")
    # find customer: either from Project/Object or default
    # check if there is a project
    projects = frappe.get_all("Project", filters={'object': object}, fields=['name'])
    if len(projects) > 0:
        # use project checklist
        o = frappe.get_doc("Project", projects[0]['name'])
    else:
        # use object checklist
        o = frappe.get_doc("Object", object)
    customer = config.default_customer_for_mud
    for c in o.checklist:
        if c.activity == config.mud_activity:
            if c.invoice_to:
                customer = c.invoice_to
    # find taxes from customer record
    tax_templates = frappe.get_all('Party Account', 
        filters={'parent': customer, 'company': config.company},
        fields=['default_sales_taxes_and_charges'])
    if tax_templates and len(tax_templates) > 0:
        tax_template = tax_templates[0]['default_sales_taxes_and_charges']
    else:
        # fallback to default tax template
        default_tax_template = frappe.get_all('Sales Taxes and Charges Template', 
            filters={'is_default': 1, 'company': config.company},
            fields=['name'])
        if len(default_tax_template) > 0:
            tax_template = default_tax_template[0]['name']
        else:
            tax_template = None
    # set default cost center from company
    cost_center = frappe.get_value("Company", config.company, "cost_center")
    # get project link
    if frappe.db.exists("Project", object):
        project = object
    else:
        project = None
    # create new invoice
    new_sinv = frappe.get_doc({
        'doctype': 'Sales Invoice',
        'company': config.company,
        'customer': customer,
        'object': object,
        'taxes_and_charges': tax_template,
        'tax_id': frappe.get_value("Customer", customer, "tax_id"),
        'cost_center': cost_center,
        # 'project': project,               # do not link to project, as project customer is end customer (will create a validation error)
        'naming_series': 'RE-MX-.YY.#####',
        'title': 'Rechnung'
    })
    # apply taxes
    if tax_template:
        tax_details = frappe.get_doc("Sales Taxes and Charges Template", tax_template)
        for t in tax_details.taxes:
            new_sinv.append('taxes', {
                'charge_type': t.charge_type,
                'account_head': t.account_head,
                'description': t.description,
                'rate': t.rate
            })
    # get deliveries and add as positions
    invoiceable_deliveries = get_deliveries(object)
    if invoiceable_deliveries and len(invoiceable_deliveries) > 0:
        # fetch mud type - item data
        mud_type_items = frappe.get_all("Truck Load Type", fields=['title', 'item'])
        mud_type_map = {}
        for m in mud_type_items:
            mud_type_map[m['title']] = m['item']
        # append invoice positions
        for i in invoiceable_deliveries:
            d = i['date']                       # datetime.strptime(str(i['date'])[:19], "%Y-%m-%d %H:%M:%S")
            new_sinv.append('items', {
                'item_code': mud_type_map[i['load_type']],
                'qty': i['weight'] / 1000,
                'description': "{date}: {truck}, pH: {ph:.2f}".format(
                    date=d.strftime("%d.%m.%Y, %H:%M"), truck=i['truck'], ph=i['ph']),
                'truck_delivery': i['delivery'],
                'truck_delivery_detail': i['detail'],
                'cost_center': cost_center
            })
            # add markups in case of increased pH
            if i['ph'] >= 9:
                new_sinv.append('items', {
                    'item_code': PH_ITEMS['11'] if i['ph'] >= 11 else PH_ITEMS['9'],
                    'qty': i['weight'] / 1000,
                    'description': "pH-Zuschlag",
                    'cost_center': cost_center
                })
            
            
        # insert the new sales invoice
        new_sinv.insert()
        # submit directly internal/default customer
        if customer == config.default_customer_for_mud:
            new_sinv.submit()
            # create mathing purchase invoice
            create_pinv_from_sinv(new_sinv.name, intracompany_account=1199)
            # create pdf attachments
            try:
                # use execute instead of attach_pdf to make it sync for the subsequent doc
                execute("Sales Invoice", new_sinv.name, lang="de", title=new_sinv.title, print_format=config.sales_invoice_print_format)
                frappe.db.commit()
                attached_file = frappe.get_all("File", 
                    filters={'attached_to_name': new_sinv.name, 'attached_to_doctype': "Sales Invoice"},
                    fields=['name']) 
            except Exception as err:
                frappe.log_error("Unable to attach pdf: {0}".format(err), "Truck delivery document creation {0}".format(object))
        elif customer == "K-19985":
            # special conditions
            if frappe.db.exists("Pricing Rule", "Toni Transport"):
                special_rate = frappe.get_value("Pricing Rule", "Toni Transport", "rate")
            else:
                special_rate = 45
            new_sinv.ignore_pricing_rule = 1
            for i in new_sinv.items:
                if i.truck_delivery:
                    if "MudEX" in frappe.db.get_value("Truck Delivery", i.truck_delivery, "truck_owner"):
                        i.rate = 0
                    else:
                        i.rate = special_rate
            new_sinv.save()
            
        return new_sinv.name
    else:
        frappe.throw( _("Nothing to invoice") )

"""
Use this function to get all deliveries to be invoiced
"""
@frappe.whitelist()
def get_deliveries(object):
    sql_query = """SELECT `tabTruck Delivery Object`.`name` AS `detail`, 
            `tabTruck Delivery`.`name` AS `delivery`, 
            `tabTruck Delivery Object`.`weight` AS `weight`,
            `tabTruck Delivery`.`truck` AS `truck`,
            `tabTruck Delivery`.`date` AS `date`,
            `tabTruck Delivery`.`load_type` AS `load_type`,
            `tabTruck Delivery`.`ph` AS `ph`
        FROM `tabTruck Delivery Object`
        LEFT JOIN `tabTruck Delivery` ON `tabTruck Delivery`.`name` = `tabTruck Delivery Object`.`parent`
        LEFT JOIN `tabSales Invoice Item` ON 
            (`tabTruck Delivery Object`.`name` = `tabSales Invoice Item`.`truck_delivery_detail`
             AND `tabSales Invoice Item`.`docstatus` = 1)
        WHERE `tabTruck Delivery`.`docstatus` = 1
          AND `tabTruck Delivery Object`.`object` = "{object}"
          AND `tabSales Invoice Item`.`name` IS NULL
        ORDER BY `tabTruck Delivery`.`date` ASC;""".format(object=object)
    invoicable_deliveries = frappe.db.sql(sql_query, as_dict=True)
    return invoicable_deliveries

@frappe.whitelist()
def has_invoiceable_mud(object):
    invoiceable_deliveries = get_deliveries(object)
    if invoiceable_deliveries and len(invoiceable_deliveries) > 0:
        return True
    else:
        return False

def get_object_information_email(objects):
    mud_activity = frappe.get_value("MudEx Settings", "MudEx Settings", "mud_activity")
    sql_query = """SELECT GROUP_CONCAT(`information_to`) AS `information_email`
        FROM `tabProject Checklist`
        WHERE `parent` IN ({objects})
          AND `activity` = "{activity}";""".format(objects=objects, activity=mud_activity)
    #frappe.throw(sql_query)
    data = frappe.db.sql(sql_query, as_dict=True)
    if data and len(data) > 0:
        return data[0]['information_email']
    else:
        return None
