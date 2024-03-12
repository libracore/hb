# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {'fieldname': "project", 'label': _("Project"), 'fieldtype': "Link", 'options': "Project", 'width': 80},
        {'fieldname': "object_name", 'label': _("Object Name"), 'fieldtype': "Data", 'width': 150},
        {'fieldname': "object_street", 'label': _("Street"), 'fieldtype': "Data", 'width': 150},
        {'fieldname': "object_location", 'label': _("Location"), 'fieldtype': "Data", 'width': 150},
        {'fieldname': "start_date", 'label': _("Start Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "end_date", 'label': _("End Date"), 'fieldtype': "Date", 'width': 80},
        {'fieldname': "drilling_meters", 'label': _("Drilling Meter"), 'fieldtype': "Int", 'width': 80},
        {'fieldname': "invoiced_meters", 'label': _("Invoiced Meter"), 'fieldtype': "Int", 'width': 80},
        {'fieldname': "actual_meters", 'label': _("Actual Meter"), 'fieldtype': "Int", 'width': 80},
        {'fieldname': "blank", 'label': "", 'fieldtype': "Data", 'width': 20}
    ]
    
def get_data(filters):
    data = frappe.db.sql("""
        SELECT
            `tabProject`.`name` AS `project`,
            `tabObject`.`object_name` AS `object_name`,
            `tabObject`.`object_street` AS `object_street`,
            `tabObject`.`object_location` AS `object_location`,
            `tabProject`.`expected_start_date` AS `start_date`,
            `tabProject`.`expected_end_date` AS `end_date`,
            (SELECT SUM(`tabObject EWS`.`ews_count` * `tabObject EWS`.`ews_depth`)
             FROM `tabObject EWS`
             WHERE `tabObject EWS`.`parent` = `tabObject`.`name`
            ) AS `drilling_meters`,
            (SELECT SUM(`qty`)
             FROM `tabSales Invoice Item`
             LEFT JOIN `tabSales Invoice` ON `tabSales Invoice Item`.`parent` = `tabSales Invoice`.`name`
             WHERE `tabSales Invoice`.`object` = `tabObject`.`name`
               AND `tabSales Invoice Item`.`item_code` LIKE "1.01.03.01%"
               AND `tabSales Invoice`.`docstatus` = 1
            ) AS `invoiced_meters`,
            (SELECT SUM(`drilling_meter`)
             FROM `tabFeedback Drilling Meter`
             LEFT JOIN `tabFeedback Drilling Meter Project` ON 
                `tabFeedback Drilling Meter Project`.`parent` = `tabFeedback Drilling Meter`.`name`
             WHERE `tabFeedback Drilling Meter Project`.`project_number` = `tabProject`.`name`
            ) AS `actual_meters`
        FROM `tabProject`
        LEFT JOIN `tabObject` ON `tabObject`.`name` = `tabProject`.`object`
        WHERE 
            `tabProject`.`customer` = "{customer}"
            AND `tabProject`.`expected_start_date` <= "{to_date}"
            AND `tabProject`.`expected_end_date` >= "{from_date}"
        ;
    """.format(
        customer=filters.get("customer"), 
        from_date=filters.get("from_date"),
        to_date=filters.get("to_date")
        ), as_dict=True)
                
    return data
