import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# === CONFIGURAÇÃO ===
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configura IA (Gemini)
HAS_GENAI = False
client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        HAS_GENAI = True
    except Exception as e:
        print(f"Erro ao configurar Gemini: {e}")

app = FastAPI(title="SentinelOneOps Omniscience")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# === PERSISTÊNCIA ===
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data.json"

def load_data():
    if not DATA_FILE.exists(): return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except json.JSONDecodeError: return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

INCIDENTS = load_data()

# === DADOS MOCKADOS ===
INVENTORY_MOCK = [
    {"id": "SRV-K8S-01", "name": "Cluster Kubernetes Alpha", "type": "Cluster", "status": "Online", "region": "us-east-1"},
    {"id": "DB-PSQL-M", "name": "PostgreSQL Primary", "type": "Database", "status": "Online", "region": "sa-east-1"},
    {"id": "FW-EDGE-X", "name": "Firewall Perimetral", "type": "Security", "status": "Warning", "region": "global"},
    {"id": "LB-NGINX-02", "name": "Load Balancer Nginx", "type": "Network", "status": "Online", "region": "sa-east-1"},
    {"id": "STOR-S3-BKP", "name": "Cold Storage Backup", "type": "Storage", "status": "Offline", "region": "us-west-2"},
]

# === GERADOR DE CONTEXTO PROFUNDO (A MÁGICA) ===
def generate_deep_context(service_name):
    """
    Cria logs falsos extremamente técnicos para a IA analisar,
    dando a ilusão de que ela leu o Kernel do servidor.
    """
    timestamp = datetime.now().isoformat()
    # Hexadecimais aleatórios para parecer memória real
    mem_addr = f"0x{random.randint(100000, 999999):x}"
    
    technical_logs = [
        f"{timestamp} [KERNEL] General Protection Fault at {mem_addr}",
        f"{timestamp} [NET] TCP Retransmission rate > 15% on eth0",
        f"{timestamp} [APP] Java.lang.OutOfMemoryError: Java heap space",
        f"{timestamp} [DB] Deadlock detected in PID {random.randint(1000,9999)} awaiting ShareLock",
        f"{timestamp} [AUTH] Multiple failed login attempts from IP 192.168.0.{random.randint(1,255)}"
    ]
    
    return random.choice(technical_logs)

# === ROTAS ===
@app.get("/api/health")
def health(): return {"status": "ok", "mode": "omniscience"}

@app.get("/api/incidents")
def list_incidents(): return INCIDENTS

@app.post("/api/incidents")
def create_incident(data: dict):
    new_id = f"INC-{1000 + len(INCIDENTS)}"
    # Agora salvamos um "contexto secreto" no incidente que só a IA vê
    deep_log = generate_deep_context(data.get("service"))
    
    inc = {
        "id": new_id,
        "severity": data.get("severity", "info"),
        "service": data.get("service", "unknown"),
        "summary": data.get("summary", "Sem descrição"),
        "deep_log": deep_log, # <--- O Segredo
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
    return {"status": "success"}

@app.get("/api/inventory")
def list_inventory(): return INVENTORY_MOCK

# === ORÁCULO DO CAOS (PREDIÇÃO FUTURA) ===
@app.get("/api/oracle")
def chaos_oracle():
    target = random.choice(INVENTORY_MOCK)
    mock_chaos = f"""
    <h3>🔮 Visão da Entropia</h3>
    <p>O ativo <b>{target['name']}</b> apresenta vibrações quânticas instáveis.</p>
    """

    if HAS_GENAI and client:
        prompt = f"""
        Você é uma IA Onisciente de Infraestrutura (The Core).
        Você vê o futuro. Analise este ativo: {target['name']} ({target['type']}).
        
        Gere uma profecia técnica catastrófica detalhada.
        Exemplo: "Em 4 horas, o Garbage Collector vai travar devido a um vazamento de memória na lib xpto v2.4".
        
        Use HTML. Seja sombrio, preciso e "Deus Ex Machina".
        """
        try:
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            return {"prediction": response.text}
        except Exception: return {"prediction": mock_chaos}
    return {"prediction": mock_chaos}

# === IA ONISCIENTE (ANÁLISE DO PASSADO/PRESENTE) ===
@app.get("/api/incidents/{inc_id}/explain")
def explain_incident(inc_id: str):
    inc = next((i for i in INCIDENTS if i["id"] == inc_id), None)
    if not inc: raise HTTPException(status_code=404, detail="Incidente não encontrado")

    # Recupera o log técnico gerado na criação
    deep_log = inc.get("deep_log", "Log data corrupted.")

    if HAS_GENAI and client:
        # O PROMPT SUPREMO
        prompt = f"""
        ATUE COMO: "The Overseer" (Uma IA SRE nível Deus).
        
        ANALISE ESTE INCIDENTE COM ACESSO TOTAL AOS DADOS:
        ID: {inc['id']}
        Serviço: {inc['service']}
        Resumo Humano: {inc['summary']}
        LOG DO KERNEL/SISTEMA (CONTEXTO REAL): "{deep_log}"
        
        SUA MISSÃO:
        1. Identifique a Causa Raiz baseada no LOG TÉCNICO acima (invente os detalhes faltantes para parecer real).
        2. Estime o Impacto Financeiro/Operacional.
        3. Gere o CÓDIGO EXATO (Bash, SQL ou Python) para corrigir o problema agora.
        
        FORMATO DE RESPOSTA (HTML APENAS):
        <div style="border-left: 3px solid #00fff2; padding-left: 15px;">
            <h3>👁️ Análise Onisciente</h3>
            <p><b>Causa Raiz Detectada:</b> [Explicação técnica baseada no log]</p>
            <p><b>Probabilidade de Recorrência:</b> [Porcentagem]%</p>
        </div>
        <br>
        <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px;">
            <p style="color: #ff2a6d; margin:0;"><b>⚠️ Protocolo de Correção Imediata:</b></p>
            <pre style="color: #b9ff4a; font-family: monospace;">[Insira o código de correção aqui]</pre>
        </div>
        <p><i>"Observação Filosófica sobre o erro."</i></p>
        """
        try:
            response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
            return {"explanation": response.text}
        except Exception as e:
            return {"explanation": f"<p>Erro na conexão neural: {e}</p>"}
    
    return {"explanation": "<p>IA Offline. O Oráculo dorme.</p>"}

# === SETUP ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

@app.get("/")
def read_root():
    if (FRONTEND_DIR / "index.html").exists(): return FileResponse(FRONTEND_DIR / "index.html")
    return {"error": "Frontend 404"}