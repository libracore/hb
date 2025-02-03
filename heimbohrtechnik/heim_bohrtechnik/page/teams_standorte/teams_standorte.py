import frappe
from frappe import _

@frappe.whitelist()
def get_teams_and_locations():

    today = frappe.utils.nowdate()
    query = """
        SELECT dt.name as team_name,
            proj.name as project_name,
            proj.object_street,
            proj.object_location,
            obj.gps_coordinates
        FROM `tabDrilling Team` dt
        LEFT JOIN `tabProject` proj ON dt.name = proj.drilling_team
        LEFT JOIN `tabObject` obj ON proj.object = obj.name
        WHERE '{today}' BETWEEN proj.expected_start_date AND proj.expected_end_date
    """.format(today=today)
    data = frappe.db.sql(query, as_dict=True)

    return data