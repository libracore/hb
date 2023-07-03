# Copyright (c) 2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

import frappe

PAYMENT_ACCOUNTS = {
    "HEIM Bohrtechnik AG": {
        "Firmenkreditkarte": "2105 - UBS Visa-Konto - HBAG",
        "Tankkarte": "106 - Tankkartenkonto - HBAG"
    }
}

def submit(exp, event):
    accounts = []
    total_pretax = 0.0
    # collect expense deductions from pretax
    for expense in exp.expenses:
        if expense.vat_included > 0:
            expense_accounts = get_expense_type_accounts(expense.expense_type, exp.company)
            if expense_accounts:
                # pretax account
                accounts.append({
                    'account': expense_accounts['pretax_account'],
                    'debit_in_account_currency': expense.vat_included
                })
                accounts.append({
                    'account': expense_accounts['default_account'],
                    'credit_in_account_currency': expense.vat_included
                })
                if expense.payment != "Bar":
                    # add expense
                    accounts.append({
                        'account': expense_accounts['default_account'],
                        'debit_in_account_currency': expense.amount
                    })
                    accounts.append({
                        'account': PAYMENT_ACCOUNTS[exp.company][expense.payment],
                        'credit_in_account_currency': expense.amount
                    })
                    

    # create new journal entry
    jv = frappe.get_doc({
        'doctype': 'Journal Entry',
        'posting_date': exp.posting_date,
        'company': exp.company,
        'accounts': accounts,
        'cheque_no': exp.name,
        'cheque_date': exp.posting_date,
        'user_remark': "Pretax on expanse claim {0}".format(exp.name) 
    })
    # insert journal entry
    new_jv = jv.insert()
    new_jv.submit()
    # link journal entry to expense claim
    exp.journal_entry = new_jv.name
    exp.save()
    frappe.db.commit()
    return new_jv
    
def cancel(exp, event):
    # get journal entry
    if not frappe.db.exists("Journal Entry", exp.journal_entry):
        return None
    jv = frappe.get_doc("Journal Entry", exp.journal_entry)
    # cancel
    jv.cancel()
    frappe.db.commit()
    return jv.name

def get_expense_type_accounts(expense_type, company):
    accounts = frappe.db.sql("""
        SELECT `default_account`, `pretax_account`
        FROM `tabExpense Claim Account`
        WHERE `parent` = "{expense_type}"
          AND `parenttype` = "Expense Claim Type"
          AND `company` = "{company}";
    """.format(company=company, expense_type=expense_type), as_dict=True)
    if len(accounts) > 0:
        return accounts[0]
    else:
        return None
