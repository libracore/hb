# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    data = get_data(filters)
    columns = get_columns(data)
    return columns, data

def get_columns(data):
    columns = [
        {'fieldname': 'drilling_team', 'label': _("Drilling Team"), 'fieldtype': 'Link', 'options': 'Drilling Team', 'width': '200px'},
        {'fieldname': 'projects', 'label': _("Projects"), 'fieldtype': 'Int', 'width': '100px'},
        {'fieldname': 'drillings', 'label': _("Bohrungen"), 'fieldtype': 'Int', 'width': '100px'},
        {'fieldname': 'drilling_meters', 'label': _("Bohrmeter"), 'fieldtype': 'Data', 'width': '100px'},
        {'fieldname': 'avg', 'label': _("Durchschn."), 'fieldtype': 'Data', 'width': '100px'},
        {'fieldname': 'deepest', 'label': _("Tiefste"), 'fieldtype': 'Data', 'width': '100px'}
    ]
    
    return columns

def get_data(filters): 
    data = frappe.db.sql("""
        SELECT
            IFNULL(`tabProject`.`drilling_team`, "?") AS `drilling_team`,
            COUNT(`tabProject`.`name`) AS `projects`,
            SUM(`tabObject EWS`.`ews_count`) AS `drillings`,
            SUM(`tabObject EWS`.`ews_depth` * `tabObject EWS`.`ews_count`) AS `drilling_meters`,
            MAX(`tabObject EWS`.`ews_depth`) As `deepest`
        FROM `tabProject`
        LEFT JOIN `tabObject EWS` ON `tabObject EWS`.`parent` = `tabProject`.`object`
        LEFT JOIN `tabDrilling Team` ON `tabDrilling Team`.`name` = `tabProject`.`drilling_team`
        WHERE ((`expected_start_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_end_date` BETWEEN '{from_date}' AND '{to_date}')
             OR (`expected_start_date` < '{from_date}' AND `expected_end_date` > '{to_date}')
            )
            AND `tabDrilling Team`.`drilling_team_type` = "Bohrteam"
        GROUP BY `tabProject`.`drilling_team`
        ORDER BY `tabProject`.`drilling_team` ASC;
    """.format(from_date=filters.from_date, to_date=filters.to_date), as_dict=True)
    
    for d in data:
        d['avg'] = "{0} m".format(round(d['drilling_meters'] / d['drillings']))
        d['deepest'] = "{0} m".format(d['deepest'])
        d['drilling_meters'] = "{:,.0f} m".format(d['drilling_meters']).replace(",", "'")
        
    return data
