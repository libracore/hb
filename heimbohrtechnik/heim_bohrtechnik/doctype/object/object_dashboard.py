# Copyright (c) 2021-2022, libracore AG and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
   return {
      'fieldname': 'object',
      'transactions': [
         {
            'label': _("Selling"),
            'items': ['Quotation', 'Sales Order', 'Sales Invoice']
         },
         {
            'label': _("Buying"),
            'items': ['Purchase Order', 'Purchase Receipt', 'Purchase Invoice']
         },
         {
            'label': _("Documentation"),
            'items': ['Construction Site Description', 'Bohranzeige', 'Construction Site Delivery', 'Subcontracting Order', 'Project', 'Layer Directory', 'Drilling Sample']
         },
         {
            'label': _("MudEX"),
            'items': ['Truck Delivery', 'Truck Planning']
         }
      ]
   }
