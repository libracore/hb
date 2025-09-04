import frappe
from frappe.utils import getdate, add_days

@frappe.whitelist()
def get_data(project, cur_subcontracting):
    _project = frappe.get_doc("Project", project)
    subcontractings = get_all_subcontractings(project)
    date_list = [_project.get("expected_start_date"), _project.get("expected_end_date")]

    for subcontracting in subcontractings:
        date_list.append(subcontracting.get("from_date"))
        date_list.append(subcontracting.get("to_date"))

    days, render_data = get_render_data_and_days(_project, subcontractings, min(date_list), max(date_list), cur_subcontracting)
    render_data = assign_lanes(render_data)
    
    return {'days': days, 'render_data': render_data}

def is_workday(d):
    # Gibt True zurück wenn der numerische Wochentag < 5 ist (0=Mo ... 6=So)
    return d.weekday() < 5

def next_workday_on_or_after(d):
    # Findet den nächstmöglichen Arbeitstag
    while not is_workday(d):
        d = add_days(d, 1)
    return d

def prev_workday_on_or_before(d):
    # Findet den erstmöglichen Arbeitstag in relativer Vergangenheit
    while not is_workday(d):
        d = add_days(d, -1)
    return d

def workday_index(window_start, target):
    # Liefert einen 1-basierten Index über Arbeitstage (Mo–Fr)
    d = window_start
    idx = 0
    while d < target:
        if is_workday(d):
            idx += 1
        d = add_days(d, 1)
    if is_workday(target):
        idx += 1
    return max(1, idx)

def workday_span(start_date, end_date):
    # Liefert die Anzahl Arbeitstage inkl. Grenzen (>=1) oder 0 wenn keine Arbeitstage im Bereich
    if end_date < start_date:
        return 0
    d = start_date
    cnt = 0
    while d <= end_date:
        if is_workday(d):
            cnt += 1
        d = add_days(d, 1)
    return cnt

def assign_lanes(gants):
    # Die Lane Zuweisung erfolgt immer direkt, also ohne in die Zukunft zu schauen
    # Ist eine Lane "frei" -> Lane Zuweisen, ist keine "frei" -> neue erstellen und zuweisen
    
    def _pos(t):
        start = t.get("render_start_col") or 1
        span = t.get("render_span") or 1
        return int(start), int(span)

    lanes_end = []
    for t in sorted(gants, key=lambda x: (_pos(x)[0], -_pos(x)[1])):
        start, span = _pos(t)
        end = start + span
        for i, lane_end in enumerate(lanes_end):
            if start >= lane_end:
                lanes_end[i] = end
                t["lane"] = i
                break
        else:
            lanes_end.append(end)
            t["lane"] = len(lanes_end) - 1
    return gants

def get_all_subcontractings(project):
    subcontractings = frappe.get_all(
        "Subcontracting Order",
        fields=["name", "order_description", "from_date", "to_date"],
        filters={"project": project},
    )
    return subcontractings

def get_render_indexes(wnd_start, wnd_end, record):
    # Normieren von Start/Ende (Fallbacks)
    from_date = record.get("from_date", record.get("expected_start_date", None))
    to_date = record.get("to_date", record.get("expected_end_date", None))
    t_start = getdate(from_date) if from_date else (getdate(to_date) if to_date else wnd_start)
    t_end = getdate(to_date) if to_date else t_start

    # Setzen des visuellen Start/Ende (für Start/Ende übergreifende Einträge)
    vis_start = max(t_start, wnd_start)
    vis_end = min(t_end, wnd_end)

    # Auf Arbeitstage kürzen
    start_work = next_workday_on_or_after(vis_start)
    end_work = prev_workday_on_or_before(vis_end)

    # Position/Länge nur über Arbeitstage
    render_start_col = workday_index(wnd_start, start_work)
    render_span = workday_span(start_work, end_work)

    return render_start_col, render_span

def get_render_data_and_days(project, subcontractings, from_date, to_date, cur_subcontracting):
    wnd_start = getdate(from_date)
    wnd_end   = getdate(to_date)
    
    # Tage zusammenbauen (nur Arbeitstage Mo–Fr)
    days = []
    d = wnd_start
    today = getdate(frappe.utils.nowdate())
    weekdays = ["Mo","Di","Mi","Do","Fr","Sa","So"]
    while d <= wnd_end:
        # Der Tag wird berücksichtigt wenn es ein Wochentag ist
        if is_workday(d):
            days.append({
                "label": f"{weekdays[d.weekday()]} {d.strftime('%d.%m')}",
                "date": d.isoformat(),
                "is_today": d == today
            })
        d = add_days(d, 1)

    gant_obj = []
    for subcontracting in subcontractings:
        render_start_col, render_span = get_render_indexes(wnd_start, wnd_end, subcontracting)
        _gant_obj = {
            "doctype": "Subcontracting Order",
            "docname": subcontracting.get("name"),
            "render_start_col": render_start_col,
            "render_span": render_span,
            "lane": 0,
            "tooltip": """
                {name} • 
                {order_description} • 
                {from_date} - {to_date}
            """.format(name=subcontracting.get("name"), order_description = subcontracting.get("order_description", "-"), \
                       from_date = getdate(subcontracting.get("from_date")).strftime("%d.%m.%Y"), \
                       to_date = getdate(subcontracting.get("to_date")).strftime("%d.%m.%Y")),
            "label": subcontracting.get("order_description", "-"),
            "current": True if subcontracting.get("name") == cur_subcontracting else False,
            "is_subcontract": True
        }
        gant_obj.append(_gant_obj)
    
    render_start_col, render_span = get_render_indexes(wnd_start, wnd_end, project)
    gant_obj.append({
            "doctype": "Project",
            "docname": project.get("name"),
            "render_start_col": 1,
            "render_span": 2,
            "lane": 0,
            "tooltip": """
                {name} • 
                {object_name} • 
                {from_date} - {to_date}
            """.format(name=project.get("name"), object_name = project.get("object_name", "-"), \
                       from_date = getdate(project.get("expected_start_date")).strftime("%d.%m.%Y"), \
                       to_date = getdate(project.get("expected_end_date")).strftime("%d.%m.%Y")),
            "label": project.get("object_name", project.get("name", "-")),
            "current": False,
            "is_subcontract": False
    })

    return days, gant_obj