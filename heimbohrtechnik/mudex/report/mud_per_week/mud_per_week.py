# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime, timedelta

def execute(filters=None):
    columns, data = [], []

    columns = get_columns()

    first_date = find_first_kw_start_date(filters.fiscal_year)

    data = []
    for kw in range(1, 53, 1):
        _data = get_values(kw, first_date, first_date + timedelta(days=6))
        _data['kw'] = "KW {0}".format(kw)
        data.append(_data)
        if filters.with_details:
            details = get_details(kw, first_date, first_date + timedelta(days=6))
            for d in details:
                data.append(d)
        first_date = first_date + timedelta(days=7)

    message = "Mud per week"
    
    chart = get_chart(data)
    
    return columns, data, message, chart

def get_columns():
    return [
        {"label": _("KW"), "fieldname": "kw", "fieldtype": "Data", "width": 75},
        {"label": _("Schlammmenge [kg]"), "fieldname": "formatted_weight", "fieldtype": "Data", "width": 150},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Data", "width": 120},
        {"label": _("Objekt"), "fieldname": "object", "fieldtype": "Link", "options": "Object", "width": 75},
        {"label": _("Truck"), "fieldname": "truck", "fieldtype": "Link", "options": "Truck", "width": 120},
        {"label": _("Document"), "fieldname": "document", "fieldtype": "Link", "options": "Truck Delivery", "width": 120},
    ]

def find_first_kw_start_date(year):
    sql_query="""SELECT DATE_ADD("{year}-01-01", INTERVAL (-WEEKDAY("{year}-01-01")) DAY) AS `date`;""".format(year=year)
    start_date = frappe.db.sql(sql_query, as_dict=True)[0]['date']
    return datetime.strptime(start_date, '%Y-%m-%d')

def get_values(kw, start_date, end_date):
    sql_query = """
        SELECT
           'KW {kw}' AS `date`,
           SUM(`tabTruck Delivery`.`net_weight`) AS `weight`,
           '{start_date}' AS `date`,
           NULL AS `document`,
           0 AS `indent`
        FROM `tabTruck Delivery`
        WHERE
           `tabTruck Delivery`.`date` BETWEEN '{start_date}' AND '{end_date}'
           AND  `tabTruck Delivery`.`docstatus` = 1;
    """.format(kw=kw, start_date=start_date, end_date=end_date)

    data = frappe.db.sql(sql_query, as_dict=True)

    data = format_data(data)
    
    return data[0]
    
def get_details(kw, start_date, end_date):
    sql_query = """
        SELECT
           'KW {kw}' AS `date`,
           `tabTruck Delivery Object`.`weight` AS `weight`,
           `tabTruck Delivery Object`.`object` AS `object`,
           `tabTruck Delivery`.`truck` AS `truck`,
           `tabTruck Delivery`.`date` AS `date`,
           `tabTruck Delivery`.`name` AS `document`,
           1 AS `indent`
        FROM `tabTruck Delivery Object`
        LEFT JOIN `tabTruck Delivery` ON `tabTruck Delivery`.`name` = `tabTruck Delivery Object`.`parent`
        WHERE
           `tabTruck Delivery`.`date` BETWEEN '{start_date}' AND '{end_date}'
           AND  `tabTruck Delivery`.`docstatus` = 1
        ORDER BY `tabTruck Delivery`.`date` ASC;
    """.format(kw=kw, start_date=start_date, end_date=end_date)

    data = frappe.db.sql(sql_query, as_dict=True)

    data = format_data(data)
    
    return data

def format_data(data):
    for d in data:
        d['formatted_weight'] = "{:,.0f}".format(d.get('weight') or 0).replace(",", "'")      # hack to get a thousand separator
        d['date'] = datetime.strptime("{0}".format(d.get('date'))[0:19], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")   # ( 
        
    return data

def get_chart(data):
    datasets = []
    values = []
    labels = []
    for d in data:
        if d['indent'] == 0:
            labels.append("{0}".format(d['kw']))
            values.append(d['weight'])
        
    datasets = [{
        'name': [_("Mud per Week")],
        'values': values
    }]
    
    chart = {
        'data': {
            'labels': labels,
            'datasets': datasets,
        },
        'type': "line"
    }
    return chart
