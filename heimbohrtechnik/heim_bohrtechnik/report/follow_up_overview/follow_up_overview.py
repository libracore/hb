# Copyright (c) 2023-2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import cint
from frappe.core.doctype.communication.email import make as make_email
import json
from frappe.utils.background_jobs import enqueue

follow_up_mail_content = """
    <p>Sehr geehrte Damen und Herren</p>
    <p><br></p>
    <p>Wir wollten uns erkundigen, ob Sie bereits die Gelegenheit hatten, das Angebot zu prüfen, dass wir Ihnen vor einiger Zeit für das oben genannten Objekt geschickt haben.</p>
    <p><br></p>
    <p>Wenn Sie weitere Einzelheiten über unsere Dienstleistungen benötigen oder das Angebot weiter besprechen möchten, stehen wir Ihnen gerne jederzeit zur Verfügung.</p>
    <p><br></p>
    <p>Wir würden uns freuen, all Ihre Fragen zu beantworten.</p>
    <p><br></p>
    <p><br></p>
    {{footer}}
"""

FOLLOW_UP_DAYS = 21

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data
    
def get_columns(filters):
    columns = [
        {"label": _("Quotation"), "fieldname": "quotation", "fieldtype": "Link", "options": "Quotation", "width": 100},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 80},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        {"label": _("Volume"), "fieldname": "volume", "fieldtype": "Currency", "width": 120},
        {"label": _("Object"), "fieldname": "object", "fieldtype": "Link", "options": "Object", "width": 80},
        {"label": _("Object name"), "fieldname": "object_name", "fieldtype": "Data", "width": 150},
        {"label": _("Angebot seit"), "fieldname": "days_since_quotation", "fieldtype": "Int", "width": 80},
        {"label": _("Nachgefasst seit"), "fieldname": "days_since_fup", "fieldtype": "Int", "width": 80},
        {"label": _("Next Follow Up"), "fieldname": "next_follow_up", "fieldtype": "Date", "width": 80},
        {"label": _("Notes"), "fieldname": "notes", "fieldtype": "Data", "width": 300}
    ]
    return columns
    
def get_data(filters):
    conditions = ""
    if filters.get("volume_from"):
        conditions += """ AND `tabQuotation`.`base_net_total` >= {vol} """.format(vol=filters.get("volume_from"))
    if filters.get("volume_to"):
        conditions += """ AND `tabQuotation`.`base_net_total` <= {vol} """.format(vol=filters.get("volume_to"))
    if filters.get("from_date"):
        conditions += """ AND `tabQuotation`.`transaction_date` >= "{date}" """.format(date=filters.get("from_date"))
    if filters.get("to_date"):
        conditions += """ AND `tabQuotation`.`transaction_date` <= "{date} 23:59" """.format(date=filters.get("to_date"))
    
    data = frappe.db.sql("""
        SELECT
            `tabQuotation`.`name` AS `quotation`,
            `tabQuotation`.`transaction_date` AS `date`,
            `tabQuotation`.`party_name` AS `customer`,
            `tabQuotation`.`customer_name` AS `customer_name`,
            `tabQuotation`.`object` AS `object`,
            `tabQuotation`.`object_name` AS `object_name`,
            `tabQuotation`.`base_net_total` AS `volume`,
            `tabQuotation`.`transaction_date` AS `transaction_date`,
            `tabQuotation`.`valid_till` AS `valid_until_date`,
            `tabQuotation`.`next_follow_up` AS `next_follow_up`,
            (SELECT `tabFollow Up Note`.`name`
             FROM `tabFollow Up Note`
             WHERE `tabFollow Up Note`.`quotation` = `tabQuotation`.`name`
             ORDER BY `tabFollow Up Note`.`date` DESC
             LIMIT 1) AS `follow_up_note`
        FROM `tabQuotation`
        WHERE
            `tabQuotation`.`status` = "Open"
            {conditions}
            /* AND `tabQuotation`.`valid_till` >= CURDATE() */
        ORDER BY `tabQuotation`.`base_net_total` DESC;
    """.format(conditions=conditions),
        as_dict=True)
    
    for d in data:
        d['days_since_quotation'] = (datetime.now().date() - d['transaction_date']).days
        if d.get("follow_up_note"):
            note = frappe.get_doc("Follow Up Note", d.get("follow_up_note"))
            d['notes'] = note.notes
            d['days_since_fup'] = (datetime.now().date() - note.date).days
            
    # if only follow-ups: filter out by date:
    if cint(filters.get("needs_follow_up")):
        filtered_data = []
        for d in data:
            if d['days_since_quotation'] >= 30 and (d.get('days_since_fup') is None or d.get('days_since_fup') >= 30):
                filtered_data.append(d)
                
        data = filtered_data

    return data

@frappe.whitelist()
def async_bulk_follow_up(filters):
    if type(filters) == str:
        filters = json.loads(filters)
    
    kwargs={
      'filters': filters
    }
    
    enqueue("heimbohrtechnik.heim_bohrtechnik.report.follow_up_overview.follow_up_overview.bulk_follow_up",
        queue='short',
        timeout=15000,
        **kwargs)
    return

def bulk_follow_up(filters):
    data = get_data(filters)
    
    for d in data:
        send_follow_up(d.get("quotation"))

    return

def send_follow_up(quotation):
    doc = frappe.get_doc("Quotation", quotation)
    if frappe.session.user == "Administrator":
        footer = frappe.get_cached_value("Signature", doc.owner, "email_footer")
    else:
        footer = frappe.get_cached_value("Signature", frappe.session.user, "email_footer")
    recipient = doc.get("email") or doc.get("email_id") or doc.get("contact_email")
    message = follow_up_mail_content.replace("{{footer}}", footer)
    
    # send mail
    make_email(
        recipients=recipient,
        sender=frappe.session.user if frappe.session.user != "Administrator" else doc.owner,
        subject="{0} - Erinnerung: Angebot {1} - {2}".format((doc.object or ""), doc.name, (doc.object_address_display or "").replace("<br>", ", ")),
        content=message,
        doctype="Quotation",
        name=quotation,
        print_format="Offerte",
        attachments=[],
        send_email=True
    )
    return

def update_next_follow_up(quotation):
    doc = frappe.get_doc("Quotation", quotation)
    if not doc.next_follow_up:
        return                      # skip if no follow up is set
    if doc.docstatus != 1 or doc.status != "Open":
        doc.next_follow_up = None   # if this is not open, clear follow up
    else:
        if doc.next_follow_up > datetime.today().date():
            return                  # next follow up is in th future, skip
        else:
            new_date = doc.next_follow_up + timedelta(days=FOLLOW_UP_DAYS)
            if new_date <= datetime.today().date():
                new_date = datetime.today().date()     # do not set follow up in the past
            doc.next_follow_up = new_date
            
    doc.save()
    frappe.db.commit()
    return
    
"""
Perform a nightly follow-up run
"""
def automatic_follow_up():
    # get all quotations due to follow up
    qtns = frappe.db.sql("""
        SELECT `name`, `status`
        FROM `tabQuotation`
        WHERE DATE(`next_follow_up`) <= CURDATE();
        """, as_dict=True)
    
    if len(qtns) == 0:
        return
        
    for qtn in qtns:
        if qtn['status'] == "Open":
            send_follow_up(qtn['name'])
        update_next_follow_up(qtn['name'])
        
    return
