# Copyright (c) 2021, libracore AG and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
   return {
      'fieldname': 'truck_delivery',
      'transactions': [
         {
            'label': _("Selling"),
            'items': ['Sales Invoice']
         }
      ]
   }
