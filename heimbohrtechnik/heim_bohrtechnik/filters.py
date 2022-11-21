# Copyright (c) 2021-2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

# searches for supplier
def supplier_by_capability(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabSupplier`.`name`, `tabSupplier`.`supplier_name`, `tabSupplier`.`remarks`
           FROM `tabSupplier`
           LEFT JOIN `tabSupplier Activity` ON `tabSupplier Activity`.`parent` = `tabSupplier`.`name`
           WHERE `tabSupplier Activity`.`activity` = "{c}" 
             AND (`tabSupplier`.`supplier_name` LIKE "%{s}%" 
                  OR `tabSupplier`.`name` LIKE "%{s}%"
                  OR `tabSupplier`.`remarks` LIKE "%{s}%");
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

# searches for supplier
def get_company_sales_items(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabItem`.`item_code`, `tabItem`.`item_name`, `tabItem`.`item_group`
           FROM `tabItem`
           WHERE `tabItem`.`is_sales_item` = 1 
             AND `tabItem`.`item_group` LIKE "{c}" 
             AND (`tabItem`.`item_code` LIKE "%{s}%" 
                  OR `tabItem`.`item_name` LIKE "%{s}%"
                  OR `tabItem`.`description` LIKE "%{s}%");
        """.format(c=filters['group_code'], s=txt))
