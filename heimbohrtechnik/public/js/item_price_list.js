// Copyright (c) 2022, libracore and contributors
// For license information, please see license.txt

frappe.listview_settings['Item Price'] = {
    onload: function(listview) {
        listview.page.add_menu_item(__("Preismutation"), function() {
            var selected = listview.get_checked_items();
            mutate_prices(selected);
        });
    }
};

function mutate_prices(selected) {
    frappe.prompt([
        {'fieldname': 'discount', 'fieldtype': 'Percent', 'label': 'Rabatt', 'reqd': 1, 'description': 'Z.B. -12%'},
        {'fieldname': 'markup', 'fieldtype': 'Percent', 'label': 'Zuschlag', 'reqd': 1, 'description': 'Z.B. 9%'}
    ],
    function(values){
        frappe.call({
                'method': "heimbohrtechnik.heim_bohrtechnik.utils.mutate_prices",
                'args':{
                    'selected': selected,
                    'discount': values.discount,
                    'markup': values.markup
                },
                'callback': function(r)
                {
                    frappe.show_alert( __("Fertig") );
                }
        });
    },
    __('Preismutation'),
    __('Anwenden')
    )
}
