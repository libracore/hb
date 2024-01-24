# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext import get_default_company
from erpnextswiss.erpnextswiss.finance import get_exchange_rate
from frappe.utils import flt, rounded
import json

class ExpenseReceipt(Document):
        
    def on_submit(self):
        # create journal entry
        multi_currency = 0
        exchange_rate = 1
        company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
        if self.currency != company_currency:
            multi_currency = 1
            exchange_rate = get_exchange_rate(from_currency=self.currency, company=self.company, date=self.date)
            
        jv = frappe.get_doc({
            'doctype': 'Journal Entry',
            'multi_currency': multi_currency,
            'posting_date': self.date,
            'user_remark': "{0} ({1})".format(
                self.remarks or "Spesen {0}".format(self.employee_name),
                self.name),
            'company': self.company
        })
        # expense allocation (company currency)
        net_base_amount = rounded((self.amount - self.vst) * exchange_rate, 2)
        jv.append("accounts", {
            'account': self.expense_account,
            'debit_in_account_currency': net_base_amount,
            'debit': net_base_amount,
            'currency': company_currency
        })
        # pretax allocation  (expense currency)
        if self.vst != 0:
            pretax_base_amount = rounded(self.vst * exchange_rate, 2)
            jv.append("accounts", {
                'account': self.vat_account,
                'debit_in_account_currency': self.vst,
                'debit': pretax_base_amount,
                'exchange_rate': exchange_rate,
                'account_currency': self.currency
            })
            
        # credit card allocation
        mode_of_payment = frappe.get_doc("Mode of Payment", self.payment)
        account = None
        for a in mode_of_payment.accounts:
            if a.company == self.company:
                account = a.default_account
        credit_card_currency = frappe.get_cached_value("Account", account, "account_currency")
        base_gross_amount = rounded(self.amount * exchange_rate, 2)
        jv.append("accounts", {
            'account': account,
            'credit_in_account_currency': self.amount if credit_card_currency != company_currency else base_gross_amount,
            'credit': base_gross_amount,
            'exchange_rate': exchange_rate if credit_card_currency != company_currency else 1
        })
        
        # test for currency deviations
        jv.set_total_debit_credit()
        currency_deviation = rounded(jv.total_debit - jv.total_credit, 2)
        if currency_deviation != 0:
            currency_deviation_account = frappe.get_cached_value("Company", self.company, "exchange_gain_loss_account")
            jv.append('accounts', {
                'account': currency_deviation_account,
                'credit': currency_deviation,
                'account_currency': frappe.get_cached_value("Account", currency_deviation_account, "account_currency")
            })

            jv.set_total_debit_credit()
        # insert and submit
        jv.flags.ignore_validate = True
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
        
    
@frappe.whitelist()
def get_unallocated_expenses(payment_method):
    unallocated_expenses = frappe.db.sql("""
        SELECT `name`, `date`, `amount`, `currency`, `remarks`
        FROM `tabExpense Receipt`
        WHERE `docstatus` = 1
          AND `payment` = "{payment_method}"
          AND `purchase_invoice` IS NULL;
    """.format(payment_method=payment_method), as_dict=True)
    return unallocated_expenses

@frappe.whitelist()
def get_allocated_expenses(purchase_invoice):
    allocated_expenses = frappe.db.sql("""
        SELECT `name`, `date`, `amount`, `currency`, `remarks`
        FROM `tabExpense Receipt`
        WHERE `docstatus` = 1
          AND `purchase_invoice` = "{purchase_invoice}";
    """.format(purchase_invoice=purchase_invoice), as_dict=True)
    return allocated_expenses
    
@frappe.whitelist()
def attach_expenses(expenses, purchase_invoice):
    if type(expenses) == str:
        expenses = json.loads(expenses)
    
    for e in expenses:
        expense_receipt = frappe.get_doc("Expense Receipt", e.get("name"))
        expense_receipt.purchase_invoice = purchase_invoice
        expense_receipt.save()
        
    frappe.db.commit()
    return

@frappe.whitelist()
def unattach_expenses(purchase_invoice):
    expenses = get_allocated_expenses(purchase_invoice)
    
    for e in expenses:
        expense_receipt = frappe.get_doc("Expense Receipt", e.get("name"))
        expense_receipt.purchase_invoice = None
        expense_receipt.save()
        
    frappe.db.commit()
    return
