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

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

_standings_cache = {
    "data": None,
    "updated_at": None
}

@app.route("/")
def index():
    with open(os.path.join(os.path.dirname(__file__), "static", "index.html"), "r") as f:
        return f.read()

@app.route("/api/standings", methods=["GET"])
def get_standings():
    return jsonify({
        "data": _standings_cache["data"],
        "updated_at": _standings_cache["updated_at"]
    })

@app.route("/api/refresh", methods=["POST"])
def refresh_standings():
    admin_key = os.environ.get("ADMIN_KEY", "")
    if admin_key:
        provided = request.headers.get("X-Admin-Key", "")
        if provided != admin_key:
            return jsonify({"error": "Unauthorized"}), 401

    today = datetime.now().strftime("%d %B %Y")

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{
                "role": "user",
                "content": f"""Today is {today}. Give me the FIFA World Cup 2026 group stage standings based ONLY on matches that have actually been played up to today. Do NOT include matches that have not been played yet. Do NOT predict or estimate future results.

For each team provide: p=matches played, w=won, d=drawn, l=lost, gf=goals for, ga=goals against, pts=points.

Use EXACTLY these team names:
Mexico, South Korea, South Africa, Czechia, Canada, Switzerland, Qatar, Bosnia and Herzegovina,
Brazil, Morocco, Scotland, Haiti, United States, Australia, Paraguay, Türkiye,
Germany, Ivory Coast, Ecuador, Curaçao, Netherlands, Japan, Sweden, Tunisia,
Belgium, Iran, Egypt, New Zealand, Spain, Uruguay, Saudi Arabia, Cape Verde,
France, Senegal, Norway, Iraq, Argentina, Austria, Algeria, Jordan,
Portugal, Colombia, Uzbekistan, DR Congo, England, Croatia, Ghana, Panama.

Respond ONLY with a valid JSON object, no explanation, no markdown:
{{"A":[{{"team":"Mexico","p":2,"w":2,"d":0,"l":0,"gf":3,"ga":1,"pts":6}}],"B":[...],...,"L":[...]}}"""
            }]
        )

        raw = message.content[0].text
        raw = raw.replace("```json", "").replace("```", "").strip()
        start = raw.index("{")
        end   = raw.rindex("}") + 1
        parsed = json.loads(raw[start:end])

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