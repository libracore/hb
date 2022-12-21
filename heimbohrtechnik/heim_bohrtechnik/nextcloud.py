# Copyright (c) 2022, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import os

"""
This function will create a new project folder with the required structure
"""
def create_project_folder(project):
    projects_folder = frappe.get_value("Heim Settings", "Heim Settings", "projects_folder")
    if not projects_folder:
        frappe.throw("Please configure the projects folder under Heim Settings", "Configuration missing")
        
    project_path = os.path.join(projects_folder, project)
    create_path(project_path)
    # create child folders
    create_path(os.path.join(project_path, "01_Fotos"))
    create_path(os.path.join(project_path, "02_Bohren"))
    create_path(os.path.join(project_path, "03_Anbindung"))
    create_path(os.path.join(project_path, "04_Lieferanten"))
    create_path(os.path.join(project_path, "05_Schadenfälle"))
    return
    
def create_path(path):
    # create project folder
    try:
        os.mkdir(path)
    except FileExistsError:
        pass
    except Exception as err:
        frappe.throw("{0}: {1}".format(path, err), "Create project folder (NextCloud")
    return
