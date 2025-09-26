// Copyright (c) 2021-2025, libracore AG and contributors
// For license information, please see license.txt
frappe.views.calendar["Construction Site Delivery"] = {
    'field_map': {
        'start': 'date',
        'end': 'to_date',
        'id': 'name',
        'allDay': 'allDay',
        'child_name': 'employee',
        'title': 'calendar_display'
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
            'fieldname': 'employee',
            'options': 'Employee',
            'label': __("Employee")
        },
        {
            'fieldtype': 'Link',
            'fieldname': 'object',
            'options': 'Object',
            'label': __("Object")
        }
    ],
    'get_events_method': "heimbohrtechnik.heim_bohrtechnik.doctype.construction_site_delivery.construction_site_delivery.get_events"
};
