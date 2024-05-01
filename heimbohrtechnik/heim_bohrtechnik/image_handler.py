# Copyright (c) 2024, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from PIL import Image
import frappe
from frappe.utils import cint
from heimbohrtechnik.heim_bohrtechnik.nextcloud import get_physical_path
import os

def check_resize_image(filename, debug=False):
    # find settins
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    if not cint(settings.enable_image_resize) or not cint(settings.resize_to):
        if debug:
            print("Image resize disabled or not correctly configured.")
        return
        
    # open image in RGB mode
    im = Image.open(filename)
    
    # find size of image
    width, height = im.size
        
    # check if resize is required
    if width <= settings.resize_to and height <= settings.resize_to:
        if debug:
            print("Image already smaller, no resize required")
        return
    
    # find new dimension
    if width >= height:
        resize = settings.resize_to / width
        new_width = settings.resize_to
        new_height = cint(height * resize)
    else:
        resize = settings.resize_to / height
        new_height = settings.resize_to
        new_width = cint(width * resize)
    
    # resize
    if debug:
        print("Resize from {0}/{1} to {2}/{3}...".format(width, height, new_width, new_height))
    im = im.resize((new_width, new_height))
    
    # save
    im.save(filename)
    
    return

"""
Hook for newly uploaded files
"""
def check_new_image(self, event):
    # check file extension: only process png and jpg/jpeg
    if (self.file_name or "").lower()[-4:] not in [".jpg", ".png", "jpeg"]:
        return
        
    # find settins and check if this is enabled
    settings = frappe.get_doc("Heim Settings", "Heim Settings")
    if not cint(settings.enable_image_resize) or not cint(settings.resize_to):
        return
        
    # find physical path
    file_name = get_physical_path(self.name)
    
    # check and resize if required
    check_resize_image(file_name)
    
    return

"""
Migration process: find images > 1 MB and resize them

Run 
 $ bench execute heimbohrtechnik.heim_bohrtechnik.image_handler.find_and_resize_large_files
"""
def find_and_resize_large_files():
    # define site root
    base_path = os.path.join(frappe.utils.get_bench_path(), "sites", frappe.utils.get_site_path()[2:])
    
    # set public and private file path
    paths = [os.path.join(base_path, "public/files"), os.path.join(base_path, "private/files")]
    
    for path in paths:
        count = 0
        # find each file
        files = os.listdir(path)
        for f in files:
            full_name = os.path.join(path, f)
            print("{0}% done ({1})".format(cint(100 * count / len(files)), full_name))
            if f.lower()[-4:] in [".jpg", ".png", "jpeg"]:
                # this is an image
                check_resize_image(full_name, debug=True)
            
            count += 1
    
    return
