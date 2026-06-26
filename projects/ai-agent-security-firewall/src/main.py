"""FastAPI application for the AI Agent Security Firewall."""

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from .firewall import Firewall
from .config import FirewallConfig

app = FastAPI(title="AI Agent Security Firewall", version="1.0.0")
config = FirewallConfig()
firewall = Firewall(config)

DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Agent Security Firewall</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#0d1117;color:#c9d1d9}
h1{color:#58a6ff;border-bottom:1px solid #30363d;padding-bottom:10px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:15px;margin:20px 0}
.stat{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;text-align:center}
.stat .num{font-size:2em;font-weight:bold;color:#58a6ff}
.stat .label{color:#8b949e;margin-top:5px}
.scan-form{margin:20px 0}
textarea{width:100%;height:100px;background:#0d1117;border:1px solid #30363d;color:#c9d1d9;padding:10px;border-radius:6px;font-family:inherit}
button{background:#238636;color:#fff;border:none;padding:10px 20px;border-radius:6px;cursor:pointer;margin-top:10px}
button:hover{background:#2ea043}
.result{margin:15px 0;padding:15px;border-radius:6px;display:none}
.result.blocked{background:#3d1f1f;border:1px solid #f85149}
.result.clean{background:#1f3d2f;border:1px solid #2ea043}
</style>
</head>
<body>
<h1>AI Agent Security Firewall</h1>
<div class="stats">
<div class="stat"><div class="num" id="total">0</div><div class="label">Total Scans</div></div>
<div class="stat"><div class="num" id="blocked">0</div><div class="label">Blocked</div></div>
<div class="stat"><div class="num" id="flagged">0</div><div class="label">Flagged</div></div>
<div class="stat"><div class="num" id="pct">0%</div><div class="label">Block Rate</div></div>
</div>
<div class="scan-form">
<h2>Scan Text</h2>
<textarea id="input" placeholder="Enter text to scan..."></textarea>
<br><button onclick="scan()">Scan</button>
<div class="result" id="result"></div>
</div>
<script>
function scan(){
  const text=document.getElementById('input').value;
  fetch('/api/v1/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})})
  .then(r=>r.json()).then(d=>{
    const el=document.getElementById('result');
    el.style.display='block';
    el.className='result '+(d.blocked?'blocked':'clean');
    el.innerHTML='Severity: '+d.severity.toUpperCase()+(d.violations.length?' | Violations: '+d.violations.map(v=>v.type).join(', '):' | Clean');
  });
}
</script>
</body>
</html>'''


@app.on_event("startup")
async def startup():
    os.makedirs("static", exist_ok=True)


@app.post("/api/v1/scan")
async def scan_text(body: dict):
    text = body.get("text", "")
    result = firewall.scan(text)
    return result


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/v1/stats")
async def stats():
    return firewall.get_stats()


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD_HTML
