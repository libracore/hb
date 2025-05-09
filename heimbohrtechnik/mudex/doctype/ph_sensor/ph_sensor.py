# -*- coding: utf-8 -*-
# Copyright (c) 2025, libracore AG and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint
from opcua import Client
from opcua import ua
from datetime import datetime
import traceback

SENSOR_ACTIVE_NODE = """\"COM__Waage_send\".\"ph Messung\".\"aktiv\""""
SENSOR_PH_NODE = """\"COM__Waage_send\".\"ph Messung\".\"Wert\""""
SENSOR_ID = 3

class pHSensor(Document):
    def read_sensor(self):
        # host should be a connection string like "opc.tcp://192.168.105.10:4840"
        if cint(self.enabled) and self.host:
            try:
                client = Client(self.host)
                client.connect()
                active_node = client.get_node(ua.NodeId(SENSOR_ACTIVE_NODE, SENSOR_ID))
                ph_node = client.get_node(ua.NodeId(SENSOR_PH_NODE, SENSOR_ID))
                self.sensor_active = cint(active_node.get_value())
                self.ph = flt(ph_node.get_value())
                self.timestamp = datetime.now()
                if self.sensor_active:
                    self.update_linked()
                    
                self.save(ignore_permissions=True)
                frappe.db.commit()
            except Exception as err:
                frappe.log_error( "{0}\n{1}".format(err, traceback.format_exc()), "Error reading pH Sensor {0}".format(self.name) )
        return
        
    def update_linked(self):
        if self.update_dt and self.update_dn:
            # store values
            linked_doc = frappe.get_doc(self.update_dt, self.update_dn)
            linked_doc.ph = self.ph
            linked_doc.save(ignore_permissions=True)
            # reset link fields to prevent iteration
            self.update_dt = None
            self.update_dn = None
        return

def read_sensors():
    enabled_sensors = frappe.get_all("pH Sensor", filters={'enabled': 1}, fields=['name'])
    for s in enabled_sensors:
        sensor = frappe.get_doc("pH Sensor", s['name'])
        sensor.read_sensor()
    return
