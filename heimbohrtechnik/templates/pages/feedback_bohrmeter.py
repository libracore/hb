# -*- coding: utf-8 -*-
# Copyright (c) 2021, libracore and contributors
# License: AGPL v3. See LICENCE

from __future__ import unicode_literals
import frappe
from frappe import _
import json
import datetime

@frappe.whitelist(allow_guest=True)
def insert_feedback(drilling_team, drilling_meter, date, project, project2):
    # create new record
    if not project2:
        feedback = frappe.get_doc({
            'doctype': 'Feedback Drilling Meter',
            'drilling_team': drilling_team,
            'drilling_meter': drilling_meter,
            'date': date,
            #Create subtable "layers"
            "project": [{
            "reference_doctype": "Feedback Drilling Meter Project",
            "project_number": project
                }]
        })
    else:
        feedback = frappe.get_doc({
            'doctype': 'Feedback Drilling Meter',
            'drilling_team': drilling_team,
            'drilling_meter': drilling_meter,
            'date': date,
            #Create subtable "layers"
            "project": [{
            "reference_doctype": "Feedback Drilling Meter Project",
            "project_number": project
                },
                {
                "reference_doctype": "Feedback Drilling Meter Project",
                "project_number": project2
                }]
        })
    feedback = feedback.insert(ignore_permissions=True)
    feedback.submit()
    return {'feedback': feedback.name}

@frappe.whitelist(allow_guest=True)
def check_key(link_key, team):
    
    #get Team Key
    team_key = frappe.db.get_value("Drilling Team", team, "team_key")
    
    #validate key and prepare response
    if link_key == team_key:
        response = True
    else:
        response = False    
    
    return response
