// Copyright (c) 2022-2023, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subcontracting Order', {
    refresh: function(frm) {
        // filters
        cur_frm.fields_dict['drilling_team'].get_query = function(doc) {
             return {
                 filters: {
                     "drilling_team_type": "Verlängerungsteam"
                 }
             }
        }
        
        // Render Subcontracting Gant-Like HTML View
        render_gant(frm);

        // from object: new bohranzeige: link project
        if ((frm.doc.object) && (!frm.doc.project)) {
            cur_frm.set_value("project", frm.doc.object);
        }
        
        // create pdf with plans
        frm.add_custom_button(__("PDF mit Werkleitungen"), function() {
            create_full_pdf(frm);
        });
        
        // load template
        frm.add_custom_button(__("Vorlage"), function() {
            from_template(frm);
        });
        
        // pull items
        frm.add_custom_button(__("Artikel holen"), function() {
            pull_items(frm);
        });
        
        // create finish document
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__("Abschluss"), function() {
                open_create_finish(frm);
            });
        }
    },
    before_save: function(frm) {
        if (!frm.doc.object_name) {
            autocomplete_object(frm);
        }
    },
    project: function(frm) {
        if (frm.doc.project) {
            find_object(frm, frm.doc.project);
        }
    },
    to_date: function(frm) {
        if (frm.doc.from_date > frm.doc.to_date) {
            cur_frm.set_value("from_date", frm.doc.to_date);
        }
    },
    from_date: function(frm) {
        if (frm.doc.from_date > frm.doc.to_date) {
            cur_frm.set_value("to_date", frm.doc.from_date);
        }
    }
});

function find_object(frm, project) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Project",
            'name': project
        },
        'callback': function(response) {
            var project = response.message;
            cur_frm.set_value("object", project.object);
            autocomplete_object(frm);
        }
    });
}

function autocomplete_object(frm) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Object",
            'name': frm.doc.object || frm.doc.project
        },
        'callback': function(response) {
            var object = response.message;
            cur_frm.set_value("object_name", object.object_name);
            cur_frm.set_value("object_street", object.object_street);
            cur_frm.set_value("object_location", object.object_location);
            if (!frm.doc.object) {
                cur_frm.set_value("object", object.name);
            }
        }
    });
}

function create_full_pdf(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.utils.create_subcontracting_order_pdf',
        'args': {'subcontracting_order': frm.doc.name},
        'callback': function(response) {
            cur_frm.reload_doc();
        },
        'freeze': true,
        'freeze_message': __("PDF mit Werkplänen erstellen, bitte warten...")
    });
}

function from_template(frm) {
    // find all templates
    frappe.call({
        'method': "frappe.client.get_list",
        'args': {
            'doctype': "Subcontracting Order Template"
        },
        'callback': function(response) {
            // dialog to select template
            var templates = response.message;
            var options = [];
            for (var i = 0; i < templates.length; i++) {
                options.push(templates[i].name);
            }
            var d = new frappe.ui.Dialog({
                'fields': [
                    {'fieldname': 'template', 'fieldtype': 'Select', 'label': __("Vorlage"), "options": options.join("\n")}
                ],
                'primary_action': function(){
                    d.hide();
                    // load template
                    frappe.call({
                        'method': 'frappe.client.get',
                        'args': {
                            'doctype': "Subcontracting Order Template",
                            'name': d.get_values().template
                        },
                        'callback': function(response) {
                            // apply template
                            var template = response.message;
                            if (template.drilling_team) { cur_frm.set_value("drilling_team", template.drilling_team); }
                            if (template.order_description) { cur_frm.set_value("order_description", template.order_description); }
                            if (template.prio) { cur_frm.set_value("prio", template.prio); }
                            if (template.remarks) { cur_frm.set_value("remarks", template.remarks); }
                            for (var i = 0; i < template.items.length; i++) {
                                var child = cur_frm.add_child('items');
                                frappe.model.set_value(child.doctype, child.name, 'qty', template.items[i].qty);
                                frappe.model.set_value(child.doctype, child.name, 'description', template.items[i].description);
                            }
                            cur_frm.refresh_field('items');
                        }
                    });
                },
                'primary_action_label': __('Vorlage anwenden'),
                'title': __("Vorlage")
            });
            d.show();
        }
    });
}

function pull_items(frm) {
    frappe.call({
        'method': 'get_bkps',
        'doc': frm.doc,
        'callback': function(response) {
            var bkps = response.message;
            // show dialog to select bkp
            if ((bkps) && (bkps.length > 0)) {
                frappe.prompt([
                        {
                            'fieldname': 'bkp', 
                            'fieldtype': 'Select', 
                            'label': 'BKP', 
                            'options': bkps.join("\n"), 
                            'reqd': 1,
                            'default': "06"
                        }  
                    ],
                    function(values){
                        // fetch items and insert
                        frappe.call({
                            'method': 'get_bkp_items',
                            'doc': frm.doc,
                            'args': {
                                'bkp': values.bkp
                            },
                            'callback': function(response) {
                                var items = response.message;
                                for (var i = 0; i < items.length; i++) {
                                    var child = cur_frm.add_child('sales_order_items');
                                    frappe.model.set_value(child.doctype, child.name, 'item_code', items[i].item_code);
                                    frappe.model.set_value(child.doctype, child.name, 'item_name', items[i].item_name);
                                    frappe.model.set_value(child.doctype, child.name, 'qty', items[i].qty);
                                    frappe.model.set_value(child.doctype, child.name, 'rate', items[i].base_net_rate);
                                    frappe.model.set_value(child.doctype, child.name, 'amount', items[i].base_net_amount);
                                    frappe.model.set_value(child.doctype, child.name, 'subcontracting_amount', items[i].base_net_amount * ((100 - cur_frm.doc.margin) / 100));
                                }
                                cur_frm.refresh_fields("sales_order_items");
                            }
                        });
                    },
                    __('Position aus AB importieren'),
                    __('Importieren')
                );
            } else {
                frappe.msgprint( __("Keine Auftragsdaten gefunden."), __("Information") );
            }
        }
    });
}

function open_create_finish(frm) {
    // check if there are existing records
    frappe.call({
        'method': "frappe.client.get_list",
        'args': {
            'doctype': "Subcontracting Order Finish",
            'filters': {
                'project': frm.doc.project
            }
        },
        'callback': function(response) {
            console.log(response.message);
            if (response.message.length > 0) {
                // open existing record
                frappe.set_route("Form", "Subcontracting Order Finish", response.message[0].name);
            } else {
                // create a new record
                frappe.call({
                    'method': "make_finish",
                    'doc': cur_frm.doc,
                    'callback': function(r)
                    {
                        console.log(r);
                        frappe.set_route("Form", "Subcontracting Order Finish", r.message.name);
                    }
                });
            }
        }
    });
}

function render_gant(frm) {
    frappe.call({
        'method': 'get_gant_data',
        'doc': frm.doc,
        'callback': function(r) { 
            renderTimeline(r.message);
        }
    });
}

function renderTimeline(data){
    // Funktion zur Visualisierung der vorgängig aufbereiteten Daten
    const cols = data.days.length;

    // Header Zeile
    const header = [
        `<div class="subcontract-gant-header" style="--cols:${cols}">`,
        ...data.days.map(d => `<div class="subcontract-gant-col-day${d.is_today?' is-today':''}">${frappe.utils.escape_html(d.label)}</div>`),
        `</div>`
    ].join('');

    // Gant-Einträge
    const gant_entries = (data.render_data || []).map(t => {
        const startCol = t.render_start_col;
        const span = (t.render_span ?? 1);
        const css_klassen = [
            "subcontract-gant-task",
            (t.current ? 'current':''),
            (t.is_subcontract ? 'is-subcontract':'')
        ].filter(Boolean).join(' ');
        const style = `grid-column:${startCol} / span ${span}; --lane:${t.lane || 0};`;
        const tooltip = frappe.utils.escape_html(t.tooltip || '');
        const url = `/desk#Form/${encodeURIComponent(t.doctype)}/${encodeURIComponent(t.docname)}`;

        return `
            <a href="${url}"
                class="${css_klassen}"
                style="${style}"
                data-tooltip="${frappe.utils.escape_html(t.tooltip || t.label || '')}">
                ${t.label || ''}
            </a>`;
    }).join('');

    const row = `<div class="subcontract-gant-row" style="--cols:${cols}">${gant_entries}</div>`;
    const $container = $(`<div class="subcontract-gant-wrapper">${[header, row].join('')}</div>`);

    setupFloatingTooltip($container);
}

function setupFloatingTooltip($root){
    // Hilfsfunktion zum erstellen eines Tootip Containers relativ zum Body
    let tipEl = null;
    let hideTimer = null;

    const showTip = (text, x, y) => {
        if (!tipEl) {
            tipEl = document.createElement('div');
            tipEl.className = 'subcontract-gant-float-tip';
            document.body.appendChild(tipEl);
        }
        tipEl.textContent = text;
        positionTip(x, y);
        requestAnimationFrame(() => tipEl.classList.add('show'));
    };

    const hideTip = () => {
        if (!tipEl) return;
        tipEl.classList.remove('show');
        clearTimeout(hideTimer);
        hideTimer = setTimeout(() => {
            if (tipEl && !tipEl.classList.contains('show')) {
            tipEl.remove();
            tipEl = null;
            }
        }, 150);
    };

    const positionTip = (x, y) => {
        if (!tipEl) return;
        const pad = 10;
        let left = x + pad;
        let top  = y + pad;

        const rect = tipEl.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        if (left + rect.width + 8 > vw) left = vw - rect.width - 8;
        if (top + rect.height + 8 > vh) top = y - rect.height - pad;

        tipEl.style.left = `${left}px`;
        tipEl.style.top  = `${top}px`;
    };

    // Events-Handler für Tasks-Tooltips
    $root.on('mouseenter', '.subcontract-gant-task', function (ev) {
        const text = this.getAttribute('data-tooltip') || this.textContent || '';
        showTip(text, ev.clientX, ev.clientY);
    });
    $root.on('mousemove', '.subcontract-gant-task', function (ev) {
        positionTip(ev.clientX, ev.clientY);
    });
    $root.on('mouseleave', '.subcontract-gant-task', function () {
        hideTip();
    });

    window.addEventListener('scroll', () => hideTip(), { passive: true });
    window.addEventListener('resize', () => hideTip());

    show_gant($root);
}

function show_gant(gant) {
    cur_frm.set_df_property('gant_like_html', 'options', gant);
}