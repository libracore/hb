# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": _("Link"), "fieldname": "dn", "fieldtype": "Dynamic Link", "options": "dt", "width": 100},
        {"label": _("Drilling Team"), "fieldname": "drilling_team", "fieldtype": "Link", "options": "Drilling Team", "width": 150},
        {"label": _("Truck"), "fieldname": "truck", "fieldtype": "Link", "options": "Truck", "width": 90},
        {"label": _("Maintenance Report"), "fieldname": "maintenance_report", "fieldtype": "Link", "options": "Maintenance Report", "width": 150}
    ]

def get_data(filters):
    # get all revision projects and MFK
    sql_query = """
        SELECT 
            *
        FROM (
            SELECT
                DATE(`tabMFK`.`start_time`) AS `date`,
                "MFK" AS `dt`,
                `tabMFK`.`name` AS `dn`,
                `tabMFK`.`drilling_team` AS `drilling_team`,
                `tabMFK`.`truck` AS `truck`,
                NULL AS `maintenance_report`
            FROM `tabMFK`
            WHERE 
                `tabMFK`.`start_time` BETWEEN "{from_date}" AND "{to_date}"
            UNION SELECT
                DATE(`tabProject`.`expected_start_date`) AS `date`,
                "Project" AS `dt`,
                `tabProject`.`name` AS `dn`,
                `tabProject`.`drilling_team` AS `drilling_team`,
                `tabMaintenance Report`.`truck` AS `truck`,
                `tabMaintenance Report`.`name` AS `maintenance_report`
            FROM `tabProject`
            LEFT JOIN `tabMaintenance Report` ON `tabMaintenance Report`.`project` = `tabProject`.`name`
            WHERE 
                `tabProject`.`expected_start_date` BETWEEN "{from_date}" AND "{to_date}"
                AND `tabProject`.`object_name` = "REVISION"
        ) AS `raw`
        ORDER BY `raw`.`date`;
    """.format(from_date=filters.from_date, to_date=filters.to_date)
    data = frappe.db.sql(sql_query, as_dict=True)

    return data
