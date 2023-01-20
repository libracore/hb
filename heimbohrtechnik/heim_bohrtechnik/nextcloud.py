# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import os
from webdav3.client import Client
from frappe.utils.password import get_decrypted_password

PATHS = {
    'images': "01_Fotos",
    'plan': "02_Werkpläne",
    'road': "03_Strassensperrung",
    'drilling': "04_Bohren",
    'subprojects': "05_Anbindung",
    'supplier': "06_Lieferanten",
    'incidents': "07_Schadenfälle",
    'admin': "08_Administration"
}

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
    create_path(client, os.path.join(project_path, PATHS['images']))
    create_path(client, os.path.join(project_path, PATHS['plan']))
    create_path(client, os.path.join(project_path, PATHS['road']))
    create_path(client, os.path.join(project_path, PATHS['drilling']))
    create_path(client, os.path.join(project_path, PATHS['subprojects']))
    create_path(client, os.path.join(project_path, PATHS['supplier']))
    create_path(client, os.path.join(project_path, PATHS['incidents']))
    create_path(client, os.path.join(project_path, PATHS['admin']))
    return

def get_project_path(project):
    projects_folder = frappe.get_value("Heim Settings", "Heim Settings", "projects_folder")
    if not projects_folder:
        frappe.throw("Please configure the projects folder under Heim Settings", "Configuration missing")
        
    return os.path.join(projects_folder, project)
    
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
def write_project_file_from_local_file (project, file_name):
    client = get_client()
    project_path = get_project_path(project)
    try:
        client.upload_sync(os.path.join(project_path, PATHS['drilling'], file_name.split("/")[-1]), file_name)
    except:
        # fallback to root (for migartion projects)
        try:
            client.upload_sync(os.path.join(project_path, file_name.split("/")[-1]), file_name)
        except Exception as err:
            frappe.log_error( err, "Nextcloud: {0} project file cannot be uploaded".format(project) )
    return
    
"""
This function gets the cloud link to a project
"""
@frappe.whitelist()
def get_cloud_url(project):
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    return "{0}/index.php/apps/files/?dir=/{1}/{2}".format(settings.cloud_hostname, settings.projects_folder, project)

""" 
Extract the physical path from a file record
"""
def get_physical_path(file_name):
    file_url = frappe.get_value("File", file_name, "file_url")     # something like /private/files/myfile.pdf
    
    base_path = os.path.join(frappe.utils.get_bench_path(), "sites", frappe.utils.get_site_path()[2:])
    
    return "{0}{1}".format(base_path, file_url)
    
