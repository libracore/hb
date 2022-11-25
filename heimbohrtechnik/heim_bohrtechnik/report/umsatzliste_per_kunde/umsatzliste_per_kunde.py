# Copyright (c) 2022, libracore AG and contributors
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
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 80},
        {"label": _("Customer name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 250},
        {"label": _("Revenue"), "fieldname": "revenue", "fieldtype": "Currency", "width": 150},
        {"label": _("Project Manager"), "fieldname": "project_manager", "fieldtype": "Data", "width": 150},
        {"label": _(""), "fieldname": "blank", "fieldtype": "Data", "width": 20}
    ]
    return columns

def get_data(filters):
    fiscal_year = frappe.get_doc("Fiscal Year", filters.fiscal_year)
    if filters.item_code:
        item = filters.item_code
    else:
        item = "%"
        
    if filters.options == "Auftragsdatum":
        sql_query = """
            SELECT
                `tabSales Order`.`customer` AS `customer`,
                `tabSales Order` .`customer_name` AS `customer_name`,
                SUM(`tabSales Order Item`.`base_net_amount`) AS `revenue`,
                MAX(`tabProject`.`manager`) AS `project_manager`
            FROM `tabSales Order`
            LEFT JOIN `tabProject` ON `tabProject`.`sales_order` = `tabSales Order`.`name`
            LEFT JOIN `tabSales Order Item` ON `tabSales Order Item`.`parent` = `tabSales Order`.`name`
            WHERE
                `tabSales Order`.`transaction_date` >= "{from_date}"
                AND `tabSales Order`.`transaction_date` <= "{to_date}"
                AND `tabSales Order`.`docstatus` = 1
                AND `tabSales Order Item`.`item_code` LIKE "{item}"
            GROUP BY `tabSales Order`.`customer`
            ORDER BY SUM(`tabSales Order Item`.`base_net_amount`) DESC;
        """.format(from_date=fiscal_year.year_start_date, to_date=fiscal_year.year_end_date, item=item)
    elif filters.options == "Lieferdatum":
        sql_query = """
            SELECT
                `tabSales Order`.`customer` AS `customer`,
                `tabSales Order` .`customer_name` AS `customer_name`,
                SUM(`tabSales Order Item`.`base_net_amount`) AS `revenue`,
                MAX(`tabProject`.`manager`) AS `project_manager`
            FROM `tabSales Order`
            LEFT JOIN `tabProject` ON `tabProject`.`sales_order` = `tabSales Order`.`name`
            LEFT JOIN `tabSales Order Item` ON `tabSales Order Item`.`parent` = `tabSales Order`.`name`
            WHERE
                `tabSales Order`.`delivery_date` >= "{from_date}"
                AND `tabSales Order`.`delivery_date` <= "{to_date}"
                AND `tabSales Order`.`docstatus` = 1
                AND `tabSales Order Item`.`item_code` LIKE "{item}"
            GROUP BY `tabSales Order`.`customer`
            ORDER BY SUM(`tabSales Order Item`.`base_net_amount`) DESC;
        """.format(from_date=fiscal_year.year_start_date, to_date=fiscal_year.year_end_date, item=item)
    elif filters.options == "Rechnungsdatum":
        sql_query = """
            SELECT
                `tabSales Invoice`.`customer` AS `customer`,
                `tabSales Invoice` .`customer_name` AS `customer_name`,
                SUM(`tabSales Invoice Item`.`base_net_amount`) AS `revenue`,
                MAX(`tabSales Invoice`.`reference_user`) AS `project_manager`
            FROM `tabSales Invoice`
            LEFT JOIN `tabSales Invoice Item` ON `tabSales Invoice Item`.`parent` = `tabSales Invoice`.`name`
            WHERE
                `tabSales Invoice`.`posting_date` >= "{from_date}"
                AND `tabSales Invoice`.`posting_date` <= "{to_date}"
                AND `tabSales Invoice`.`docstatus` = 1
                AND `tabSales Invoice Item`.`item_code` LIKE "{item}"
            GROUP BY `tabSales Invoice`.`customer`
            ORDER BY SUM(`tabSales Invoice Item`.`base_net_amount`) DESC;
        """.format(from_date=fiscal_year.year_start_date, to_date=fiscal_year.year_end_date, item=item)
    
    data = frappe.db.sql(sql_query, as_dict=True)
    return data
