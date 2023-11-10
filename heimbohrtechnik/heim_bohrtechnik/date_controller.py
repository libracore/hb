# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore AG and contributors
# For license information, please see license.txt
#
#
#
# Use with
#  from heimbohrtechnik.heim_bohrtechnik.date_controller import move_project, get_duration_days
#
# Test with
#  $ bench execute heimbohrtechnik.heim_bohrtechnik.date_controller.run_test_cases
#

# import libs
import frappe
import datetime
import time

"""
Cache holidays, note: do not include regional holidays (same doctype, but Regional Holiday), include past as a shift could occur in the past
"""
def get_holidays():
    # fetch holidays
    holidays_raw = frappe.db.sql("""
            SELECT `holiday_date` AS `date`
            FROM `tabHoliday`
            WHERE `parenttype` = "Holiday List";
        """, as_dict=True)
        
    holidays = []
    for h in holidays_raw:
        holidays.append(h['date'])
    return holidays
    
"""
Move a project, defined by start date and half-day and
its duration (float in days) in working days) by move_by_days (float)
"""
def move_project(start_date, start_half_day, duration, move_by_days):
    # find start by moving
    new_start_date = holiday_safe_add_days(start_date, start_half_day, move_by_days)
    # find end using the duration (- one segment as the start is inclusive)
    end_date = holiday_safe_add_days(new_start_date['date'], new_start_date['hd'], (duration - 0.5))
    return {
        'start_date': new_start_date['date'],
        'start_hd': new_start_date['hd'],
        'end_date': end_date['date'],
        'end_hd': end_date['hd']
    }

"""
Add days (can be float) to a date with half-day, and keep weekends
"""
def holiday_safe_add_days(start_date, start_half_day, move_by_days):
    # define start date as timestamp
    ts = get_timestamp(start_date, start_half_day)

    direction = 0.5 if move_by_days >= 0 else -0.5
    holidays = get_holidays()
    while move_by_days != 0:
        # move by half a day
        ts += (60 * 60 * 24) * direction
        # check if this is a working segment
        if not get_date_from_timestamp(ts)['date'] in holidays:
            move_by_days += (-1) * direction

    d = get_date_from_timestamp(ts)
    return d

"""
From a date and VM/NM -> timestamp
"""
def get_timestamp(date, half_day):
    if type(date) == str:
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
    if type(date) == datetime.date:
        date = datetime.combine(date, 0)
        
    timestamp = datetime.datetime.timestamp(date)
    if half_day == "NM":
        timestamp += 60 * 60 * 18
    else:
        timestamp += 60 * 60 * 6
    return timestamp

"""
Timestamp to datetime conversion
"""
def get_date_from_timestamp(timestamp):
    dt = datetime.datetime.fromtimestamp(timestamp)
    hd = "VM" if (dt.time().hour + (dt.time().minute / 60)) < 12 else "NM"
    return {'date': dt.strftime("%Y-%m-%d"), 'hd': hd}

"""
Find number of working days (except holidays/weekend)
"""
def get_duration_days(start_date, start_hd, end_date, end_hd):
    start_ts = get_timestamp(start_date, start_hd)
    end_ts = get_timestamp(end_date, end_hd)
    holidays = get_holidays()
    frappe.log_error(holidays, "holidays")
    duration = 0.5
    while start_ts < end_ts:
        start_ts += (60 * 60 * 12)      # iterate half day
        if not get_date_from_timestamp(start_ts)['date'] in holidays:
            duration += 0.5
    return duration

"""
TEST SECTION
"""
def test(start, start_hd, duration, move_by):
    print("{0}".format({
        'start_date': start,
        'start_hd': start_hd,
        'duration': duration,
        'move_by': move_by
    }))
    moved = move_project(start, start_hd, duration, move_by)
    print(moved)
    print(get_duration_days(moved['start_date'], moved['start_hd'], moved['end_date'], moved['end_hd']))

def run_test_cases():
    test("2023-11-08", "VM", 2, 1)
    test("2023-11-08", "VM", 1, 1)
    test("2023-11-09", "NM", 2, 1)
    test("2023-11-09", "NM", 2, 0.5)
    test("2023-11-08", "VM", 1, 1.5)
