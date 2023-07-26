# -*- coding: utf-8 -*-
# Copyright (c) 2023, libracore (https://www.libracore.com) and contributors
# For license information, please see license.txt
#
# Import logic for SV files
#
# Usage:
#    run as
#    $ python3 sv_parser /home/libracore/SV

###### PyMuPDF
import fitz
from os import listdir
from os.path import isfile, join
import sys

FOLDER = "~/temp/SV_all"

# update folder if provided as parameters
if len(sys.argv) > 1:
    FOLDER = sys.argv[1]

# robust float function
def flt(s):
    result = None
    try:
        result = float(s.replace(",", "."))
    except:
        result = None
    return result

# get all files from folder (pure filename without path)
files = [f for f in listdir(FOLDER) if isfile(join(FOLDER, f))]

print("{0}".format(files))

# prepare variables
statistics = {'count': 0, 'failures': 0, 'form_count': 0, 'strange_count': 0}
svs = []

# go through all files
for f in files:
    if len(f) >= 4 and f[-4:].lower() == ".pdf" and f[0:3].lower() != "sv-":   # only use pdf and not SV-P-nnn (this are the digital files)
        statistics['count'] += 1
        print("reading {0}".format(f))
        # prepare result dict
        _project = {
            'file': f
        }
        # try pdf forms first
        import PyPDF2
        pdf = PyPDF2.PdfReader(join(FOLDER, f))
        form = pdf.get_fields()
        if form:
            statistics['form_count'] += 1
            #for k,v in form.items():
            #    if len("{0}".format(k)) > 2:
            #        print("{0}: {1}".format(k, v))
            _project['rotation'] = 0
            _project['to_depth'] = flt(form['bis mTiefe'].get('/V'))
            _project['end_depth'] = flt(form['bis mTiefe9'].get('/V'))
            _project['mud_amount'] = flt(form['Entsorgte Menge ca m'].get('/V'))
            _project['project'] = form['Projekt-Nr'].get('/V')
            _project['start_date'] = form['Bohrbeginn'].get('/V')
            _project['end_date'] = form['Bohrende'].get('/V')
            _project['permit'] = form['Bewilligungs-Nr'].get('/V')
            _project['coordinates'] = form['Koordinaten'].get('/V')
            _project['drilling_master'] = form['Bohrmeister'].get('/V')
            _project['drilling_order'] = form['Bohrauftrag'].get('/V')          # like 2x350Hip.PN35
            _project['drilling_device'] = form['Bohrgerät'].get('/V')
            _project['drilling_kote'] = form['Bohrkote'].get('/V')
            _project['piping'] = form['Verrohrung'].get('/V')
            _project['drill'] = form['Bohrwerkzeug'].get('/V')
            _project['samples'] = form['Beprobung alle m'].get('/V')
            _project['object_name'] = form['Objekt'].get('/V')
            _project['object_location'] = form['Koordinaten0'].get('/V')
            _project['drilling_number'] = form['Bohrung'].get('/V')
            _project['layers'] = [
                {
                    'depth': flt(form['bis mTiefe0'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen1'].get('/V'),
                    'description': form['Art-Eigenschaften'].get('/V'),
                    'color': form['Farbe'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe1'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen2'].get('/V'),
                    'description': form['Art-Eigenschaften0'].get('/V'),
                    'color': form['Farbe0'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe2'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen3'].get('/V'),
                    'description': form['Art-Eigenschaften1'].get('/V'),
                    'color': form['Farbe1'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe3'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen4'].get('/V'),
                    'description': form['Art-Eigenschaften2'].get('/V'),
                    'color': form['Farbe2'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe4'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen5'].get('/V'),
                    'description': form['Art-Eigenschaften3'].get('/V'),
                    'color': form['Farbe3'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe5'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen6'].get('/V'),
                    'description': form['Art-Eigenschaften4'].get('/V'),
                    'color': form['Farbe4'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe6'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen7'].get('/V'),
                    'description': form['Art-Eigenschaften5'].get('/V'),
                    'color': form['Farbe5'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe7'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen8'].get('/V'),
                    'description': form['Art-Eigenschaften6'].get('/V'),
                    'color': form['Farbe6'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe8'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen9'].get('/V'),
                    'description': form['Art-Eigenschaften7'].get('/V'),
                    'color': form['Farbe7'].get('/V')
                },
                {
                    'depth': flt(form['bis mTiefe9'].get('/V')),
                    'remarks': form['BeobachtugenBemerkungen10'].get('/V'),
                    'description': form['Art-Eigenschaften8'].get('/V'),
                    'color': form['Farbe8'].get('/V')
                }
            ]
            # 'Spediteur', 'Entsorger', 'Richtung', 'Winkel', 'Spediteur0', 'Spediteur1', 'Tiefe ca', 'BeobachtugenBemerkungen1', 'BeobachtugenBemerkungen2', ...
            # append to list of results
            if _project['project']:
                svs.append(_project)
            continue
        
        # read this file
        doc = fitz.open(join(FOLDER, f))
        # read pages of this pdf
        for page in doc:
            rot = doc[0].rotation
            #print("Rotation: {0}".format(rot))
            if rot:
                page.set_rotation(0)
                page.rect
                p = fitz.Point(0, 0)
                p * page.rotation_matrix
            sorted_text = page.get_text("text", sort=True)
            if not sorted_text:
                statistics['failures'] += 1
                print("no text found")
                continue        # skip this for
            # prepare result dict
            _project['rotation'] = rot

            # create a list of lines from string
            sorted_lines = sorted_text.split("\n")
            # find project number: look for "Bohrart" --> 2 lines later
            # find "Bohrart"-line
            for i in range(0, len(sorted_lines) - 1):
                if sorted_lines[i].startswith("Bohrart"):
                    # i is now at line "Bohrart"
                    _project['project'] = sorted_lines[i+2]
                    _project['start_date'] = sorted_lines[i+3]
                    _project['end_date'] = sorted_lines[i+4]
                    _project['permit'] = sorted_lines[i+1]
                if sorted_lines[i] == ("mm"):
                    _project['to_depth'] = flt(sorted_lines[i+2])
                if sorted_lines[i].startswith("Rotomax") or sorted_lines[i].startswith("Nordmeyer"):
                    _project['piping'] = sorted_lines[i+1]
                if sorted_lines[i] == ("Tiefe"):
                    _project['end_depth'] = flt(sorted_lines[i-1])
                
            # find mud after line 15 in first float line
            mud = None
            mud_line = 14
            while not mud:
                mud_line += 1
                if mud_line >= (len(sorted_lines) - 1):
                    break
                mud = flt(sorted_lines[mud_line])
            _project['mud_amount'] = mud
            
            # add other readers
            
            
            # append to list of results
            if 'project' in _project and _project['project']:
                svs.append(_project)

print("=======RESULTS=====")

for sv in svs:
    # output only strage files (10 m depth ~ 1 m3 mud)
    drilling_depth = sv.get('end_depth') or 0
    mud_amount = sv.get('mud_amount') or 0
    if (drilling_depth < (1 * mud_amount)) or (drilling_depth > (100 * mud_amount)):
        statistics['strange_count'] += 1
        print("{f}: {p} ({r}): {sd}..{ed} (Permit: {pe}) - Piping: {pp} mm - Piping depth: {td} m - Drilling depth: {d} m - {m} m3".format(
            f=sv.get('file'),
            p=sv.get('project'),
            r=sv.get('rotation'),
            sd=sv.get('start_date'),
            ed=sv.get('end_date'),
            pe=sv.get('permit'),
            td=sv.get('to_depth'),
            pp=sv.get('piping'),
            m=sv.get('mud_amount'),
            d=sv.get('end_depth')
        ))
        
    # TODO: create SV record (frappe)
    
    
print("=====SUMMARY====")
print("Files: {0}".format(statistics['count']))
print("Errors: {0} ({1}%)".format(statistics['failures'], round(100 * statistics['failures']/(statistics['count'] or 1))))
print("Forms: {0} ({1}%)".format(statistics['form_count'], round(100 * statistics['form_count']/(statistics['count'] or 1))))
print("Strange: {0} ({1}%)".format(statistics['strange_count'], round(100 * statistics['strange_count']/(statistics['count'] or 1))))
