# -*- coding: utf-8 -*-
# Copyright (c) 2026, libracore and contributors
# For license information, please see license.txt

from tqdm import tqdm
import frappe

"""
Check payment entries and journal entries for missing tax codes

Provide account (1170, 1171, 2200), and desired tax type and name (template)
"""
def extend_tax_codes(account, tax_type, tax_name):
    # find all transactions where the codes is missing, but account pattern matches
    missing_tax_codes = frappe.db.sql("""
        SELECT 
            "Payment Entry" AS `doctype`,
            `tabPayment Entry`.`name` AS `docname`
        FROM `tabPayment Entry`
        LEFT JOIN `tabPayment Entry Deduction` ON `tabPayment Entry Deduction`.`parent` = `tabPayment Entry`.`name`
        WHERE
            `tabPayment Entry`.`taxes_and_charges` IS NULL
            AND `tabPayment Entry Deduction`.`account` = %(account)s
        UNION ALL SELECT 
            "Journal Entry" AS `doctype`,
            `tabJournal Entry`.`name` AS `docname`
        FROM `tabJournal Entry`
        LEFT JOIN `tabJournal Entry Account` ON `tabJournal Entry Account`.`parent` = `tabJournal Entry`.`name`
        WHERE
            `tabJournal Entry`.`taxes_and_charges` IS NULL
            AND `tabJournal Entry Account`.`account` = %(account)s
        ;""",
        {
            'account': account
        },
        as_dict=True
    )
    
    # apply tax template
    for t in tqdm(missing_tax_codes, desc="apply tax template", unit="transaction"):
        frappe.db.sql("""
            UPDATE `tab{doctype}`
            SET 
                `tax_type` = %(tax_type)s,
                `taxes_and_charges` = %(tax_name)s
            WHERE
                `name` = %(docname)s
            ;""".format(doctype=t.get('doctype')),
            {
                'docname': t.get('docname'),
                'tax_type': tax_type,
                'tax_name': tax_name
            }
        )
    
    frappe.db.commit()
    
    return
