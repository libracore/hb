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

From Console:
$ bench execute heimbohrtechnik.heim_bohrtechnik.timeshepherd.sync_timeshepherd_ids
$ bench execute heimbohrtechnik.heim_bohrtechnik.timeshepherd.sync_leave_applications

"""

def get_settings():
    return frappe.get_doc("Timeshepherd Settings", "Timeshepherd Settings")

def get_password():
    return get_decrypted_password("Timeshepherd Settings", "Timeshepherd Settings", "password")
    
def get_new_token():
    if not cint(frappe.get_value("Timeshepherd Settings", "Timeshepherd Settings", "enabled")):
        print("Timeshepherd disabled")
        return
        
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
        
"""
Fetch employees from timeshepherd

Structure:
    {
        'id': <id>,
        'isActive': True/False,
        'firstName': <first_name>,
        'lastName': <last_name>,
        'eMail': <email>,
        'workingHours': <hours>,
        'holidayEntitlement': <days>,
        'balances': None
    }
    
"""
def get_employees(only_active_ids=False):
    if not cint(frappe.get_value("Timeshepherd Settings", "Timeshepherd Settings", "enabled")):
        print("Timeshepherd disabled")
        return
        
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
        
def get_absences(debug=False):
    if not cint(frappe.get_value("Timeshepherd Settings", "Timeshepherd Settings", "enabled")):
        print("Timeshepherd disabled")
        return
        
    token = get_new_token()
    settings = get_settings()
    employees = get_employees(only_active_ids=True)
    
    absences = []
    
    absences = get_absence_page(settings=settings, token=token, employees=employees, 
        from_date=datetime.now(), to_date=(datetime.now() + relativedelta(months=(settings.fetch_months or 12))))
    
    """
    Pagination
    """
    """
    # use pagination because otherwise the API overloads
    from_date = datetime.now()
    to_date = from_date
    
    for employee in employees:
        for i in range(1, 7):
            from_date = to_date
            to_date = (from_date + relativedelta(months=1))
            _absences = get_absence_page(settings=settings, token=token, employees=[employee], 
                from_date=from_date, to_date=to_date)
            if _absences:
                for absence in _absences:
                    absences.append(absence)
    """
    
    # consolidate to blocks rather than single days
    absences = consolidate_absences(absences, debug)
    
    return absences

def get_absence_page(settings, token, employees, from_date, to_date):
    if not cint(frappe.get_value("Timeshepherd Settings", "Timeshepherd Settings", "enabled")):
        print("Timeshepherd disabled")
        return
        
    absences_raw = None
    while True:
        url = "{0}/TS.DAS.REST/api/v1/Absence/Search".format(settings.host)
        api_call_header = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        payload = {
            'dateFrom': from_date.strftime("%Y-%m-%dT00:00:00.000Z"), 
            'dateTo': to_date.strftime("%Y-%m-%dT23:59:00.000Z"), 
            'allEmployees': False,
            'employeeIds': employees,
            'suppressBookingDetails': False
        }
        
        print("{0}".format(payload))
        
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
            for day in absence['absences']:
                if len(day['booking']) > 0 and day['booking'][0]['bookingAccountDescription'] != "Geht":
                    absences.append({
                        'date': day['date'][0:10],
                        'absence_short': day['booking'][0]['bookingAccountShort'],              # FG
                        'absence_description': day['booking'][0]['bookingAccountDescription'],  # Ferien ganztags
                        'status': day['booking'][0]['workFlowStatus'],                          # Approved
                        'absence_type': day['booking'][0]['type'],                              # Absent   
                        'employee': employee['id'],
                        'first_name': employee['first_name'],
                        'last_name': employee['last_name'],
                        'email': employee['email']            
                    })
        
        return absences
        
    else:
        return None

"""
This function will combine the individual days into absence blocks
"""
def consolidate_absences(absences, debug=False):
    consolidated = []
    last_date = None
    current_absence = None
    for absence in absences:
        date = datetime.strptime(absence['date'], "%Y-%m-%d")
        if debug:
            print("next entry: employee {0}: date {1} (previous: {2}, {3})".format(
                absence['employee'], date, current_absence['employee'] if current_absence else "-", last_date))
        # start a new block
        if not current_absence:
            # first run, initialise
            last_date = date
            current_absence = {
                'from_date': date,
                'employee': absence['employee'],
                'to_date': date,
                'absence_description': absence['absence_description'],
                'status': absence['status']
            }
        else:
            # check if this was the previous day
            if (date - last_date).days == 1 and absence['employee'] == current_absence['employee']:
                # this is the following day
                last_date = date
                current_absence['to_date'] = date
                # override status and absence type in case of holidays
                if absence['status'] != "None" and absence['status'] != current_absence['status']:
                    current_absence['status'] = absence['status']
                if absence['absence_description'] != "Feiertag" and absence['absence_description'] != current_absence['absence_description']:
                    current_absence['absence_description'] = absence['absence_description']
            else:
                # more than one day apart or different employee: store current and start new
                if current_absence:
                    consolidated.append(current_absence)
                    if debug:
                        print("Store {0}".format(current_absence))
                last_date = date
                current_absence = {
                    'from_date': date,
                    'employee': absence['employee'],
                    'to_date': date,
                    'absence_description': absence['absence_description'],
                    'status': absence['status']
                }
    # finalise: add last record
    if current_absence:
        consolidated.append(current_absence)
    return consolidated

"""
Read absences and transform to leave applications
"""
def sync_leave_applications():
    absences = get_absences()

    for absence in absences:
        if absence['status'] == "Approved":                 # only take approved absences
            # find employee
            employee_matches = frappe.get_all("Employee", 
                filters={'timeshepherd_id': absence['employee'], 'status': 'Active'},
                fields=['name']
            )
            if len(employee_matches) > 0:
                # verify if this leave is already recorded
                leave_matches = frappe.get_all("Leave Application",
                    filters=[
                        ['employee', '=', employee_matches[0]['name']],
                        ['from_date', '=', absence['from_date']],
                        ['to_date', '=', absence['to_date']],
                        ['docstatus', '<', 2]
                    ],
                    fields=['name']
                )
                
                if len(leave_matches) > 0:
                    # existing leave
                    leave = frappe.get_doc("Leave Application", leave_matches[0]['name'])
                    
                else:
                    # make sure leave type exists
                    if not frappe.db.exists("Leave Type", absence['absence_description']):
                        leave_type = frappe.get_doc({
                            'doctype': "Leave Type",
                            'leave_type_name': absence['absence_description'],
                            'allow_negative': 1,            # allow negative balance to circumvent leave allocation
                            'include_holiday': 0
                        })
                        leave_type.insert()
                        frappe.db.commit()
                    
                    # check and cancel overlaps
                    check_resolve_overlaps(employee=employee_matches[0]['name'], 
                        from_date=absence['from_date'], to_date=absence['to_date'])
                    
                    # create leave
                    new_leave = frappe.get_doc({
                        'doctype': "Leave Application",
                        'employee': employee_matches[0]['name'],
                        'from_date': absence['from_date'],
                        'to_date': absence['to_date'],
                        'leave_type': absence['absence_description']
                    })
                    try:
                        new_leave.insert()
                    except Exception as err:
                        if absence['from_date'] != datetime.today().strftime("%Y-%m-%d"):     # skip insert errors from today (ongoing leaves)
                            frappe.log_error("Unable to insert: {0}: {1}".format(new_leave.as_dict(), err), "Timeshepherd leave sync")
                    frappe.db.commit()
        
    return
    
"""
Read timesheet user ids and match to employees
"""
def sync_timeshepherd_ids():
    employees = get_employees()
    
    for employee in employees:
        first_name = (employee['firstName'] or "").strip()
        last_name = (employee['lastName'] or "").strip()
        employee_matches = frappe.get_all("Employee", 
            filters={
                'first_name': first_name,
                'last_name': last_name,
                'status': 'Active'
            },
            fields=['name']
        )
        
        if len(employee_matches) == 1:
            employee_doc = frappe.get_doc("Employee", employee_matches[0]['name'])
            employee_doc.timeshepherd_id = employee['id']
            employee_doc.save()
            frappe.db.commit()
        elif len(employee_matches) == 0:
            print("No matches for {0} ({1} {2})".format(employee['id'], first_name, last_name))
        else:
            print("Multiple matches for {0} ({1} {2})".format(employee['id'], first_name, last_name))
    
    return

"""
Check if there is already a leave application and cancel this
"""
def check_resolve_overlaps(employee, from_date, to_date):
    # find overlaps
    for d in frappe.db.sql("""
        SELECT `name`, `from_date`, `to_date`
        FROM `tabLeave Application`
        WHERE `employee` = "{employee}"
          AND `docstatus` < 2
          AND `status` IN ("Open", "Approved")
          AND `to_date` >= "{from_date}"
          AND `from_date` <= "{to_date}";
        """.format(employee=employee, from_date=from_date, to_date=to_date), as_dict=True):
        
        # do not cancel started ongoing leave (otherwise it shortens every day)
        if d['from_date'] <= datetime.today().date() and d['to_date'] >= datetime.today().date():
            continue
            
        # push to cancelled stage
        frappe.db.sql("""
            UPDATE `tabLeave Application`
            SET `docstatus` = 2
            WHERE `name` = "{name}";
            """.format(name=d['name']))
    
    return

""" 
This function will check if a customer exists and return its ID
"""
def check_customer(customer_name):
    if not cint(frappe.get_value("Timeshepherd Settings", "Timeshepherd Settings", "enabled")):
        print("Timeshepherd disabled")
        return
        
    token = get_new_token()
    settings = get_settings()
    
    customers_raw = None
    
    while True:
        url = "{0}/TS.DAS.REST/api/v1/Customer/Search".format(settings.host)
        api_call_header = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        payload = {
            "searchTerm": customer_name,
            "skip": 0,
            "take": 30,
            "sortBy": None,
            "searchFilters": []
        }

        api_call_response = requests.post(
            url,
            json=payload, 
            headers=api_call_header, 
            verify=True if cint(settings.verify_ssl) else False
        )
        
        if api_call_response.status_code == 401:
            token = get_new_token()
        else:
            customers_raw = json.loads(api_call_response.text)
            break
            
    if not customers_raw:
        return []
        
    active_ids = []
    for customer in customers_raw:
        if customer.get('id'):
            active_ids.append(customer.get('id'))
                
    return active_ids

"""
Create a new customer record and return its ID
"""
def create_customer(customer, customer_name):
    if not cint(frappe.get_value("Timeshepherd Settings", "Timeshepherd Settings", "enabled")):
        print("Timeshepherd disabled")
        return
        
    if len(customer) < 5:
        frappe.log_error("Invalid customer {0}".format(customer), "Timeshepherd create_customer")
        return None
        
    token = get_new_token()
    settings = get_settings()
    
    customers_raw = None
    
    while True:
        url = "{0}/TS.DAS.REST/api/v1/Customer/Post".format(settings.host)
        api_call_header = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        payload = {
            "number": "{0}".format(customer[-5:0]),
            "short": customer,
            "description": customer_name
        }

        api_call_response = requests.post(
            url,
            json=payload, 
            headers=api_call_header, 
            verify=True if cint(settings.verify_ssl) else False
        )
        
        if api_call_response.status_code == 401:
            token = get_new_token()
        else:
            customers_raw = json.loads(api_call_response.text)
            break
            
    if not customers_raw:
        return None
        
    if customers_raw.get('id'):
        return customers_raw.get('id')
    else:
        return None

"""
Create a new project in Timeshepherd
"""
def create_project(project):
    if not cint(frappe.get_value("Timeshepherd Settings", "Timeshepherd Settings", "enabled")):
        print("Timeshepherd disabled")
        return
    if not frappe.db.exists("Project", project):
        frappe.log_error("Project not found {0}".format(project), "Timeshepherd create_project")
        return None
    if not frappe.get_value("Project", project, "customer"):
        frappe.log_error("Customer not found {0}".format(project), "Timeshepherd create_project")
        return None
    if len(project) < 6:
        frappe.log_error("Invalid project {0}".format(project), "Timeshepherd create_project")
        return None
        
    token = get_new_token()
    settings = get_settings()
    
    project_raw = None
    
    # find customer ID
    project_doc = frappe.get_doc("Project", project)
    customer = project_doc.customer
    customer_name = frappe.get_value("Customer", customer, "customer_name")
    description = "{0} {1}".format(project_doc.object_street, project_doc.object_location)
    
    customer_id = check_customer(customer_name)
    if customer_id:
        customer_id = customer_id[0]
    else:
        customer_id = create_customer(customer, customer_name)
        
    while True:
        url = "{0}/TS.DAS.REST/api/v1/Project/Post".format(settings.host)
        api_call_header = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json'
        }
        payload = {
            "number": "{0}".format(project[-6:]),
            "short": project,
            "description": description,
            "date": datetime.now().strftime("%Y-%m-%dT%H:%M%S"),
            "customerId": customer_id,
        }

        api_call_response = requests.post(
            url,
            json=payload, 
            headers=api_call_header, 
            verify=True if cint(settings.verify_ssl) else False
        )
        
        if api_call_response.status_code == 401:
            token = get_new_token()
        else:
            project_raw = json.loads(api_call_response.text)
            break
            
    if not project_raw:
        return None
        
    if project_raw.get('id'):
        return project_raw.get('id')
    else:
        return None
