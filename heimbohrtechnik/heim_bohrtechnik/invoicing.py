# Copyright (c) 2023-2024, libracore and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe.utils.file_manager import save_file

INTERMEDIATE_TEXT = "Zwischenkonto für {0}"

"""
Create a purchase invoice for an internal company from a sales invoice
"""
@frappe.whitelist()
def create_pinv_from_sinv(sales_invoice, intracompany_account=False):
    sinv = frappe.get_doc("Sales Invoice", sales_invoice)
    # create mathing purchase invoice
    pinv_company = sinv.customer_name
    pinv_supplier = frappe.get_all("Supplier", 
        filters={'supplier_name': sinv.company}, fields=['name'])[0]['name']
    pinv_cost_center = frappe.get_value("Company", pinv_company, "cost_center")
    # find taxes from supplier record
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
    new_pinv.insert(ignore_permissions=True)
    new_pinv.submit()
    if intracompany_account:
        # create payment records against intracompany account 1199
        pinv_account = frappe.db.sql("""
            SELECT `name`
            FROM `tabAccount`
            WHERE `company` = "{pinv_company}" AND `name` LIKE "1199%";""".format(pinv_company=pinv_company), as_dict=True)
        if len(pinv_account) > 0:
            pinv_jv = frappe.get_doc({
                'doctype': 'Journal Entry',
                'company': pinv_company,
                'posting_date': sinv.posting_date,
                'accounts': [
                    {
                        'account': new_pinv.credit_to,
                        'party_type': 'Supplier',
                        'party': pinv_supplier,
                        'reference_type': 'Purchase Invoice',
                        'reference_name': new_pinv.name,
                        'debit': sinv.outstanding_amount,
                        'debit_in_account_currency': sinv.outstanding_amount
                    },
                    {
                        'account': pinv_account[0]['name'],
                        'credit': sinv.outstanding_amount,
                        'credit_in_account_currency': sinv.outstanding_amount
                    }
                ],
                'user_remark': INTERMEDIATE_TEXT.format(new_pinv.name)
            })
            pinv_jv.insert(ignore_permissions)
            pinv_jv.submit()
        else:
            frappe.log_error("Zwischenkonto 1199% fehlt für Unternehmen {0}".format(pinv_company), "Intracompany-Verrechnung")
        sinv_account = frappe.db.sql("""
            SELECT `name`
            FROM `tabAccount`
            WHERE `company` = "{sinv_company}" AND `name` LIKE "1199%";""".format(sinv_company=sinv.company), as_dict=True)
        if len(sinv_account) > 0:
            sinv_jv = frappe.get_doc({
                'doctype': 'Journal Entry',
                'company': sinv.company,
                'posting_date': sinv.posting_date,
                'accounts': [
                    {
                        'account': sinv.debit_to,
                        'party_type': 'Customer',
                        'party': sinv.customer,
                        'reference_type': 'Sales Invoice',
                        'reference_name': sinv.name,
                        'credit': sinv.outstanding_amount,
                        'credit_in_account_currency': sinv.outstanding_amount
                    },
                    {
                        'account': sinv_account[0]['name'],
                        'debit': sinv.outstanding_amount,
                        'debit_in_account_currency': sinv.outstanding_amount
                    }
                ],
                'user_remark': INTERMEDIATE_TEXT.format(sinv.name)
            })
            sinv_jv.insert(ignore_permissions=True)
            sinv_jv.submit()
        else:
            frappe.log_error("Zwischenkonto 1199% fehlt für Unternehmen {0}".format(sinv.company), "Intracompany-Verrechnung")
            
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
    
    jv_matches = frappe.get_all("Journal Entry",
        filters={
            'user_remark': INTERMEDIATE_TEXT.format(sinv.name),
            'docstatus': 1,
            'posting_date': sinv.posting_date
        },
        fields=['name'])
    for jv in jv_matches:
        jv_doc = frappe.get_doc("Journal Entry", jv['name'])
        jv_doc.cancel()
            
    pinv_supplier = frappe.get_all("Supplier", 
        filters={'supplier_name': sinv.company}, fields=['name'])[0]['name']
    matching_pinv = frappe.get_all("Purchase Invoice",
        filters={'supplier': pinv_supplier, 'bill_no': sinv.name, 'docstatus': 1},
        fields=['name'])
    for p in matching_pinv:
        pinv_doc = frappe.get_doc("Purchase Invoice", p['name'])
        pinv_doc.cancel()
        jv_matches = frappe.get_all("Journal Entry",
            filters={
                'user_remark': INTERMEDIATE_TEXT.format(pinv_doc.name),
                'docstatus': 1,
                'posting_date': pinv_doc.posting_date
            },
            fields=['name'])
        for jv in jv_matches:
            jv_doc = frappe.get_doc("Journal Entry", jv['name'])
            jv_doc.cancel()
        
    return
