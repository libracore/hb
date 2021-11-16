// Copyright (c) 2021, libracore AG and contributors
// For license information, please see license.txt
frappe.views.calendar["Truck Planning"] = {
    'field_map': {
        'start': 'start_time',
        'end': 'end_time',
        'id': 'name',
        'allDay': 'allDay',
        'child_name': 'truck',
        'title': 'object_details'
    },
    /*'options': {
        'header': {
            'left': 'prev,next today',
            'center': 'title',
            'right': 'month'
        }
    },*/
    'gantt': true,
    'filters': [
        {
            'fieldtype': 'Link',
            'fieldname': 'truck',
            'options': 'Truck',
            'label': __("Truck")
        },
        {
            'fieldtype': 'Link',
            'fieldname': 'object',
            'options': 'Object',
            'label': __("Object")
        }
    ],
    'get_events_method': "heimbohrtechnik.mudex.doctype.truck_planning.truck_planning.get_events"
};
