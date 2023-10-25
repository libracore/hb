# Copyright (c) 2019-2021, libracore and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def cleanup_languages():
    # this function will remove languages after migrate
    print("Removing unnecessary languages...")
    lang = "'de', 'en-US', 'en', 'fr'"
    sql_query = """DELETE FROM `tabLanguage` WHERE `language_code` NOT IN ({lang});""".format(lang=lang)
    frappe.db.sql(sql_query, as_dict=1)
    return

def assert_kg():
    # this function will make sure that there is always the kg UOM
    print("Make sure kg is available as UOM...")
    if not frappe.db.exists("UOM", "kg"):
        kg = frappe.get_doc({
            'doctype': 'UOM',
            'uom_name': 'kg'
        })
        kg.insert()
    return

def disable_prepared_report():
    # this will disable prepared reports 
    print("Disabling prepared reports...")
    reports = frappe.get_all("Report", filters={'disabled': 0}, fields=['name'])
    for r in reports:
        report = frappe.get_doc("Report", r['name'])
        if report.disable_prepared_report == 0:
            report.disable_prepared_report = 1;
            try:
                report.save()
            except Exception as err:
                print("Report {0}: {1}".format(report.name, err))
    frappe.db.commit()
    return

def create_folder():
    """Make sure the folder exists"""
    from erpnextswiss.erpnextswiss.attach_pdf import create_folder
    print("Make sure the folder Bohrplaner-Prints exists...")
    create_folder(folder='Bohrplaner-Prints', parent='Home')
