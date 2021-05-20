# Copyright (c) 2021, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

# searches for supplier
def supplier_by_capability(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabSupplier`.`name`, `tabSupplier`.`supplier_name`
           FROM `tabSupplier`
           LEFT JOIN `tabSupplier Activity` ON `tabSupplier Activity`.`parent` = `tabSupplier`.`name`
           WHERE `tabSupplier Activity`.`activity` = "{c}" AND `tabSupplier`.`supplier_name` LIKE "%{s}%";
        """.format(c=filters['capability'], s=txt))

@frappe.whitelist()
def get_required_activities(supplier, activity):
    sql_query = """SELECT `required_activity`
                   FROM `tabSupplier Activity`
                   WHERE `parent` = "{supplier}"
                     AND `activity` = "{activity}"; """.format(supplier=supplier, activity=activity)
    data = frappe.db.sql(sql_query, as_dict=True)
    activities = []
    for a in data:
        activities.append(a['required_activity'])
    return activities
