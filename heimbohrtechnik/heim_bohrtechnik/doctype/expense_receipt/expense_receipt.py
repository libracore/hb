# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext import get_default_company

class ExpenseReceipt(Document):
        
    def on_submit(self):
        # create journal entry
        multi_currency = 0
        if self.currency != "CHF":
            multi_currency = 1
            
        jv = frappe.get_doc({
            'doctype': 'Journal Entry',
            'multi_currency': multi_currency,
            'posting_date': self.date,
            'user_remark': "{0} ({1})".format(
                self.remarks or "Spesen {0}".format(self.employee_name),
                self.name),
            'company': get_default_company()
        })
        jv.append("accounts", {
            'account': self.expense_account,
            'debit_in_account_currency': (self.amount - self.vst),
        })
        if self.vst != 0:
            jv.append("accounts", {
                'account': self.vat_account,
                'debit_in_account_currency': self.vst,
            })
        mode_of_payment = frappe.get_doc("Mode of Payment", self.payment)
        account = None
        for a in mode_of_payment.accounts:
            if a.company == get_default_company():
                account = a.default_account
                
        jv.append("accounts", {
            'account': account,
            'credit_in_account_currency': self.amount,
        })
        jv.insert()
        jv.submit()
        self.journal_entry = jv.name
        self.save()
        frappe.db.commit()
        return
        
    def on_cancel(self):
        if self.journal_entry:
            jv = frappe.get_doc("Journal Entry", self.journal_entry)
            if jv.docstatus == 1:
                jv.cancel()
                frappe.db.commit()
        return
        
    
