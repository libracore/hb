# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {'fieldname': 'project', 'label': _("Project"), 'fieldtype': 'Link', 'options': 'Project', 'width': 80},
        {'fieldname': 'object_name', 'label': _("Object name"), 'fieldtype': 'Data', 'width': 175},
        {'fieldname': 'object_street', 'label': _("Street"), 'fieldtype': 'Data', 'width': 175},
        {'fieldname': 'object_location', 'label': _("Location"), 'fieldtype': 'Data', 'width': 175},
        {'fieldname': 'start_date', 'label': _("Start"), 'fieldtype': 'Date', 'width': 100},
        {'fieldname': 'end_date', 'label': _("End"), 'fieldtype': 'Date', 'width': 100},
        {'fieldname': 'status', 'label': _("Status"), 'fieldtype': 'Data', 'width': 100}
    ]
    
def get_data(filters):
    sql_query = """
        SELECT
            `tabConstruction Site Description`.`project` AS `project`,
            `tabProject`.`expected_start_date` AS `start_date`,
            `tabProject`.`expected_end_date` AS `end_date`,
            `tabProject`.`object_name` AS `object_name`,
            `tabProject`.`object_street` AS `object_street`,
            `tabProject`.`object_location` AS `object_location`,
            `tabProject`.`toitoi_ordered` AS `toitoi_ordered`
        FROM `tabConstruction Site Description`
        LEFT JOIN `tabProject` ON `tabProject`.`name` = `tabConstruction Site Description`.`project`
        WHERE 
            `tabConstruction Site Description`.`requires_toitoi` = 1
            AND `tabProject`.`expected_start_date` > CURDATE()
        ORDER BY `tabProject`.`expected_start_date` ASC;
        """
        
    data = frappe.db.sql(sql_query, as_dict=True)
    display = []
    
    for d in data:
        if filters.get("status"):
            if filters.get("status") == "required" and d.get("toitoi_ordered") == 1:
                continue        # skip ordered when filter for required
            elif filters.get("status") == "organised" and d.get("toitoi_ordered") == 0:
                continue        # skip required when fiter for organised
        
        if d.get("toitoi_ordered") == 1:
            color = "green"
            status = _("organised")
        else:
            color = "red"
            status = _("required")
            
        d['status'] = """<span style="color: {0};">{1}</span>""".format(color, status)
        display.append(d)
        
    return display
