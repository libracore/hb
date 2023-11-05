# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = [
        {"label": _("Drilling Move Log"), "fieldname": "log", "fieldtype": "Link", "options": "Drilling Move Log", "width": 140},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 100},
        {"label": _("Subproject"), "fieldname": "subproject", "fieldtype": "Link", "options": "Subcontracting Order", "width": 100},
        {"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Date", "width": 100},
        {"label": _("End Date"), "fieldname": "end_date", "fieldtype": "Date", "width": 100},
        {"label": _("Team"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 150}
    ]
    return columns
    
def get_data(filters):
    project_filter = ""
    if filters.project:
        project_filter = """ AND `dmlp`.`project` = "{0}" """.format(filters.project)
        
    projects = frappe.db.sql("""
        SELECT
            `dmlp`.`project` AS `project`,
            `dml`.`name` AS `log`,
            `dml`.`date` AS `date`
        FROM `tabDrilling Move Log Project` AS `dmlp`
        LEFT JOIN `tabDrilling Move Log` AS `dml` ON `dml`.`name` = `dmlp`.`parent`
        WHERE
            `dml`.`date` BETWEEN "{from_date}" AND "{to_date}"
            {project_filter}
        ORDER BY `dml`.`date` DESC, `dml`.`creation` DESC;
    """.format(from_date=filters.from_date, to_date=filters.to_date, project_filter=project_filter),
        as_dict=True)
    
    data = []
    last_log = None
    for p in projects:
        # check/add log heading
        if p['log'] != last_log:
            data.append({
                'log': p['log'],
                'indent': 0
            })
            last_log = p['log']
        # add project row
        project_doc = frappe.get_doc("Project", p['project'])
        data.append({
            'log': p['log'],
            'project': p['project'],
            'indent': 1,
            'start_date': project_doc.expected_start_date,
            'end_date': project_doc.expected_end_date,
            'drilling_team': project_doc.drilling_team
        })
        
        # add subprojects
        for s in project_doc.subprojects:
            data.append({
                'log': p['log'],
                'project': p['project'],
                'subproject': s.subcontracting_order,
                'indent': 2,
                'start_date': s.start,
                'end_date': s.end,
                'drilling_team': s.team
            })
    return data
