# Copyright (c) 2024, libracore AG and contributors
# For license information, please see license.txt

from frappe import _

def get_data():
    return {
        'fieldname': 'subcontracting_order',
        'transactions': [
            {
                'label': _("Subcontracting Order Finish"),
                'items': ['Subcontracting Order Finish']
            }
        ]
    }
