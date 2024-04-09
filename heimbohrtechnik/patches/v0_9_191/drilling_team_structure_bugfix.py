import frappe

def execute():
    try:
        frappe.db.sql("""
            UPDATE `tabDrilling Team`
            SET 
                `hammer_drilling` = 0, 
                `small_drilling_rig` = 0;
        """)
    except Exception as err:
        print("Bugfix drilling team data structure failed.")
        print("Check $ bench execute heimbohrtechnik.patches.v0_9_191.drilling_team_structure_bugfix.execute")
        print("{0}".format(err))
    return
