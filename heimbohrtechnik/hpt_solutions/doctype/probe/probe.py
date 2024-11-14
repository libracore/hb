# -*- coding: utf-8 -*-
# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests

class Probe(Document):
    def post_probe_to_hpt_cloud(self):
        """
        Transmit this probe to the HPT cloud
        """
        probe_dict = self.as_dict()
        
        response = requests.post(
            "https://cloud.hpt.solutions/api/method/hptcloud.hptcloud.doctype.probe.probe.update_probe",
            json = {
                'probe': probe_dict,
                'key': frappe.get_value("HPT Settings", "HPT Settings", "hpt_api_key")
            }
        )
        
        if response.status_code != 200:
            frappe.log_error( "Probe upload failed with {0}".format(response.text), "HPT Upload failed")
            
        return
    
