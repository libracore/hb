# -*- coding: utf-8 -*-
# Copyright (c) 2022-2026, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import datetime
from heimbohrtechnik.heim_bohrtechnik.page.bohrplaner.bohrplaner import get_content, get_overlay_datas, get_subproject_overlay_datas, get_internal_overlay_datas
from frappe.utils.pdf import get_pdf
import base64
import re
from frappe.utils.file_manager import get_file
import mimetypes

"""
This function checks the access and returns the restricted information
"""
@frappe.whitelist(allow_guest=True)
def get_grid(from_date, to_date, drilling_team=None, tv_mode=False):
    data = get_content(from_date[1:11], to_date[1:11], only_teams=True if not drilling_team else False)

    if drilling_team:
        dt = frappe.get_doc("Drilling Team", drilling_team).as_dict()
        data['drilling_teams'] = [{
            'crane_details': dt['crane_details'],
            'drilling_team_type': dt['drilling_team_type'],
            'drm': dt['drm'],
            'drt': dt['drt'],
            'has_crane': dt['has_crane'],
            'has_trough': dt['has_trough'],
            'phone': dt['phone'],
            'team_id': drilling_team,
            'title': drilling_team,
            'trough_details': dt['trough_details'],
            'truck_and_weight': dt['truck_and_weight']
        }]
            
    return data
    
    
@frappe.whitelist(allow_guest=True)
def get_data(key, from_date, to_date, customer=None, drilling_team=None, tv_mode=False):
    if not customer and not drilling_team and not tv_mode:
        return {'error': 'No customer or drilling team'}
    
    if customer:
        if not frappe.db.exists("Customer", customer):
            return {'error': 'Invalid customer'}
        if frappe.get_value("Customer", customer, "key") != key:
            return {'error': 'Invalid key'}
        
        data = {
            'projects': get_overlay_datas(from_date[1:11], to_date[1:11], customer),
            'internals': get_internal_overlay_datas(from_date[1:11], to_date[1:11], customer)
        }
    elif drilling_team:
        if not frappe.db.exists("Drilling Team", drilling_team):
            return {'error': 'Invalid drilling team'}
        if frappe.get_value("Drilling Team", drilling_team, "team_key") != key:
            return {'error': 'Invalid key'}
        
        data = {
            'subprojects': get_subproject_overlay_datas(from_date[1:11], to_date[1:11], drilling_team)
        }
    else:
        # TV mode
        data = {
            'projects': get_overlay_datas(from_date[1:11], to_date[1:11]),
            'internals': get_internal_overlay_datas(from_date[1:11], to_date[1:11])
        }
    
    return data

"""
Check secret
"""
@frappe.whitelist(allow_guest=True)
def verify_secret(key):
    if frappe.get_value("Heim Settings", "Heim Settings", "tv_access_secret") == key:
        return True
    else:
        return False

"""
Compute the last planned date (for visible range)
"""
@frappe.whitelist(allow_guest=True)
def get_last_date(customer=None, key=None, drilling_team=None):
    last_date = []

    if not key:
        return None
    if customer:
        if not frappe.db.exists("Customer", customer):
            return None
        if frappe.get_value("Customer", customer, "key") != key:
            return None
        
        last_date = frappe.db.sql("""
            SELECT MAX(`expected_end_date`) AS `expected_end_date`
            FROM `tabProject`
            WHERE `tabProject`.`customer` = "{customer}"
              AND `tabProject`.`status` = "Open"
              ;
        """.format(customer=customer), as_dict=True)
    else:
        if not frappe.db.exists("Drilling Team", drilling_team):
            return None
        if frappe.get_value("Drilling Team", drilling_team, "team_key") != key:
            frappe.log_error("invalid key used for external drilling plan {0}".format(drilling_team), "Bohrplan Access Error")
            return None
        
        last_date = frappe.db.sql("""
            SELECT MAX(`to_date`) AS `expected_end_date`
            FROM `tabSubcontracting Order`
            WHERE `tabSubcontracting Order`.`drilling_team` = "{drilling_team}"
              ;
        """.format(drilling_team=drilling_team), as_dict=True)
        
    if len(last_date) > 0:
        return last_date[0]['expected_end_date']
    else:
        return None

@frappe.whitelist(allow_guest=True)
def get_subcontracting_pdf(key, drilling_team, subcontracting_order):
    if not frappe.db.exists("Drilling Team", drilling_team):
        return {'error': 'Invalid drilling team'}
    if frappe.get_value("Drilling Team", drilling_team, "team_key") != key:
        return {'error': 'Invalid key'}
    
    doc = frappe.get_doc("Subcontracting Order", subcontracting_order)
    raw_html = frappe.get_value('Print Format', 'Verlängerungsauftrag', 'html')
    css = frappe.get_value('Print Format', 'Verlängerungsauftrag', 'css')
    css_html = f"<style>{css}</style>{raw_html}"
    # create html
    rendered_html = frappe.render_template(css_html, {'doc': doc} )
    rendered_html = inline_private_images(rendered_html)
    # need to load the styles and tags
    content = frappe.render_template(
        'heimbohrtechnik/templates/includes/print.html',
        {'html': rendered_html}
    )
    options = {
        'disable-smart-shrinking': ''
    }
    pdf = get_pdf(content, options)
    frappe.local.response.filename = f"{doc}.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"

def inline_private_images(html):
    """Replace private file image src with base64 data URIs"""
    def replace_src(match):
        file_url = match.group(1)
        if "/private/files/" not in file_url:
            return match.group(0)
        try:
            file_doc = frappe.get_doc("File", {"file_url": file_url})
            file_path = file_doc.get_full_path()  # resolves to the actual disk path

            with open(file_path, "rb") as f:
                content = f.read()

            mime_type, _ = mimetypes.guess_type(file_doc.file_name)
            mime_type = mime_type or "image/png"
            b64 = base64.b64encode(content).decode("utf-8")
            return f'src="data:{mime_type};base64,{b64}"'
        except Exception:
            frappe.log_error(
                title="PDF image inlining failed",
                message=frappe.get_traceback()
            )
            return match.group(0)

    return re.sub(r'src="([^"]+)"', replace_src, html)
