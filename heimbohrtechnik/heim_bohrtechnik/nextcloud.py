# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import os
from webdav3.client import Client
from frappe.utils.password import get_decrypted_password

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
    projects_folder = frappe.get_value("Heim Settings", "Heim Settings", "projects_folder")
    if not projects_folder:
        frappe.throw("Please configure the projects folder under Heim Settings", "Configuration missing")
        
    project_path = os.path.join(projects_folder, project)
    create_path(client, project_path)
    # create child folders
    create_path(client, os.path.join(project_path, "01_Fotos"))
    create_path(client, os.path.join(project_path, "02_Bohren"))
    create_path(client, os.path.join(project_path, "03_Anbindung"))
    create_path(client, os.path.join(project_path, "04_Lieferanten"))
    create_path(client, os.path.join(project_path, "05_Schadenfälle"))
    return
    
def create_path(client, path):
    # create project folder
    try:
        if not client.check(path):
            client.mkdir(path)
    except Exception as err:
        frappe.throw("{0}: {1}".format(path, err), "Create project folder (NextCloud")
    return

"""
This function gets the cloud link to a project
"""
@frappe.whitelist()
def get_cloud_url(project):
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    return "{0}/index.php/apps/files/?dir=/{1}/{2}".format(settings.cloud_hostname, settings.projects_folder, project)
