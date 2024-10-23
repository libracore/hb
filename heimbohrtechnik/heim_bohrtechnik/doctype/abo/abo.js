// Copyright (c) 2024, libracore AG and contributors
// For license information, please see license.txt

frappe.ui.form.on('Abo', {
	refresh: function(frm) {
        set_next_reminder_property(frm.doc.set_reminder_manually);
        
        if (!frm.doc.__islocal) {
            cur_frm.set_df_property('reminder_date', 'hidden', 1);
            frm.add_custom_button(__("Create Invoice"),  function(){
              create_invoice(frm);
            });
        }
        
        // libracore E-Mail Composer
        if (document.getElementsByClassName("fa-envelope-o").length === 0) {
            cur_frm.page.add_action_icon(__("fa fa-envelope-o"), function() {
                custom_mail_dialog(frm);
            });
            var target ="span[data-label='" + __("Email") + "']";
            $(target).parent().parent().remove();
        }
        
        if (frm.doc.customer) {
            frm.set_query('contact', function() {
                return {
                    filters: {
                        'link_doctype': 'Customer',
                        'link_name': frm.doc.customer
                    }
                };
            });
        }
	},
    set_reminder_manually: function(frm) {
        set_next_reminder_property(frm.doc.set_reminder_manually);
    },
    disabled: function(frm) {
        set_end_date(frm.doc.disabled);
    },
    before_save: function(frm) {
        if (frm.doc.__islocal) {
            set_next_reminder(frm);
        }
    },
    interval: function(frm) {
        if (!frm.doc.__islocal) {
            set_next_reminder(frm);
        }
    },
    contact: function(frm) {
        if (frm.doc.contact) {
            frappe.call({
                method: 'frappe.contacts.doctype.contact.contact.get_contact_details',
                args: {
                    contact: frm.doc.contact
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('contact_display', r.message.contact_display);
                    }
                }
            });
        }
    },
    customer: function(frm) {
        if (frm.doc.customer) {
            frm.set_query('contact', function() {
                return {
                    filters: {
                        'link_doctype': 'Customer',
                        'link_name': frm.doc.customer
                    }
                };
            });
        }
    }
});

function set_next_reminder_property(set_reminder_manually) {
    if (set_reminder_manually) {
        cur_frm.set_df_property('next_reminder', 'read_only', 0);
    } else {
        cur_frm.set_df_property('next_reminder', 'read_only', 1);
    }
}

function set_end_date(disabled) {
    if (disabled) {
        cur_frm.set_value('end_date', frappe.datetime.nowdate());
    } else {
        cur_frm.set_value('end_date', null);
    }
}

function set_next_reminder(frm) {
    if (!frm.doc.set_reminder_manually) {
        //set initial date
        let initial_date = frm.doc.last_reminder || frm.doc.reminder_date
        //set years to add
        let years = 0
        if (frm.doc.interval == "Yearly") {
            years = 1;
        } else if (frm.doc.interval == "Biannual") {
            years = 2;
        }
        //set next date
        let next_reminder = frappe.datetime.add_months(initial_date, years * 12);
        cur_frm.set_value("next_reminder", next_reminder);
    }
}

function create_invoice(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.abo.abo.create_invoice',
        'args': {
            'doc_name': frm.doc.name
        },
        'callback': function(response) {
            frappe.set_route("Form", "Sales Invoice", response.message);
        }
    });
}


function custom_mail_dialog(frm) {
    frappe.call({
        'method': 'heimbohrtechnik.heim_bohrtechnik.doctype.abo.abo.get_email_information',
        'args': {
            'contact': frm.doc.contact
        },
        'callback': function(response) {
            var recipient = response.message.recipient;
            var cc = response.message.cc;
            new frappe.erpnextswiss.MailComposer({
                doc: cur_frm.doc,
                frm: cur_frm,
                subject: "Abo " + cur_frm.doc.name,
                recipients: recipient,
                cc: cc,
                'email_template': "Nachfrage Abo",
                attach_document_print: false
            });
        }
    });
}

