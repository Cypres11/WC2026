"""
WC 2026 FIFA Rankings Webapp
RFB Consult · Roland Broos
Flask backend voor Railway deployment
"""

from flask import Flask, jsonify, render_template_string, request
import anthropic
import json
import os
from datetime import datetime

app = Flask(__name__)

# ── Anthropic client ────────────────────────────────────────────────────────
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

# ── In-memory cache voor WK stand ───────────────────────────────────────────
# Bij Railway restart wordt dit gereset — simpel en voldoende voor dit project
_standings_cache = {
    "data": None,
    "updated_at": None
}

# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve de HTML app."""
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html"), "r") as f:
        return f.read()

@app.route("/api/standings", methods=["GET"])
def get_standings():
    """Geef gecachte stand terug."""
    return jsonify({
        "data": _standings_cache["data"],
        "updated_at": _standings_cache["updated_at"]
    })

@app.route("/api/refresh", methods=["POST"])
def refresh_standings():
    """Haal actuele WK-stand op via Claude API."""
    # Optionele admin key check
    admin_key = os.environ.get("ADMIN_KEY", "")
    if admin_key:
        provided = request.headers.get("X-Admin-Key", "")
        if provided != admin_key:
            return jsonify({"error": "Unauthorized"}), 401

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": """Geef de actuele WK 2026 groepsstand voor alle 12 groepen A t/m L.
Per team: p=gespeeld, w=gewonnen, d=gelijkspel, l=verloren, gf=doelpunten voor, ga=doelpunten tegen, pts=punten.
Gebruik exact deze teamnamen: Mexico, "South Korea", "South Africa", Czechia, Canada, Switzerland, Qatar, "Bosnia and Herzegovina", Brazil, Morocco, Scotland, Haiti, "United States", Australia, Paraguay, Türkiye, Germany, "Ivory Coast", Ecuador, Curaçao, Netherlands, Japan, Sweden, Tunisia, Belgium, Iran, Egypt, "New Zealand", Spain, Uruguay, "Saudi Arabia", "Cape Verde", France, Senegal, Norway, Iraq, Argentina, Austria, Algeria, Jordan, Portugal, Colombia, Uzbekistan, "DR Congo", England, Croatia, Ghana, Panama.
Antwoord UITSLUITEND met geldig JSON object, geen uitleg, geen markdown:
{"A":[{"team":"Mexico","p":1,"w":1,"d":0,"l":0,"gf":2,"ga":0,"pts":3}],"B":[...],"L":[...]}"""
            }]
        )

        raw = message.content[0].text
        # Strip mogelijke markdown
        raw = raw.replace("```json", "").replace("```", "").strip()
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])

        # Flatten naar naam-lookup
        flat = {}
        for grp, teams in parsed.items():
            for t in teams:
                if "team" in t:
                    flat[t["team"]] = {**t, "group": grp}

        _standings_cache["data"]       = flat
        _standings_cache["updated_at"] = datetime.now().strftime("%d %b %Y %H:%M UTC")

        return jsonify({
            "success": True,
            "teams":   len(flat),
            "updated_at": _standings_cache["updated_at"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "updated_at": _standings_cache["updated_at"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
