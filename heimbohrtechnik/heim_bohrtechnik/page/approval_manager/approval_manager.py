# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore and contributors
# License: AGPL v3. See LICENCE
#

import frappe
from frappe import throw, _
from frappe.desk.form.assign_to import add, clear
from frappe.utils import cint

@frappe.whitelist()
def get_approvals(user):
    # find assigned purchase invoices
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
            `tabPurchase Invoice`.`bill_no`
        FROM `tabToDo`
        LEFT JOIN `tabPurchase Invoice` ON `tabPurchase Invoice`.`name` = `tabToDo`.`reference_name`
        WHERE
            `tabToDo`.`owner` = "{user}"
            AND `tabToDo`.`reference_type` = "Purchase Invoice"
            AND `tabToDo`.`status` = "Open"
        ORDER BY `tabPurchase Invoice`.`due_date` ASC
        ;
        """.format(user=user), as_dict=True)
    
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
        
    return pinvs
    
@frappe.whitelist()
def approve(pinv, is_final, user):
    add_comment(pinv, _("Approval"), _("Approved"), user)
    # clear assignment
    clear("Purchase Invoice", pinv)
    # submit or re-assign
    if cint(is_final):
        # submit document, this is a final approval
        pinv_doc = frappe.get_doc("Purchase Invoice", pinv)
        pinv_doc.submit()
        frappe.db.commit()
    else:
        # final approver
        approvers = frappe.db.sql("""
            SELECT `tabDepartment Approver`.`approver`
            FROM `tabEmployee`
            LEFT JOIN `tabDepartment` ON `tabDepartment`.`name` = `tabEmployee`.`department`
            LEFT JOIN `tabDepartment Approver` ON `tabDepartment Approver`.`parent` = `tabDepartment`.`name`
            WHERE 
                `tabEmployee`.`user_id` = "{user}";
            """.format(user=user), as_dict=True)
        if len(approvers) > 0:
            add({'doctype': 'Purchase Invoice', 'name': pinv, 'assign_to': approvers[0]['approver']})
    return

@frappe.whitelist()
def reject(pinv, user):
    add_comment(pinv, _("Reject"), _("Rejected"), user)
    # clear assignment
    clear("Purchase Invoice", pinv)
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
