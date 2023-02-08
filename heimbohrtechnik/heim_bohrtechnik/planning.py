# Copyright (c) 2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

"""
Check if a project has a conflict with a public holiday
"""
def check_project_against_regional_holiday(project):
    p_doc = frappe.get_doc("Project", project)
    region = (p_doc.object_location or "")[-2:]             # canton code
    # find applicable holidays
    sql_query = """
        SELECT `holiday_date`, `description`
        FROM `tabHoliday`
        WHERE 
            `parenttype` = "Regional Holidays"
            AND `parent` = "{region}"
            AND `holiday_date` >= "{p_start}"
            AND `holiday_date` <= "{p_end}";
    """.format(region=region, p_start=p_doc.expected_start_date, p_end=p_doc.expected_end_date)

    conflicts = frappe.db.sql(sql_query, as_dict=True)
    if len(conflicts):
        return conflicts
    else:
        return None
