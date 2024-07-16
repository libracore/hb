import frappe
from frappe import _
from erpnextswiss.erpnextswiss.doctype.label_printer.label_printer import create_pdf


@frappe.whitelist()
def get_label(item, label_type):
    #get label printer
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    if label_type == "small":
        if not settings.item_label_printer_small:
            frappe.throw(_("Please define a label printer for small article labels under Heim Settings"))
        label_printer = settings.item_label_printer_small
        label_template = "item_label_small.html"
    elif label_type == "big":
        if not settings.item_label_printer_big:
            frappe.throw(_("Please define a label printer for big article labels under Heim Settings"))
        label_printer = settings.item_label_printer_big
        label_template = "item_label_big.html"


    #get raw data
    item = frappe.get_doc("Item", item)

    data = {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "price": item.standard_rate,
    }

    frappe.msgprint("Label Printer: {0}".format(data))

    #prepare content
    content = frappe.render_template("heimbohrtechnik/templates/labels/"+label_template, data)
    #create label
    printer=frappe.get_doc("Label Printer", label_printer)
    pdf = create_pdf(printer, content)

    #return download
    frappe.local.response.filename = "{name}.pdf".format(name=item.item_code + label_printer.replace(" ", "-").replace("/", "-"))
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
