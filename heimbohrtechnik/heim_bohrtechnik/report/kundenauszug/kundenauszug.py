# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.pdf import get_pdf

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {'fieldname': "posting_date", 'label': _("Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "voucher_no", 'label': _("Document"), 'fieldtype': "Dynamic Link", 'options': 'voucher_type', 'width': 100},
        {'fieldname': "text", 'label': _("Text"), 'fieldtype': "Data", 'width': 200},
        {'fieldname': "debit", 'label': _("Debit"), 'fieldtype': "Currency", 'options': 'Currency', 'width': 100},
        {'fieldname': "credit", 'label': _("Credit"), 'fieldtype': "Currency", 'options': 'Currency', 'width': 100},
        {'fieldname': "balance", 'label': _("Balance"), 'fieldtype': "Currency", 'options': 'Currency', 'width': 120}
    ]
    
def get_data(filters):
    conditions = ""
    if filters.get("party_type") == "Customer":
        if not filters.get("customer"):
            return []
        else:
            conditions += """ AND `party_type` = "Customer" AND `party` = "{customer}" """.format(customer=filters.get("customer"))
    elif filters.get("party_type") == "Supplier":
        if not filters.get("supplier"):
            return []
        else:
            conditions += """ AND `party_type` = "Supplier" AND `party` = "{supplier}" """.format(supplier=filters.get("supplier"))
        
    sql_query = """
        SELECT 
            `posting_date`, 
            `voucher_no`, 
            `voucher_type`, 
            `debit`, 
            `credit`, 
            `against_voucher`,
            `account_currency` AS `currency`
        FROM `tabGL Entry` 
        WHERE
            `company` = "{company}"
            {conditions}
            /* PLACEHOLDER */
        ORDER BY `posting_date` ASC;
    """.format(company=filters.get("company"), conditions=conditions)
    
    balance = 0
    if filters.get("from_date"):
        balance = get_opening_balance(sql_query, filters.get("from_date"))
        
    transactions = get_transactions(sql_query, filters.get("from_date"), filters.get("to_date"))
    
    for t in transactions:
        balance += (t.get("debit") - t.get("credit"))
        t['balance'] = balance
        if t.get("voucher_type") in ("Sales Invoice", "Purchase Invoice"):
            if t.get("debit") >= 0:
                t['text'] = _("Sales Invoice")
            else:
                t['text'] = _("Return")
        elif t.get("voucher_type") == "Payment Entry":
            t['text'] = "{0} {1} {2}".format(_("Payment Entry"), _("gegen"), t.get("against_voucher") or "")
        else:
           t['text'] = "-"
           
    return transactions
    
def get_transactions(sql_query, from_date, to_date, opening=False):
    date_condition = ""
    if from_date:
        date_condition += """ AND `posting_date` >= "{date}" """.format(date=from_date)
    if to_date:
        date_condition += """ AND `posting_date` {operator} "{date}" """.format(
            date=to_date,
            operator="<" if opening else "<=" 
        )
    
    transactions = frappe.db.sql(sql_query.replace("/* PLACEHOLDER */", date_condition), as_dict=True)
    
    return transactions
    
def get_opening_balance(sql_query, date):
    transactions = get_transactions(sql_query, None, date, opening=True)
    balance = 0
    for t in transactions:
        balance += (t.get("debit") - t.get("credit"))
    return balance

@frappe.whitelist()
def download_pdf(company, party_type=None, customer=None, supplier=None, from_date=None, to_date=None):
    filters = {
        'company': company, 
        'party_type': party_type, 
        'customer': customer if customer else None, 
        'supplier': supplier if supplier else None, 
        'from_date': from_date if from_date else None, 
        'to_date': to_date if to_date else None
    }
    data = get_data(filters)
    
    html = frappe.render_template(
        "heimbohrtechnik/heim_bohrtechnik/report/kundenauszug/account_statement.html", 
        {
            'filters': filters, 
            'data': data
        }
    )
    
    pdf = get_pdf(html)

    frappe.local.response.filename = "Kontoauszug_{0}.pdf".format(customer or supplier)
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
    
    return
