# WC 2026 FIFA Rankings App

Webapp voor het bijhouden van FIFA rankings en WK-stand tijdens het WK 2026.

**Stack:** Python · Flask · Anthropic Claude API · Railway

## Deployment op Railway

1. Push naar GitHub repository
2. Maak nieuw project op railway.app → "Deploy from GitHub repo"
3. Voeg environment variabelen toe:
   - `ANTHROPIC_API_KEY` = jouw Anthropic API key
   - `ADMIN_KEY` = optioneel wachtwoord voor de Update knop
4. Railway deployt automatisch

## Lokaal draaien (Mac)

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python app.py
```

Dan: http://localhost:5000

## RFB Consult · Roland Broos · Juni 2026
