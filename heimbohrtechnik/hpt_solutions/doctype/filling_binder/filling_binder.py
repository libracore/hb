# -*- coding: utf-8 -*-
# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests

class FillingBinder(Document):
    def before_save(self):
        if self.name:
            self.post_filling_binder_to_hpt_cloud()
        return
        
    def post_filling_binder_to_hpt_cloud(self, debug=False):
        """
        Transmit this filling_binder to the HPT cloud
        """
        filling_binder = {
                "name": self.name,
                "naming_series": self.naming_series,
                "manufacturer": self.manufacturer,
                "product": self.product,
                "mixture_type": self.mixture_type,
                "status": self.status,
                "water": self.water,
                "cement": self.cement,
                "bentonite": self.bentonite,
                "filling_binder": self.filling_binder,
                "suspension": self.suspension,
                "thermal_conductivity": self.thermal_conductivity,
                "density_water": self.density_water,
                "density_cement": self.density_cement,
                "density_bentonite": self.density_bentonite,
                "suspension_ratio": self.suspension_ratio,
                "density_manufacturer": self.density_manufacturer,
                "water_solid_value": self.water_solid_value,
                "bag_weight": self.bag_weight
            }
            
        parameters = {
            "filling_binder": filling_binder,
            "key": frappe.get_value("HPT Settings", "HPT Settings", "hpt_api_key")
        }
        
        response = requests.post(
            "https://cloud.hpt.solutions/api/method/hptcloud.hptcloud.doctype.filling_binder.filling_binder.update_filling_binder",
            json = parameters
        )
        
        if response.status_code != 200:
            frappe.log_error( "Filling_binder upload failed with {0}".format(response.text), "HPT Upload failed")
        if 'error' in response.text:
            frappe.log_error( "Filling_binder upload failed with {0}".format(response.json()['message']['error']), "HPT Upload failed")

        if debug:
            print(response.text)
        
        return
