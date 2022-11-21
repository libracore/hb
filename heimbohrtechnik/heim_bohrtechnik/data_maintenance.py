# Copyright (c) 2021-2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

"""
This function will maintain sales order links to projects
"""
def link_sales_orders_to_projects():
    # find all projects that have no links
    sql_query = """
        SELECT 
            `tabProject`.`name` AS `project`,
            `tabSales Order`.`customer` AS `customer`,
            `tabSales Order`.`name` AS `sales_order`
        FROM `tabProject`
        LEFT JOIN `tabSales Order` ON 
            (`tabSales Order`.`object` = `tabProject`.`object`
             AND `tabSales Order`.`docstatus` = 1)
        WHERE 
            `tabProject`.`sales_order` IS NULL
            AND `tabSales Order`.`name` IS NOT NULL;"""
    unlinked_projects = frappe.db.sql(sql_query, as_dict=True)
    for u in unlinked_projects:
        project = frappe.get_doc("Project", u['project'])
        project.customer = u['customer']
        project.sales_order = u['sales_order']
        try:
            project.save()
            frappe.db.commit()
        except Exception as err:
            frappe.log_error( "Link Sales Order to Project Issue: {0}: {1}".format(u['project'], err), "link_sales_orders_to_projects")
    return

"""
Remove old Bohrplaner-Prints
"""
def remove_bohrplaner_prints():
    prints = frappe.db.sql("""SELECT `name` FROM `tabFile` WHERE `folder` = 'Home/Bohrplaner-Prints'""", as_dict=True)
    for print_doc in prints:
        p = frappe.get_doc("File", print_doc.name)
        p.delete()
