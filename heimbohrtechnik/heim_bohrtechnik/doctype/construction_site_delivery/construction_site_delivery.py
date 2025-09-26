# -*- coding: utf-8 -*-
# Copyright (c) 2022-2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from datetime import datetime, timedelta

class ConstructionSiteDelivery(Document):
    def before_save(self):
        # make sure proper dates are set
        if not self.date:
            today = datetime.now()
            self.date = datetime(today.year, today.month, today.day, 7, 0, 0)
        if not self.to_date:
            if type(self.date) == str:
                self.date = datetime.strptime(self.date, "%Y-%m-%d %H:%M:%S")
            self.to_date = self.date + timedelta(hours=2)
            
        # assemble the calendar display
        self.calendar_display = "{0}: {1} - {2}{3}, {4}".format(
            self.employee_short,
            self.project,
            "{0}, ".format(self.note) if self.note else "",
            self.object_street,
            self.object_location
        )
        return

@frappe.whitelist()
def get_events(doctype, start, end, field_map, filters=None, fields=None):
    field_map = frappe._dict(json.loads(field_map))
    doc_meta = frappe.get_meta(doctype)
    for d in doc_meta.fields:
        if d.fieldtype == "Color":
            field_map.update({
                "color": d.fieldname
            })

    if filters:
        filters = json.loads(filters or '')

    if not fields:
        fields = [field_map.start, field_map.end, field_map.title, 'name']

    if field_map.color:
        fields.append(field_map.color)

    start_date = "ifnull(%s, '0001-01-01 00:00:00')" % field_map.start
    end_date = "ifnull(%s, '2199-12-31 00:00:00')" % field_map.end

    filters += [
        [doctype, start_date, '<=', end],
        [doctype, end_date, '>=', start],
    ]

    return frappe.get_list(doctype, fields=fields, filters=filters)
