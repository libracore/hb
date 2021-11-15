# Copyright (c) 2021, libracore AG and contributors
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
        {"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 100},
        {"label": _("Item"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 120},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 75},
        {"label": _("Buying rate"), "fieldname": "buying_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Last purchase rate"), "fieldname": "last_purchase_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Price list rate"), "fieldname": "price_list_rate", "fieldtype": "Currency", "width": 100},
        {"label": _("Pricing Rule"), "fieldname": "pricing_rule", "fieldtype": "Link", "options": "Pricing Rule", "width": 120},
        #{"label": _("Discount"), "fieldname": "discount_percentage", "fieldtype": "Percent", "width": 100},
        #{"label": _("Rate"), "fieldname": "discounted_rate", "fieldtype": "Currency", "width": 100},
        #{"label": _("DB1"), "fieldname": "db1", "fieldtype": "Currency", "width": 100},
        #{"label": _("DB1 [%]"), "fieldname": "db1_percent", "fieldtype": "Percent", "width": 100}
    ]

def get_data(filters):
    if not filters.item_group:
        filters.item_group = "%"
    if not filters.item_name:
        filters.item_name = "%"
    else:
        filters.item_name = "%{0}%".format(filters.item_name)
    if not filters.item_code:
        filters.item_code = "%"
    else:
        filters.item_code = "%{0}%".format(filters.item_code)

    sql_query = """SELECT 
              `aggr`.`item_code`,
              `aggr`.`item_name`,
              `aggr`.`item_group`,
              `aggr`.`stock_uom`,
              `aggr`.`price_list_rate`,
              `aggr`.`last_purchase_rate`,
              `aggr`.`pricing_rule`,
              `aggr`.`discount_percentage`,
              `aggr`.`discounted_rate`,
              `aggr`.`db1`,
              ((`aggr`.`db1` / `aggr`.`discounted_rate`) * 100) AS `db1_percent`
          FROM 
            (SELECT 
              `raw`.`item_code`,
              `raw`.`item_name`,
              `raw`.`item_group`,
              `raw`.`stock_uom`,
              `raw`.`price_list_rate`,
              `raw`.`last_purchase_rate`,
              `raw`.`pricing_rule`,
              `tPR`.`discount_percentage` AS `discount_percentage`,
              ((100 - `tPR`.`discount_percentage`)/100) * `raw`.`price_list_rate` AS `discounted_rate`,
              ((((100 - `tPR`.`discount_percentage`)/100) * `raw`.`price_list_rate`) - `raw`.`last_purchase_rate`) AS `db1`
            FROM 
                (SELECT 
                  `tabItem`.`item_code` AS `item_code`,
                  `tabItem`.`item_name` AS `item_name`,
                  `tabItem`.`item_group` AS `item_group`,
                  `tabItem`.`last_purchase_rate` AS `last_purchase_rate`,
                  `tabItem`.`stock_uom` AS `stock_uom`,
                  (SELECT `tabItem Price`.`price_list_rate` 
                   FROM `tabItem Price` 
                   WHERE `tabItem Price`.`item_code` = `tabItem`.`item_code`
                     AND `tabItem Price`.`price_list` = "Standard-Vertrieb") AS `price_list_rate`,
                  (SELECT `tabPricing Rule`.`name`
                   FROM `tabPricing Rule`
                   LEFT JOIN `tabPricing Rule Item Code` ON `tabPricing Rule Item Code`.`parent` = `tabPricing Rule`.`name`
                   LEFT JOIN `tabPricing Rule Item Group` ON `tabPricing Rule Item Group`.`parent` = `tabPricing Rule`.`name`
                   WHERE `tabPricing Rule`.`selling` = 1
                     AND `tabPricing Rule`.`customer` = "{customer}"
                     AND `tabPricing Rule`.`disable` = 0
                     AND (`tabPricing Rule Item Code`.`item_code` = `tabItem`.`item_code`
                          OR `tabPricing Rule Item Group`.`item_group` = `tabItem`.`item_group`
                          OR `tabPricing Rule Item Group`.`item_group` = "Alle Artikelgruppen")
                   ORDER BY `tabPricing Rule`.`priority` DESC
                   LIMIT 1) AS `pricing_rule`
                FROM `tabItem`
                WHERE `tabItem`.`is_sales_item` = 1
                  AND `tabItem`.`item_group` LIKE "{item_group}"
                  AND `tabItem`.`item_name` LIKE "{item_name}"
                  AND `tabItem`.`item_code` LIKE "{item_code}") AS `raw`
            LEFT JOIN `tabPricing Rule` AS `tPR` ON `tPR`.`name` = `raw`.`pricing_rule`
            ) AS `aggr`;""".format(customer=filters.customer, item_group=filters.item_group,
                item_code=filters.item_code, item_name=filters.item_name)
    data = frappe.db.sql(sql_query, as_dict=True)
    config = frappe.get_doc("Heim Settings", "Heim Settings")
    buying_price_lists = "('{0}', '{1}')".format(config.buying_price_list_chf, config.buying_price_list_eur)
    eur_conversion_rate = frappe.db.sql("""SELECT IFNULL(`exchange_rate`, 1) AS `rate`
        FROM `tabCurrency Exchange`
        WHERE `from_currency` = "CHF"
          AND `to_currency` = "EUR"
        ORDER BY `date` DESC
        LIMIT 1;""", as_dict=True)[0]['rate']
    # add buying prices
    for d in data:
        buying_rates = frappe.db.sql("""SELECT 
                IFNULL(`tabItem Price`.`price_list_rate`, 0) AS `rate`,
                `tabItem Price`.`currency` AS `currency`
            FROM `tabItem Price`
            WHERE `tabItem Price`.`item_code` = "{item_code}"
              AND `tabItem Price`.`price_list` IN {price_lists}
              AND `tabItem Price`.`valid_from` <= DATE(NOW())
            ORDER BY `tabItem Price`.`currency` ASC, `tabItem Price`.`valid_from` DESC;
        """.format(item_code=d['item_code'], price_lists=buying_price_lists), as_dict=True)
        if len(buying_rates) > 0:
            if buying_rates[0]['currency'] == "EUR":
                d['buying_rate'] = buying_rates[0]['rate'] / eur_conversion_rate
            else:
                d['buying_rate'] = buying_rates[0]['rate']
        else:
            d['buying_rate'] = None
    return data
