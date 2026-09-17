// Copyright (c) 2021-2026, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Truck Scale', {
    'refresh': function(frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Weight"), function() {
                get_weight(frm);
            });
            
            render_weight_chart(frm);
        }
    }
});

function get_weight(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.mudex.doctype.truck_scale.truck_scale.get_weight',
        'args': {
            'truck_scale': frm.doc.name
        },
        'callback': function(r) {
            if (typeof r.message !== 'undefined') {
                var html = __('Weight') + " " + r.message.weight + " kg";
                cur_frm.set_df_property('weight_html', 'options', html);
            } else {
                console.log("Invalid response");
            }
        }
    });
}

function render_weight_chart(frm) {
    const wrapper = frm.get_field('weight_chart_html').$wrapper;
    wrapper.empty();

    if (frm.is_new()) {
        wrapper.html('<p class="text-muted">Save the Truck Scale to see weight history.</p>');
        return;
    }
    
    frappe.db.get_list('Truck Scale Trace', {
        'filters': { truck_scale: frm.doc.name },
        'fields': ['weight', 'timestamp'],
        'order_by': 'timestamp asc',
        'limit': 1000
    }).then(records => {
        if (!records.length) {
            wrapper.html('<p class="text-muted">' + __("Noch keine Gewichte aufgezeichnet. Läuft der Agent?") + '</p>');
            return;
        }

        const labels = records.map(r => frappe.datetime.str_to_user(r.timestamp));
        const values = records.map(r => r.weight);
        
        new frappe.Chart(wrapper[0], {
            'title': __("Waagenlast"),
            'data': {
                'labels': labels,
                'datasets': [{ 'name': __("Gewicht (kg)"), 'values': values }]
            },
            'type': 'line',
            'height': 250,
            'colors': ['#5e64ff'],
            'lineOptions': { 'regionFill': 1 }
        });
    });
}
