// Copyright (c) 2021-2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Construction Site Description', {
    onload: function(frm) {
        // filter for tractor suppliers
        cur_frm.fields_dict['tractor'].get_query = function(doc) {
             return {
                'query': 'heimbohrtechnik.heim_bohrtechnik.filters.supplier_by_capability',
                'filters': {
                    'capability': "Traktor"
                }
            }
        } 
    },
    refresh: function(frm) {
        // from object: link project
        if ((frm.doc.object) && (!frm.doc.project)) {
            cur_frm.set_value("project", frm.doc.object);
        }
        
        if (!frm.doc.__islocal) {
            frm.add_custom_button( __("Object") , function() {
                frappe.set_route("Form", "Object", frm.doc.object);
            }).addClass("btn-primary");
            
            frm.add_custom_button( __("Project") , function() {
                frappe.set_route("Form", "Project", frm.doc.project);
            }).addClass("btn-primary");
        
            frm.add_custom_button( __("Verlängerung") , function() {
                show_subcontracting_wizard(frm);
            }).addClass("btn-primary");
        }
    },
    before_save: function(frm) {
        if (!frm.doc.object_name) {
            autocomplete_object(frm);
        }
    },
    project: function(frm) {
        // from project: link object
        if ((!frm.doc.object) && (frm.doc.project)) {
            cur_frm.set_value("object", frm.doc.project);
            autocomplete_object(frm);
        }
    }
});

function autocomplete_object(frm) {
    frappe.call({
        'method': "frappe.client.get",
        'args': {
            'doctype': "Object",
            'name': frm.doc.object
        },
        'callback': function(response) {
            var object = response.message;
            cur_frm.set_value("object_name", object.object_name);
        }
    });
}

function show_subcontracting_wizard(frm) {
    let wizard = new frappe.ui.Dialog({
        'fields': [
            // ** Bohrpunkt Sondieren
            { 'fieldtype': "Section Break", 'fieldname': "sec_probing", 'label': __("Bohrpunkt Sondieren") },
            { 'fieldtype': "Data", 'fieldname': "remarks_probing", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_probing_1" },
            { 'fieldtype': "Check", 'fieldname': "do_probing", 'label': __("Bohrpunkt Sondieren") },
            { 'fieldtype': "Check", 'fieldname': "do_empty_tube", 'label': __("mit Leerrohr einbauen d300mm Rohr") },
            { 'fieldtype': "Column Break", 'fieldname': "col_probing_2" },
            { 'fieldtype': "Int", 'fieldname': "probe_count", 'label': __("Anzahl Sonden"), 'default': 1 },
            // ** Graben öffnen
            { 'fieldtype': "Section Break", 'fieldname': "sec_open_ditch", 'label': __("Graben öffnen") },
            { 'fieldtype': "Data", 'fieldname': "remarks_open_ditch", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_open_ditch_1" },
            { 'fieldtype': "Check", 'fieldname': "do_open_ditch", 'label': __("Graben öffnen und einsanden") },
            { 'fieldtype': "Column Break", 'fieldname': "col_open_ditch_2"},
            // ** Graben öffnen
            { 'fieldtype': "Section Break", 'fieldname': "sec_close_ditch", 'label': __("Graben öffnen") },
            { 'fieldtype': "Data", 'fieldname': "remarks_close_ditch", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_close_ditch_1" },
            { 'fieldtype': "Check", 'fieldname': "do_close_ditch", 'label': __("Graben schliessen, Grobplanie") },
            { 'fieldtype': "Column Break", 'fieldname': "col_close_ditch_2" },
            // ** Kernbohrung
            { 'fieldtype': "Section Break", 'fieldname': "sec_core", 'label': __("Kernbohrung") },
            { 'fieldtype': "Data", 'fieldname': "remarks_core", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_core_1" },
            { 'fieldtype': "Check", 'fieldname': "do_core_80", 'label': __("Ø 80mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_100", 'label': __("Ø 100mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_125", 'label': __("Ø 125mm") },
            { 'fieldtype': "Column Break", 'fieldname': "col_core_2" },
            { 'fieldtype': "Check", 'fieldname': "do_core_150", 'label': __("Ø 150mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_200", 'label': __("Ø 200mm") },
            { 'fieldtype': "Check", 'fieldname': "do_core_250", 'label': __("Ø 250mm") },
            // ** Pressringe
            { 'fieldtype': "Section Break", 'fieldname': "sec_core", 'label': __("Pressringe") },
            { 'fieldtype': "Data", 'fieldname': "remarks_pring", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_pring_1" },
            { 'fieldtype': "Check", 'fieldname': "do_pring_8050", 'label': __("Ø 80/50mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_10050", 'label': __("Ø 100/50mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_10063", 'label': __("Ø 100/63mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_10075", 'label': __("Ø 100/75mm") },
            { 'fieldtype': "Column Break", 'fieldname': "col_pring_2" },
            { 'fieldtype': "Check", 'fieldname': "do_pring_12575", 'label': __("Ø 125/75mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_150250", 'label': __("Ø 150/2x50mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_15075", 'label': __("Ø 150/75mm") },
            { 'fieldtype': "Check", 'fieldname': "do_pring_15090", 'label': __("Ø 150/90mm") },
            // ** Verlängerung
            { 'fieldtype': "Section Break", 'fieldname': "sec_long", 'label': __("Verlängerung") },
            { 'fieldtype': "Data", 'fieldname': "remarks_long", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_long_1" },
            { 'fieldtype': "Check", 'fieldname': "do_long_404050H", 'label': __("40/40/50 Verlängern bis Hauseintritt") },
            { 'fieldtype': "Check", 'fieldname': "do_long_323240H", 'label': __("32/32/40 Verlängern bis Hauseintritt") },
            { 'fieldtype': "Check", 'fieldname': "do_long_404050V", 'label': __("40/40/50 Verlängern bis Verteiler/Sammler im Haus") },
            { 'fieldtype': "Check", 'fieldname': "do_long_323240V", 'label': __("32/32/40 Verlängern bis Verteiler/Sammler im Haus") },
            { 'fieldtype': "Column Break", 'fieldname': "col_long_2" },
            { 'fieldtype': "Select", 'fieldname': "long_diameter", 'options': "\nd50mm\nd63mm\nd75mm\nd90mm\nd110mm\nd140mm\nd160mm\nd180mm\nd200mm\nd220mm\nd250mm", 'label': __("Hauptleitung bis Eintritt oder Zwischenraum verlegen") },
            { 'fieldtype': "Int", 'fieldname': "long_meter", 'label': __("Laufmeter"), 'default': 1 },
            // ** Anlage befüllen
            { 'fieldtype': "Section Break", 'fieldname': "sec_fill", 'label': __("Anlage befüllen") },
            { 'fieldtype': "Data", 'fieldname': "remarks_fill", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_fill_1" },
            { 'fieldtype': "Check", 'fieldname': "do_fill_water", 'label': __("Anlage mit Wasser befüllen") },
            { 'fieldtype': "Check", 'fieldname': "do_fill_glycol", 'label': __("Anlage mit Glykol befüllen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_fill_2" },
            { 'fieldtype': "Select", 'fieldname': "fill_ethglyn", 'options': "\n20%\n25%\n30%", 'label': __("Ethylenglykol N (Konzentrat)") },
            { 'fieldtype': "Select", 'fieldname': "fill_ethglyl", 'options': "\n20%\n25%\n30%", 'label': __("Ethylenglykol L (Konzentrat)") },
            // ** Wandbox / Rundschacht
            { 'fieldtype': "Section Break", 'fieldname': "sec_wall", 'label': __("Wandbox / Rundschacht") },
            { 'fieldtype': "Data", 'fieldname': "remarks_wall", 'label': __("Bemerkungen") },
            { 'fieldtype': "Column Break", 'fieldname': "col_wall_1" },
            { 'fieldtype': "Check", 'fieldname': "do_wall_box", 'label': __("Wandbox") },
            { 'fieldtype': "Select", 'fieldname': "wall_box_type", 'options': "\n2-Fach\n3-Fach\n4-Fach\n5-Fach", 'label': __("Wandboxart") },
            { 'fieldtype': "Check", 'fieldname': "do_mount", 'label': __("Montageblock") },
            { 'fieldtype': "Select", 'fieldname': "mount_type", 'options': "\n2-Fach\n3-Fach\n4-Fach\n5-Fach", 'label': __("Montageblockart") },
            { 'fieldtype': "Column Break", 'fieldname': "col_wall_2" },
            { 'fieldtype': "Check", 'fieldname': "do_round_shaft", 'label': __("Rundschacht") },
            { 'fieldtype': "Select", 'fieldname': "round_shaft_type", 'options': "\n2-Fach\n3-Fach\n4-Fach\n5-Fach", 'label': __("Rundschachtart") },
            { 'fieldtype': "Check", 'fieldname': "do_passable", 'label': __("Befahrbar") }
        ],
        'primary_action': function() {
            
        },
        'primary_action_label': __("OK"),
        'title': __("Verlängerungs-Assistent")
    });
    wizard.show();
    
    setTimeout(function () {
        var modals = document.getElementsByClassName("modal-dialog");
        if (modals.length > 0) {
            modals[modals.length - 1].style.width = "1000px";
        }
    }, 300);

}
