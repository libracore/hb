# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and Contributors
# See license.txt
from __future__ import unicode_literals

# import frappe
import unittest
from heimbohrtechnik.heim_bohrtechnik.timeshepherd import get_absences, get_employees

class TestTimeshepherdSettings(unittest.TestCase):
	pass

def test_employees():
    employees = get_employees()
    
    for employee in employees:
        print("{0}: {1} {2}".format(employee['id'], employee['firstName'].strip(), employee['lastName'].strip()))
        
    return
    
def test_absences():
    absences = get_absences()
    
    for absence in absences:
        print("{0}".format(absence))
        
    return
