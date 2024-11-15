# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests

class Probe(Document):
    def before_save(self):
        if self.name:
            self.post_probe_to_hpt_cloud()
        return
        
    def post_probe_to_hpt_cloud(self, debug=False):
        """
        Transmit this probe to the HPT cloud
        """
        probe = {
                "name": self.name,
                "naming_series": self.naming_series,
                "manufacturer": self.manufacturer,
                "product": self.product,
                "probe_type": self.probe_type,
                "disabled": self.disabled,
                "outer_diameter": self.outer_diameter,
                "pressure_level": self.pressure_level,
                "nominative_pressure": self.nominative_pressure,
                "wall_strength": self.nominative_pressure,
                "radius": self.radius,
                "inner_diameter": self.inner_diameter,
                "volume_per_m": self.volume_per_m,
                "material": self.material,
                "max_short_inner_pressure": self.max_short_inner_pressure,
                "tube_roughness": self.tube_roughness,
                "test_pressures": [],
                "pressure_losses": [],
                "vent_amounts": []
            }
        for tp in self.test_pressures:
            probe["test_pressures"].append({
                "density": tp.density,
                "length": tp.length,
                "test_nominal_pressure": tp.test_nominal_pressure
            })
        for pl in self.pressure_losses:
            probe["pressure_losses"].append({
                "flow": pl.flow,
                "pressure_loss": pl.pressure_loss
            })
        for va in self.vent_amounts:
            probe["vent_amounts"].append({
                "vent_pressure": va.vent_pressure,
                "volume": va.volume
            })
            
        parameters = {
            "probe": probe,
            "key": frappe.get_value("HPT Settings", "HPT Settings", "hpt_api_key")
        }
        
        response = requests.post(
            "https://cloud.hpt.solutions/api/method/hptcloud.hptcloud.doctype.probe.probe.update_probe",
            json = parameters
        )
        
        if response.status_code != 200:
            frappe.log_error( "Probe upload failed with {0}".format(response.text), "HPT Upload failed")
        if 'error' in response.text:
            frappe.log_error( "Probe upload failed with {0}".format(response.json()['message']['error']), "HPT Upload failed")

        if debug:
            print(response.text)
        
        return
    
