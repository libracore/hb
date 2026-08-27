# -*- coding: utf-8 -*-
# Copyright (c) 2026, libracore and contributors
# License: AGPL v3. See LICENCE

import frappe

no_cache = 1

def get_context(context):
    sql_query = """
        SELECT 
            `street`, 
            `pincode`, 
            `city`, 
            `canton`, 
            `gps_latitude`,
            `gps_longitude`,
            `remarks`
        FROM `tabParking`
        ORDER BY `pincode` ASC, `street` ASC;
    """
    parkings = frappe.db.sql(sql_query, as_dict=True)

    context.no_cache = 1
    context.show_sidebar = False

    context.parkings = parkings
    
    return
