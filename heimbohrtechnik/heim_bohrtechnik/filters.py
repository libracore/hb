# Copyright (c) 2021-2024, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

# searches for supplier
def supplier_by_capability(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabSupplier`.`name`, `tabSupplier`.`supplier_name`, `tabSupplier`.`remarks`, `tabSupplier`.`hauptadresse`
           FROM `tabSupplier`
           LEFT JOIN `tabSupplier Activity` ON `tabSupplier Activity`.`parent` = `tabSupplier`.`name`
           WHERE `tabSupplier Activity`.`activity` = "{c}" 
             AND `tabSupplier`.`disabled` = 0
             AND (`tabSupplier`.`supplier_name` LIKE "%{s}%" 
                  OR `tabSupplier`.`name` LIKE "%{s}%"
                  OR `tabSupplier`.`remarks` LIKE "%{s}%");
        """.format(c=filters['capability'], s=txt))

# searches for customers
def customers(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabCustomer`.`name`, `tabCustomer`.`customer_name`, `tabCustomer`.`customer_details`, `tabCustomer`.`hauptadresse`
           FROM `tabCustomer`
           WHERE `tabCustomer`.`disabled` = 0
             AND (`tabCustomer`.`customer_name` LIKE "%{s}%" 
                  OR `tabCustomer`.`name` LIKE "%{s}%"
                  OR `tabCustomer`.`customer_details` LIKE "%{s}%");
        """.format(s=txt))
        
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
             AND `tabItem`.`disabled` = 0 
             AND `tabItem`.`phase_out` = 0 
             AND `tabItem`.`item_group` LIKE "{c}" 
             AND (`tabItem`.`item_code` LIKE "%{s}%" 
                  OR `tabItem`.`item_name` LIKE "%{s}%"
                  OR `tabItem`.`description` LIKE "%{s}%");
        """.format(c=filters['group_code'], s=txt))

# searches for user
def get_user(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """SELECT `tabUser`.`name`, `tabUser`.`full_name`
           FROM `tabUser`
           WHERE `tabUser`.`enabled` = 1 
             AND `tabUser`.`name` IN ("{c}")
             AND (`tabUser`.`name` LIKE "{s}" 
                  OR `tabUser`.`full_name` LIKE "%{s}%");
        """.format(c='", "'.join(filters['users']), s=txt))
