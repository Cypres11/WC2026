"""
WC 2026 FIFA Rankings Webapp
RFB Consult · Roland Broos
Flask backend voor Railway deployment - v4.1 met admin invoer
"""

from flask import Flask, jsonify, request, redirect, session, render_template_string
import json
import os, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "wc2026rfbconsult")

# ── In-memory cache ─────────────────────────────────────────────────────────
_cache = {"data": {}, "updated_at": None}

# ── 48 teams per groep ──────────────────────────────────────────────────────
GROUPS = {
    "A": ["Mexico","South Korea","South Africa","Czechia"],
    "B": ["Canada","Switzerland","Qatar","Bosnia and Herzegovina"],
    "C": ["Brazil","Morocco","Scotland","Haiti"],
    "D": ["United States","Australia","Paraguay","Türkiye"],
    "E": ["Germany","Ivory Coast","Ecuador","Curaçao"],
    "F": ["Netherlands","Japan","Sweden","Tunisia"],
    "G": ["Belgium","Iran","Egypt","New Zealand"],
    "H": ["Spain","Uruguay","Saudi Arabia","Cape Verde"],
    "I": ["France","Senegal","Norway","Iraq"],
    "J": ["Argentina","Austria","Algeria","Jordan"],
    "K": ["Portugal","Colombia","Uzbekistan","DR Congo"],
    "L": ["England","Croatia","Ghana","Panama"],
}

CONF = {
    "Mexico":"CONCACAF","South Korea":"AFC","South Africa":"CAF","Czechia":"UEFA",
    "Canada":"CONCACAF","Switzerland":"UEFA","Qatar":"AFC","Bosnia and Herzegovina":"UEFA",
    "Brazil":"CONMEBOL","Morocco":"CAF","Scotland":"UEFA","Haiti":"CONCACAF",
    "United States":"CONCACAF","Australia":"AFC","Paraguay":"CONMEBOL","Türkiye":"UEFA",
    "Germany":"UEFA","Ivory Coast":"CAF","Ecuador":"CONMEBOL","Curaçao":"CONCACAF",
    "Netherlands":"UEFA","Japan":"AFC","Sweden":"UEFA","Tunisia":"CAF",
    "Belgium":"UEFA","Iran":"AFC","Egypt":"CAF","New Zealand":"OFC",
    "Spain":"UEFA","Uruguay":"CONMEBOL","Saudi Arabia":"AFC","Cape Verde":"CAF",
    "France":"UEFA","Senegal":"CAF","Norway":"UEFA","Iraq":"AFC",
    "Argentina":"CONMEBOL","Austria":"UEFA","Algeria":"CAF","Jordan":"AFC",
    "Portugal":"UEFA","Colombia":"CONMEBOL","Uzbekistan":"AFC","DR Congo":"CAF",
    "England":"UEFA","Croatia":"UEFA","Ghana":"CAF","Panama":"CONCACAF",
}

def compute_standings(matches):
    """Bereken stand vanuit lijst wedstrijduitslagen."""
    stats = {}
    for grp, teams in GROUPS.items():
        for t in teams:
            stats[t] = {"p":0,"w":0,"d":0,"l":0,"gf":0,"ga":0,"pts":0,"group":grp}

    for m in matches:
        h, a, hs, as_ = m["home"], m["away"], m["hs"], m["as"]
        if hs is None or as_ is None:
            continue
        hs, as_ = int(hs), int(as_)
        stats[h]["p"] += 1; stats[h]["gf"] += hs; stats[h]["ga"] += as_
        stats[a]["p"] += 1; stats[a]["gf"] += as_; stats[a]["ga"] += hs
        if hs > as_:
            stats[h]["w"] += 1; stats[h]["pts"] += 3
            stats[a]["l"] += 1
        elif hs < as_:
            stats[a]["w"] += 1; stats[a]["pts"] += 3
            stats[h]["l"] += 1
        else:
            stats[h]["d"] += 1; stats[h]["pts"] += 1
            stats[a]["d"] += 1; stats[a]["pts"] += 1
    return stats

# Standaard wedstrijden (alle matchday 1+2+3 fixtures)
DEFAULT_MATCHES = [
    # Groep A
    {"id":"A1","home":"Mexico","away":"South Africa","hs":"2","as":"0"},
    {"id":"A2","home":"South Korea","away":"Czechia","hs":"2","as":"1"},
    {"id":"A3","home":"Mexico","away":"Czechia","hs":None,"as":None},
    {"id":"A4","home":"South Korea","away":"South Africa","hs":None,"as":None},
    {"id":"A5","home":"Mexico","away":"South Korea","hs":None,"as":None},
    {"id":"A6","home":"Czechia","away":"South Africa","hs":None,"as":None},
    # Groep B
    {"id":"B1","home":"Canada","away":"Bosnia and Herzegovina","hs":"1","as":"1"},
    {"id":"B2","home":"Switzerland","away":"Qatar","hs":"1","as":"1"},
    {"id":"B3","home":"Canada","away":"Switzerland","hs":None,"as":None},
    {"id":"B4","home":"Bosnia and Herzegovina","away":"Qatar","hs":None,"as":None},
    {"id":"B5","home":"Canada","away":"Qatar","hs":None,"as":None},
    {"id":"B6","home":"Switzerland","away":"Bosnia and Herzegovina","hs":None,"as":None},
    # Groep C
    {"id":"C1","home":"Brazil","away":"Morocco","hs":"1","as":"1"},
    {"id":"C2","home":"Scotland","away":"Haiti","hs":"1","as":"0"},
    {"id":"C3","home":"Brazil","away":"Scotland","hs":None,"as":None},
    {"id":"C4","home":"Morocco","away":"Haiti","hs":None,"as":None},
    {"id":"C5","home":"Brazil","away":"Haiti","hs":None,"as":None},
    {"id":"C6","home":"Morocco","away":"Scotland","hs":None,"as":None},
    # Groep D
    {"id":"D1","home":"United States","away":"Paraguay","hs":"4","as":"1"},
    {"id":"D2","home":"Australia","away":"Türkiye","hs":"2","as":"0"},
    {"id":"D3","home":"United States","away":"Australia","hs":None,"as":None},
    {"id":"D4","home":"Paraguay","away":"Türkiye","hs":None,"as":None},
    {"id":"D5","home":"United States","away":"Türkiye","hs":None,"as":None},
    {"id":"D6","home":"Australia","away":"Paraguay","hs":None,"as":None},
    # Groep E
    {"id":"E1","home":"Germany","away":"Curaçao","hs":"7","as":"1"},
    {"id":"E2","home":"Ivory Coast","away":"Ecuador","hs":"1","as":"0"},
    {"id":"E3","home":"Germany","away":"Ivory Coast","hs":None,"as":None},
    {"id":"E4","home":"Ecuador","away":"Curaçao","hs":None,"as":None},
    {"id":"E5","home":"Germany","away":"Ecuador","hs":None,"as":None},
    {"id":"E6","home":"Ivory Coast","away":"Curaçao","hs":None,"as":None},
    # Groep F
    {"id":"F1","home":"Netherlands","away":"Japan","hs":"2","as":"2"},
    {"id":"F2","home":"Sweden","away":"Tunisia","hs":"5","as":"1"},
    {"id":"F3","home":"Netherlands","away":"Sweden","hs":None,"as":None},
    {"id":"F4","home":"Japan","away":"Tunisia","hs":None,"as":None},
    {"id":"F5","home":"Netherlands","away":"Tunisia","hs":None,"as":None},
    {"id":"F6","home":"Sweden","away":"Japan","hs":None,"as":None},
    # Groep G
    {"id":"G1","home":"Belgium","away":"Egypt","hs":"1","as":"1"},
    {"id":"G2","home":"Iran","away":"New Zealand","hs":"2","as":"2"},
    {"id":"G3","home":"Belgium","away":"Iran","hs":None,"as":None},
    {"id":"G4","home":"Egypt","away":"New Zealand","hs":None,"as":None},
    {"id":"G5","home":"Belgium","away":"New Zealand","hs":None,"as":None},
    {"id":"G6","home":"Iran","away":"Egypt","hs":None,"as":None},
    # Groep H
    {"id":"H1","home":"Spain","away":"Cape Verde","hs":"0","as":"0"},
    {"id":"H2","home":"Saudi Arabia","away":"Uruguay","hs":"1","as":"1"},
    {"id":"H3","home":"Spain","away":"Uruguay","hs":None,"as":None},
    {"id":"H4","home":"Saudi Arabia","away":"Cape Verde","hs":None,"as":None},
    {"id":"H5","home":"Spain","away":"Saudi Arabia","hs":None,"as":None},
    {"id":"H6","home":"Uruguay","away":"Cape Verde","hs":None,"as":None},
    # Groep I
    {"id":"I1","home":"France","away":"Senegal","hs":"2","as":"0"},
    {"id":"I2","home":"Norway","away":"Iraq","hs":"1","as":"0"},
    {"id":"I3","home":"France","away":"Norway","hs":None,"as":None},
    {"id":"I4","home":"Senegal","away":"Iraq","hs":None,"as":None},
    {"id":"I5","home":"France","away":"Iraq","hs":None,"as":None},
    {"id":"I6","home":"Norway","away":"Senegal","hs":None,"as":None},
    # Groep J
    {"id":"J1","home":"Argentina","away":"Algeria","hs":"3","as":"0"},
    {"id":"J2","home":"Austria","away":"Jordan","hs":"3","as":"1"},
    {"id":"J3","home":"Argentina","away":"Austria","hs":"2","as":"0"},
    {"id":"J4","home":"Algeria","away":"Jordan","hs":None,"as":None},
    {"id":"J5","home":"Argentina","away":"Jordan","hs":None,"as":None},
    {"id":"J6","home":"Algeria","away":"Austria","hs":None,"as":None},
    # Groep K
    {"id":"K1","home":"Portugal","away":"DR Congo","hs":"1","as":"1"},
    {"id":"K2","home":"Colombia","away":"Uzbekistan","hs":"3","as":"1"},
    {"id":"K3","home":"Portugal","away":"Colombia","hs":None,"as":None},
    {"id":"K4","home":"DR Congo","away":"Uzbekistan","hs":None,"as":None},
    {"id":"K5","home":"Portugal","away":"Uzbekistan","hs":None,"as":None},
    {"id":"K6","home":"Colombia","away":"DR Congo","hs":None,"as":None},
    # Groep L
    {"id":"L1","home":"England","away":"Croatia","hs":"4","as":"2"},
    {"id":"L2","home":"Ghana","away":"Panama","hs":"1","as":"0"},
    {"id":"L3","home":"England","away":"Ghana","hs":None,"as":None},
    {"id":"L4","home":"Croatia","away":"Panama","hs":None,"as":None},
    {"id":"L5","home":"England","away":"Panama","hs":None,"as":None},
    {"id":"L6","home":"Croatia","away":"Ghana","hs":None,"as":None},
]

# ── Persistent storage ──────────────────────────────────────────────────────
SCORES_FILE = os.path.join(os.path.dirname(__file__), 'scores.json')

def load_scores():
    """Laad scores van schijf, of gebruik defaults als bestand niet bestaat."""
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, 'r') as f:
                data = json.load(f)
                print(f"Scores geladen van {SCORES_FILE}: {len(data.get('matches',[]))} wedstrijden")
                return data.get('matches', DEFAULT_MATCHES), data.get('updated_at', None)
        except Exception as e:
            print(f"Fout bij laden scores: {e} — gebruik defaults")
    return DEFAULT_MATCHES, "18 jun 2026 (matchday 1)"

def save_scores(matches, updated_at):
    """Sla scores op naar schijf."""
    try:
        with open(SCORES_FILE, 'w') as f:
            json.dump({'matches': matches, 'updated_at': updated_at}, f)
        print(f"Scores opgeslagen naar {SCORES_FILE}")
    except Exception as e:
        print(f"Fout bij opslaan scores: {e}")

# Initialiseer cache — laad van schijf of gebruik defaults
_matches, _updated_at = load_scores()
_cache["matches"]    = _matches
_cache["data"]       = compute_standings(_matches)
_cache["updated_at"] = _updated_at

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html")) as f:
        return f.read()

@app.route("/api/standings")
def get_standings():
    return jsonify({"data": _cache["data"], "updated_at": _cache["updated_at"]})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "updated_at": _cache["updated_at"]})

@app.route("/admin", methods=["GET","POST"])
def admin():
    admin_key = os.environ.get("ADMIN_KEY","wc2026")
    error = ""

    # Login check
    if not session.get("admin"):
        if request.method == "POST" and request.form.get("password") == admin_key:
            session["admin"] = True
        elif request.method == "POST":
            error = "Onjuist wachtwoord"
        if not session.get("admin"):
            return render_template_string(LOGIN_HTML, error=error)

    # Save scores
    if request.method == "POST" and request.form.get("action") == "save":
        matches = list(_cache.get("matches", DEFAULT_MATCHES))
        for m in matches:
            hs = request.form.get(f"hs_{m['id']}","").strip()
            as_ = request.form.get(f"as_{m['id']}","").strip()
            m["hs"] = hs if hs != "" else None
            m["as"] = as_ if as_ != "" else None
        _cache["matches"]    = matches
        _cache["data"]       = compute_standings(matches)
        _cache["updated_at"] = datetime.now().strftime("%d %b %Y %H:%M UTC")
        save_scores(matches, _cache["updated_at"])
        return redirect("/admin?saved=1")

    matches  = _cache.get("matches", DEFAULT_MATCHES)
    saved    = request.args.get("saved","")
    return render_template_string(ADMIN_HTML, groups=GROUPS, matches=matches, saved=saved)

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect("/admin")

# ── HTML Templates ──────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WC2026 Admin</title>
<style>
body{background:#0d1b2a;color:#e0e0e0;font-family:Arial,sans-serif;display:flex;
  align-items:center;justify-content:center;min-height:100vh;margin:0}
.box{background:#1a2e42;border:1px solid #c9a84c;border-radius:10px;padding:32px;width:320px;text-align:center}
h2{color:#c9a84c;margin-bottom:20px}
input{width:100%;background:#0d1b2a;border:1px solid #2a4a6a;border-radius:6px;
  color:#e0e0e0;padding:10px;font-size:1em;margin-bottom:12px;box-sizing:border-box}
button{width:100%;background:#1a3a5c;border:1px solid #c9a84c;color:#c9a84c;
  border-radius:6px;padding:10px;font-size:1em;cursor:pointer}
button:hover{background:#c9a84c;color:#0d1b2a}
.err{color:#e05c5c;font-size:0.85em;margin-bottom:10px}
</style></head><body>
<div class="box">
  <h2>🔒 WC2026 Admin</h2>
  {% if error %}<p class="err">{{ error }}</p>{% endif %}
  <form method="POST">
    <input type="password" name="password" placeholder="Wachtwoord..." autofocus>
    <button type="submit">Inloggen</button>
  </form>
</div></body></html>"""

ADMIN_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>WC2026 Admin — Scores invoeren</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1b2a;color:#e0e0e0;font-family:Arial,sans-serif;padding:16px}
header{background:#1a3a5c;border-bottom:2px solid #c9a84c;padding:12px 16px;
  display:flex;justify-content:space-between;align-items:center;margin:-16px -16px 20px;border-radius:0}
header h1{color:#c9a84c;font-size:1.1em}
header a{color:#8aaec8;font-size:0.8em;text-decoration:none}
.saved{background:#1a3a1a;border:1px solid #4caf7d;color:#4caf7d;
  padding:10px 16px;border-radius:6px;margin-bottom:16px;font-size:0.85em}
.groups{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.group{background:#111f2e;border:1px solid #1a2e42;border-radius:8px;overflow:hidden}
.group h3{background:#1a3a5c;color:#c9a84c;padding:8px 12px;font-size:0.85em;letter-spacing:1px}
.match{display:grid;grid-template-columns:1fr 40px 16px 40px 1fr;align-items:center;
  gap:6px;padding:7px 12px;border-bottom:1px solid #0d1b2a;font-size:0.82em}
.match:last-child{border-bottom:none}
.home{text-align:right;color:#e0e0e0}
.vs{text-align:center;color:#3a5a7a;font-size:0.75em}
.score{width:38px;background:#0d1b2a;border:1px solid #2a4a6a;border-radius:4px;
  color:#c9a84c;text-align:center;padding:4px;font-size:0.9em;font-weight:bold}
.score:focus{border-color:#c9a84c;outline:none}
.away{color:#e0e0e0}
footer{margin-top:24px;text-align:center}
.savebtn{background:#1a3a5c;border:2px solid #c9a84c;color:#c9a84c;
  border-radius:8px;padding:12px 40px;font-size:1em;cursor:pointer;font-family:Arial}
.savebtn:hover{background:#c9a84c;color:#0d1b2a}
.viewbtn{display:inline-block;margin-left:12px;color:#8aaec8;font-size:0.85em;text-decoration:none}
</style></head><body>
<header>
  <h1>⚽ WC2026 Admin — Scores invoeren</h1>
  <div><a href="/">← Bekijk app</a> &nbsp; <a href="/admin/logout">Uitloggen</a></div>
</header>

{% if saved %}
<div class="saved">✓ Stand opgeslagen en bijgewerkt! Alle bezoekers zien nu de actuele stand.</div>
{% endif %}

<form method="POST">
  <input type="hidden" name="action" value="save">
  <div class="groups">
  {% for grp, teams in groups.items() %}
    <div class="group">
      <h3>GROEP {{ grp }}</h3>
      {% for m in matches if m.id.startswith(grp) %}
      <div class="match">
        <span class="home">{{ m.home }}</span>
        <input class="score" type="number" name="hs_{{ m.id }}" 
               value="{{ m.hs if m.hs is not none else '' }}" min="0" max="99"
               placeholder="–">
        <span class="vs">:</span>
        <input class="score" type="number" name="as_{{ m.id }}"
               value="{{ m.as if m.as is not none else '' }}" min="0" max="99"
               placeholder="–">
        <span class="away">{{ m.away }}</span>
      </div>
      {% endfor %}
    </div>
  {% endfor %}
  </div>
  <div style="margin-top:8px;padding:0 4px">
    <p style="font-size:0.72em;color:#3a5a7a;margin-bottom:12px">
      Laat velden leeg voor niet gespeelde wedstrijden. Stand wordt automatisch berekend uit de scores.
    </p>
  </div>
  <footer>
    <button type="submit" class="savebtn">💾 Stand opslaan</button>
    <a href="/" class="viewbtn">Bekijk live app →</a>
  </footer>
</form>
</body></html>"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
