# Copyright (c) 2021-2022, libracore AG and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
   return {
      'fieldname': 'drilling_team',
      'transactions': [
         {
            'label': _("Projects"),
            'items': ['Project']
         }
      ]
   }
