# Copyright (c) 2022-2023, libracore and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import sys
import requests
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from frappe.utils.password import get_decrypted_password
from frappe.utils import cint

"""
Test: use
$ bench execute heimbohrtechnik.heim_bohrtechnik.doctype.timeshepherd_settings.test_timeshepherd_settings.test_absences

"""

def get_settings():
    return frappe.get_doc("Timeshepherd Settings", "Timeshepherd Settings")

def get_password():
    return get_decrypted_password("Timeshepherd Settings", "Timeshepherd Settings", "password")
    
def get_new_token():
    settings = get_settings()
    auth_server_url = "{0}/TS.DAS.Auth/connect/token".format(settings.host)
    scope = "openid profile offline_access timeshepherd"
    grant_type = "password"
    x_ts_client = "1"
    
    token_payload = {
        'grant_type': grant_type,
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'scope': scope,
        'username': settings.user_name,
        'password': get_password()
    }
    
    header = {
        'x-tx-client': x_ts_client
    }
    
    token_response = requests.post(auth_server_url,
        data=token_payload,
        verify=True if cint(settings.verify_ssl) else False,
        allow_redirects=False,
        auth=(settings.client_id, settings.client_secret)
    )
    
    if token_response.status_code != 200:
        frappe.log_error("Failed to obtain token from the OAuth 2.0 server: {1}: {1}".format(
            token_response.status_code, token_response.text), "Timeshepherd token failed")
        return None
    else:
        tokens = json.loads(token_response.text)
        return tokens['access_token']
        
def get_employees(only_active_ids=False):
    token = get_new_token()
    settings = get_settings()
    
    employees_raw = None
    
    while True:
        url = "{0}/TS.DAS.REST/api/v1/Employee/GetEmployees".format(settings.host)
        api_call_header = {
            'Authorization': 'Bearer ' + token
        }
        
        api_call_response = requests.get(url, 
            headers=api_call_header, 
            verify=True if cint(settings.verify_ssl) else False
        )
        
        if api_call_response.status_code == 401:
            token = get_new_token()
        else:
            employees_raw = json.loads(api_call_response.text)
            break
            
    if not employees_raw:
        return None
        
    if only_active_ids:
        active_ids = []
        for employee in employees_raw:
            if employee['isActive']:
                active_ids.append(employee['id'])
                
        return active_ids
    else:
        return employees_raw
        
def get_absences():
    token = get_new_token()
    settings = get_settings()
    employees = get_employees(only_active_ids=True)
    
    absences_raw = None
    
    while True:
        url = "{0}/TS.DAS.REST/api/v1/Absence/Search".format(settings.host)
        api_call_header = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        payload = {
            'dateFrom': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"), # "2023-04-01T00:00:00.000Z", #
            'dateTo': (datetime.now() + relativedelta(months=6)).strftime("%Y-%m-%dT%H:%M:%SZ"), # "2023-05-30T00:00:00.000Z", #
            'allEmployees': False,
            'employeeIds': employees,
            'suppressBookingDetails': False
        }
        
        api_call_response = requests.post(url, 
            headers=api_call_header, 
            json=payload,
            verify=True if cint(settings.verify_ssl) else False
        )
        
        if api_call_response.status_code == 401:
            token = get_new_token()
        else:
            absences_raw = json.loads(api_call_response.text)
            break
            
    if not absences_raw:
        return None
    
    print("{0}".format(absences_raw))
    # process absences:   
    if 'absencesEmployee' in absences_raw:
        absences = []
        for absence in absences_raw['absencesEmployee']:
            employee = {
                'id': absence['employee']['id'],
                'first_name': absence['employee']['firstName'],
                'last_name': absence['employee']['lastName'],
                'email': absence['employee']['email']
            }
            print("Employee: {0}".format(employee['first_name']))
            for day in absence['absences']:
                #print("{0}".format(day['booking']))
                if len(day['booking']) > 0:
                    absences.append({
                        'date': day['date'],
                        'absence_short': day['booking'][0]['bookingAccountShort'],              # FG
                        'absence_description': day['booking'][0]['bookingAccountDescription'],  # Ferien ganztags
                        'status': day['booking'][0]['workFlowAction'],                          # Approved
                        'absence_type': day['booking'][0]['type'],                              # Absent   
                        'employee': employee['id'],
                        'first_name': employee['first_name'],
                        'last_name': employee['last_name'],
                        'email': employee['email']            
                    })
        print("{0}".format(absences))
        return absences
        
    else:
        return None
    
    return
