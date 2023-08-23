# Copyright (c) 2022-2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import os
from webdav3.client import Client
from frappe.utils.password import get_decrypted_password
from frappe.desk.form.load import get_attachments
import time
from frappe.model.document import Document

PATHS = {
    'admin':            "1_Administration",
    'quotation':        "1_Administration/Angebot",
    'order':            "1_Administration/Auftrag",
    'invoice':          "1_Administration/Rechnung",
    'drilling':         "2_Bohren",
    'plan':             "3_Pläne",
    'road':             "4_Strassensperrung",
    'subprojects':      "5_Anbindung",
    'supplier':         "6_Lieferanten",
    'supplier_ews':     "6_Lieferanten/EWS",
    'supplier_mud':     "6_Lieferanten/Mulden_und_Saugwagen",
    'supplier_other':   "6_Lieferanten/Diverses",
    'incidents':        "7_Schadenfälle",
    'memo':             "8_Memos_und_Notizen"
}

def get_path(target):
    return PATHS[target]
    
"""
This is the authentication function
"""
def get_client():
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    password = get_decrypted_password("Heim Settings", "Heim Settings", "cloud_password")
    options = {
        'webdav_hostname': "{0}/remote.php".format(settings.cloud_hostname),
        'webdav_root': "files/",
        'webdav_login': settings.cloud_user,
        'webdav_password': password
    }
    client = Client(options)
    return client

"""
This function will create a new project folder with the required structure
"""
def create_project_folder(project):
    client = get_client()
    
    project_path = get_project_path(project)
    
    create_path(client, project_path)
    # create child folders
    create_path(client, os.path.join(project_path, PATHS['admin']))
    create_path(client, os.path.join(project_path, PATHS['quotation']))
    create_path(client, os.path.join(project_path, PATHS['order']))
    create_path(client, os.path.join(project_path, PATHS['invoice']))
    create_path(client, os.path.join(project_path, PATHS['drilling']))
    create_path(client, os.path.join(project_path, PATHS['plan']))
    create_path(client, os.path.join(project_path, PATHS['road']))
    create_path(client, os.path.join(project_path, PATHS['subprojects']))
    create_path(client, os.path.join(project_path, PATHS['supplier']))
    create_path(client, os.path.join(project_path, PATHS['supplier_ews']))
    create_path(client, os.path.join(project_path, PATHS['supplier_mud']))
    create_path(client, os.path.join(project_path, PATHS['supplier_other']))
    create_path(client, os.path.join(project_path, PATHS['incidents']))
    create_path(client, os.path.join(project_path, PATHS['memo']))
    return

def get_project_path(project):
    projects_folder = frappe.get_value("Heim Settings", "Heim Settings", "projects_folder")
    # only use base project folder (for split projects the first one
    project = project[:8] if len(project) >= 8 else project
    if not projects_folder:
        frappe.throw("Please configure the projects folder under Heim Settings", "Configuration missing")
        
    return os.path.join(projects_folder, project)

def get_base_path():
    projects_folder = frappe.get_value("Heim Settings", "Heim Settings", "projects_folder")
    return projects_folder
    
def create_path(client, path):
    # create project folder
    try:
        if not client.check(path):
            client.mkdir(path)
    except Exception as err:
        frappe.throw("{0}: {1}".format(path, err), "Create project folder (NextCloud")
    return

def write_file(project, f):
    return
    
"""
Write the project file (local file path) to nextcloud
"""
def write_project_file_from_local_file (project, file_name, target=PATHS['drilling']):
    client = get_client()
    project_path = get_project_path(project)
    if client.check(os.path.join(project_path, target)):
        client.upload_sync(os.path.join(project_path, target, file_name.split("/")[-1]), file_name)
    else:
        # fallback to root (for migration projects)
        client.upload_sync(os.path.join(project_path, file_name.split("/")[-1]), file_name)

    return

"""
Write the a local file (local file path) to the nextcloud base path (00_Projekte)
"""
def write_file_to_base_path(file_name):
    client = get_client()
    base_path = get_base_path()
    client.upload_sync(os.path.join(base_path, file_name.split("/")[-1]), file_name)
    return

"""
This function gets the cloud link to a project
"""
@frappe.whitelist()
def get_cloud_url(project):
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    # only use base project folder (for split projects the first one
    project = project[:8] if len(project) >= 8 else project
    return "{0}/index.php/apps/files/?dir=/{1}/{2}".format(settings.cloud_hostname, settings.projects_folder, project)

""" 
Extract the physical path from a file record
"""
def get_physical_path(file_name):
    file_url = frappe.get_value("File", file_name, "file_url")     # something like /private/files/myfile.pdf
    
    base_path = os.path.join(frappe.utils.get_bench_path(), "sites", frappe.utils.get_site_path()[2:])
    
    return "{0}{1}".format(base_path, file_url)
    
"""
Hook from File: upload specific files to nextcloud
"""
def upload_file(self, event):    
    if self.attached_to_doctype == "Bohranzeige":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        physical_file_name = get_physical_path(self.name)
        write_project_file_from_local_file (project, physical_file_name, PATHS['drilling'])
    
    elif self.attached_to_doctype == "Purchase Order":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            if frappe.get_value("Purchase Order", self.attached_to_name, "supplier") in ("L-80011", "L-80061"):
                write_project_file_from_local_file (project, physical_file_name, PATHS['supplier_ews'])
            else:
                write_project_file_from_local_file (project, physical_file_name, PATHS['supplier_other'])
    
    elif self.attached_to_doctype == "Quotation":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['quotation'])
            
    elif self.attached_to_doctype == "Sales Order":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['order'])
            
    elif self.attached_to_doctype == "Sales Invoice":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "object")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['invoice'])
    
    elif self.attached_to_doctype == "Project":
        #check if this file is an Attachment and not coming from a Subtable (plans or permits)
        if self.folder == "Home/Attachments":
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (self.attached_to_name, physical_file_name, PATHS['drilling'])
        else:
        #Because the File is not writen to the database yet, we are not able here to check if it is a plan or a permit(both are subtables)
        #Therefore this check will follow later in (see hooks.py "on_update project" and function "upload_project_file" below)
            pass
    
    elif self.attached_to_doctype == "Request for Public Area Use":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['road'])
        
    elif self.attached_to_doctype == "Subcontracting Order":
        project = frappe.get_value(self.attached_to_doctype, self.attached_to_name, "project")
        if frappe.db.exists("Project", project):
            physical_file_name = get_physical_path(self.name)
            write_project_file_from_local_file (project, physical_file_name, PATHS['subprojects'])
        
    return

"""
Write all attachments to nextcloud
"""
def upload_attachments(dt, dn, project):
    attachments = get_attachments(dt, dn)
    for a in attachments:
        physical_file_name = get_physical_path(a.get('file_name'))
        write_project_file_from_local_file (project, physical_file_name, PATHS['admin'])
    return
#check if the project subtable attachment is a plan or a permit and write it on the right place
def upload_project_file(project, event):
    project_old = project._doc_before_save
    if project.plans and project_old.plans:
        if len(project_old.plans) < len(project.plans):
            subtable = "plans"
            file_id = get_file_id(project, event, subtable)
            physical_file_name = get_physical_path(file_id)
            write_project_file_from_local_file (project.name, physical_file_name, PATHS['plan'])
        elif len(project_old.permits) < len(project.permits):
            subtable = "permits"
            file_id = get_file_id(project, event, subtable)
            physical_file_name = get_physical_path(file_id)
            write_project_file_from_local_file (project.name, physical_file_name, PATHS['drilling'])
    
def get_file_id(project, event, subtable):
    if subtable == "plans":
        url = project.plans[-1].file
    elif subtable == "permits":
        url = project.permits[-1].file
    sql_query = frappe.db.sql("""
    SELECT `name`
    FROM `tabFile`
    WHERE `file_url` = '{0}'""".format(url), as_dict=True)
    file_id = sql_query[0]['name']
    return file_id
    
    
