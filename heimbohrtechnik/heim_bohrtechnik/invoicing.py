# Copyright (c) 2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils.file_manager import save_file

"""
Create a purchase invoice for an internal company from a sales invoice
"""
@frappe.whitelist()
def create_pinv_from_sinv(sales_invoice):
    sinv = frappe.get_doc("Sales Invoice", sales_invoice)
    # create mathing purchase invoice
    pinv_company = sinv.customer_name
    pinv_supplier = frappe.get_all("Supplier", 
        filters={'supplier_name': sinv.company}, fields=['name'])[0]['name']
    pinv_cost_center = frappe.get_value("Company", pinv_company, "cost_center")
    # find taxes from customer record
    pinv_tax_templates = frappe.get_all('Party Account', 
        filters={'parent': pinv_supplier, 'company': pinv_company},
        fields=['default_purchase_taxes_and_charges'])
    if pinv_tax_templates and len(pinv_tax_templates) > 0:
        pinv_tax_template = pinv_tax_templates[0]['default_purchase_taxes_and_charges']
    else:
        pinv_tax_template = None
    # create new purchase invoice
    new_pinv = frappe.get_doc({
        'doctype': 'Purchase Invoice',
        'company': pinv_company,
        'supplier': pinv_supplier,
        'bill_no': sinv.name,
        'bill_date': sinv.posting_date,
        'due_date': sinv.due_date,
        'object': sinv.object,
        'project': sinv.project,
        'cost_center': pinv_cost_center,
        'taxes_and_charges': pinv_tax_template,
        'disable_rounded_total': 1
    })
    # add item positions
    for i in sinv.items:
        new_pinv.append('items', {
            'item_code': i.item_code,
            'qty': i.qty,
            'description': i.description,
            'rate': i.rate,
            'cost_center': pinv_cost_center
        })
    # apply taxes
    if pinv_tax_template:
        pinv_tax_details = frappe.get_doc("Purchase Taxes and Charges Template", pinv_tax_template)
        for t in pinv_tax_details.taxes:
            new_pinv.append('taxes', {
                'charge_type': t.charge_type,
                'account_head': t.account_head,
                'description': t.description,
                'rate': t.rate
            })
    # insert
    new_pinv.insert()
    # new_pinv.submit()     # only accounting will submit invoices
    frappe.db.commit()
    # create pdf attachments
    try:
        # create pdf
        html = frappe.get_print("Sales Invoice", sales_invoice)
        pdf = frappe.utils.pdf.get_pdf(html)
        save_file("{sales_invoice}.pdf".format(sales_invoice=sales_invoice), pdf, "Purchase Invoice", new_pinv.name, is_private=True)
    except Exception as err:
        frappe.log_error("Unable to attach pdf: {0}".format(err), "Create purchase invoice from sales invoice {0}".format(object))
    return new_pinv.name

"""
Cancel a purchase invoice from an internal supplier
"""
@frappe.whitelist()
def cancel_related_pinv(sales_invoice):
    sinv = frappe.get_doc("Sales Invoice", sales_invoice)
    pinv_supplier = frappe.get_all("Supplier", 
        filters={'supplier_name': sinv.company}, fields=['name'])[0]['name']
    matching_pinv = frappe.get_all("Purchase Invoice",
        filters={'supplier': pinv_supplier, 'bill_no': sinv.name, 'docstatus': 1},
        fields=['name'])
    for p in matching_pinv:
        pinv_doc = frappe.get_doc("Purchase Invoice", p['name'])
        pinv_doc.cancel()
        
    return
