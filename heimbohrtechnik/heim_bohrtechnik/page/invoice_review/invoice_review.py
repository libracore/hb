# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# License: AGPL v3. See LICENCE
#

import frappe
from frappe import throw, _
from frappe.desk.form.assign_to import add, clear
from frappe.utils import cint
from datetime import datetime

@frappe.whitelist()
def get_invoices_for_review():
    # find not reviewed purchase invoices
    pinvs = frappe.db.sql("""
        SELECT 
            `tabPurchase Invoice`.`name`,
            `tabPurchase Invoice`.`supplier`,
            `tabPurchase Invoice`.`supplier_name`,
            `tabPurchase Invoice`.`posting_date`,
            `tabPurchase Invoice`.`due_date`,
            `tabPurchase Invoice`.`net_total`,
            `tabPurchase Invoice`.`grand_total`,
            `tabPurchase Invoice`.`currency`,
            `tabPurchase Invoice`.`bill_no`,
            `tabPurchase Invoice`.`total_taxes_and_charges` AS `tax`
        FROM `tabPurchase Invoice`
        WHERE
            `tabPurchase Invoice`.`docstatus` = 0
            AND `tabPurchase Invoice`.`reviewed_by` IS NULL
        ORDER BY `tabPurchase Invoice`.`due_date` ASC, `tabPurchase Invoice`.`name` ASC
        ;
        """.format(), as_dict=True)
    
    # extend atatchments
    for pinv in pinvs:
        pinv['attachments'] = frappe.db.sql("""
            SELECT *
            FROM `tabFile`
            WHERE 
                `attached_to_doctype` = "Purchase Invoice"
                AND `attached_to_name` = "{pinv}"
            ;""".format(pinv=pinv['name']), as_dict=True)
        # reformat values for output
        pinv['posting_date'] = frappe.utils.get_datetime(pinv['posting_date']).strftime("%d.%m.%Y")
        pinv['due_date'] = frappe.utils.get_datetime(pinv['due_date']).strftime("%d.%m.%Y")
        pinv['net_total'] = "{:,.2f}".format(pinv['net_total']).replace(",", "'")
        pinv['grand_total'] = "{:,.2f}".format(pinv['grand_total']).replace(",", "'")
        pinv['tax'] = "{:,.2f}".format(pinv['tax']).replace(",", "'")
        
    return pinvs
    
@frappe.whitelist()
def reviewed(pinv, user):
    add_comment(pinv, _("Review"), _("Reviewed"), user)
    # add review mark
    pinv_doc = frappe.get_doc("Purchase Invoice", pinv)
    pinv_doc.reviewed_by = user
    pinv_doc.reviewed_on = datetime.today()
    pinv_doc.save()
    frappe.db.commit()
    return

def add_comment(pinv, subject, comment, user):
    new_comment = frappe.get_doc({
        'doctype': "Comment",
        'comment_type': "Comment",
        'subject': subject,
        'content': comment,
        'reference_doctype': "Purchase Invoice",
        'reference_name': pinv,
        'modified_by': user,
        'owner': user
    })
    new_comment.insert(ignore_permissions=True)
    frappe.db.commit()
    return
