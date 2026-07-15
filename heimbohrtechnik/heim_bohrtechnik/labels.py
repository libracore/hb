import frappe
from frappe import _
from erpnextswiss.erpnextswiss.doctype.label_printer.label_printer import create_pdf


@frappe.whitelist()
def get_label(item, label_type):
    #get label printer
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    hpt_settings = frappe.get_doc("HPT Settings", "HPT Settings")

    config_map = {
        "small": ("item_label_printer_small", "item_label_small.html", _("small")),
        "big": ("item_label_printer_big", "item_label_big.html", _("big")),
        "hpt": ("item_label_printer_big", "item_label_hpt.html", _("big"))
    }

    printer_field, label_template, error_label = config_map[label_type]
    
    label_printer = settings.get(printer_field)
    if not label_printer:
        frappe.throw(_("Please define a label printer for {0} article labels under Heim Settings").format(error_label))


    #get raw data
    item = frappe.get_doc("Item", item)
    data = {
        "item_code": item.item_code,
        "item_name": item.item_name,
    }

    frappe.msgprint("Label Printer: {0}".format(data))

    #prepare content

    if label_type == "hpt":
        data.update({
            "date": frappe.utils.formatdate(frappe.utils.today(), "dd.mm.yyyy"),
            "warehouse": hpt_settings.default_warehouse or ""
        })
    
    content = frappe.render_template("heimbohrtechnik/templates/labels/"+label_template, data)
    
    #create label
    printer=frappe.get_doc("Label Printer", label_printer)
    pdf = create_pdf(printer, content)

    #return download
    frappe.local.response.filename = "{name}.pdf".format(name=item.item_code + label_printer.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
