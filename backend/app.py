import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Tenta importar a lib do Google (Opcional)
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("AVISO: Biblioteca google-genai não encontrada.")

# === CONFIGURAÇÃO ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None
if HAS_GENAI and GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Erro ao configurar Gemini: {e}")

app = FastAPI(title="SentinelOneOps")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === PERSISTÊNCIA (Banco de dados simples) ===
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

def load_data():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

INCIDENTS = load_data()

# === DADOS MOCKADOS DE INVENTÁRIO (Novidade!) ===
INVENTORY_MOCK = [
    {"id": "SRV-001", "name": "Cluster Kubernetes Alpha", "type": "Servidor", "status": "Online", "region": "us-east-1"},
    {"id": "DB-PROD", "name": "PostgreSQL Primary", "type": "Database", "status": "Online", "region": "sa-east-1"},
    {"id": "FW-EDGE", "name": "Firewall Perimetral", "type": "Security", "status": "Warning", "region": "global"},
    {"id": "LB-HTTP", "name": "Load Balancer Nginx", "type": "Network", "status": "Online", "region": "sa-east-1"},
    {"id": "BKP-SYS", "name": "Backup System Cold", "type": "Storage", "status": "Offline", "region": "us-west-2"},
]

# === MODELOS ===
class Incident(BaseModel):
    id: str
    severity: str
    service: str
    summary: str
    opened_at: Optional[str] = None
    acknowledged: bool = False

# === ROTAS ===
@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now()}

# Rota de Incidentes
@app.get("/api/incidents")
def list_incidents():
    return INCIDENTS

@app.post("/api/incidents")
def create_incident(data: dict):
    new_id = f"INC-{1000 + len(INCIDENTS)}"
    inc = {
        "id": new_id,
        "severity": data.get("severity", "info"),
        "service": data.get("service", "unknown"),
        "summary": data.get("summary", "Sem descrição"),
        "opened_at": datetime.now().isoformat(),
        "acknowledged": False
    }
    INCIDENTS.insert(0, inc)
    save_data(INCIDENTS)
    return inc

@app.delete("/api/incidents")
def clear_all_incidents():
    INCIDENTS.clear()
    save_data(INCIDENTS)
    return {"status": "success", "message": "Todos os incidentes foram apagados."}

# Rota de Inventário (NOVA)
@app.get("/api/inventory")
def list_inventory():
    return INVENTORY_MOCK

# Rota da IA
@app.get("/api/incidents/{inc_id}/explain")
def explain_incident(inc_id: str):
    inc = next((i for i in INCIDENTS if i["id"] == inc_id), None)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente não encontrado")

    mock_explanation = f"""
    <p><b>🤖 Análise (Modo Offline):</b></p>
    <p>O serviço <b>{inc['service']}</b> gerou um alerta de severidade <b>{inc['severity']}</b>.</p>
    <ul>
        <li><b>Diagnóstico:</b> O sistema de IA não pôde ser contatado.</li>
        <li><b>Ação Recomendada:</b> Verifique os logs via SSH.</li>
    </ul>
    """

    if client:
        prompt = f"""
        Aja como um SRE Sênior. Analise este incidente:
        ID: {inc['id']} | Serviço: {inc['service']} | Severidade: {inc['severity']} | Resumo: {inc['summary']}
        Responda APENAS em HTML simples (<p>, <b>, <ul>, <li>).
        """
        try:
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            return {"explanation": response.text}
        except Exception as e:
            return {"explanation": mock_explanation}
    
    return {"explanation": mock_explanation}

# === SERVIR FRONTEND ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

@app.get("/")
def read_root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "Frontend não encontrado"}