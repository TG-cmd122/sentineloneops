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

# Tenta importar a lib do Google, se falhar, segue sem ela
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

# === PERSISTÊNCIA ===
# Garante que o arquivo é criado na mesma pasta do app.py
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

# --- NOVO: ROTA PARA APAGAR TUDO ---
@app.delete("/api/incidents")
def clear_all_incidents():
    INCIDENTS.clear()  # Limpa a lista da memória
    save_data(INCIDENTS)  # Salva a lista vazia no arquivo
    return {"status": "success", "message": "Todos os incidentes foram apagados."}
# -----------------------------------

# === IA COPILOT (MODO HÍBRIDO: REAL OU MOCK) ===
@app.get("/api/incidents/{inc_id}/explain")
def explain_incident(inc_id: str):
    # 1. Achar o incidente
    inc = next((i for i in INCIDENTS if i["id"] == inc_id), None)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente não encontrado")

    # 2. Preparar a resposta de "backup" (Simulada)
    mock_explanation = f"""
    <p><b>🤖 Análise (Modo Offline/Fallback):</b></p>
    <p>O serviço <b>{inc['service']}</b> gerou um alerta de severidade <b>{inc['severity']}</b>.</p>
    <ul>
        <li><b>Diagnóstico:</b> O sistema de IA não pôde ser contatado, mas o padrão sugere saturação de recursos ou timeout.</li>
        <li><b>Ação Recomendada:</b> Verifique os logs da aplicação e reinicie o serviço se necessário.</li>
        <li><b>Comando:</b> <code>systemctl status {inc['service']}</code></li>
    </ul>
    """

    # 3. Tentar chamar a IA de verdade
    if client:
        prompt = f"""
        Aja como um SRE Sênior. Analise este incidente:
        ID: {inc['id']} | Serviço: {inc['service']} | Severidade: {inc['severity']} | Resumo: {inc['summary']}
        
        Responda APENAS em HTML (tags <p>, <b>, <ul>, <li>, <code>). Sem markdown ```html.
        Estrutura: Análise breve, Causas Raízes, Comandos de Mitigação.
        """
        try:
            # Tenta o modelo mais comum
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            return {"explanation": response.text}
        except Exception as e:
            print(f"⚠️ Erro ao chamar Gemini (usando fallback): {e}")
            # Se der erro, retorna o Mock silenciosamente
            return {"explanation": mock_explanation}
    
    # Se não tiver cliente configurado, retorna Mock
    return {"explanation": mock_explanation}


# === SERVIR FRONTEND (CORREÇÃO DE CAMINHO) ===
# Calcula a pasta 'frontend' subindo um nível a partir de 'backend'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

print("-" * 40)
print(f"📂 Verificando pastas...")
print(f"   Backend rodando em: {BASE_DIR}")
print(f"   Procurando Frontend em: {FRONTEND_DIR}")

if not FRONTEND_DIR.exists():
    print("❌ ERRO: Pasta 'frontend' não encontrada!")
    print("   Certifique-se de que a estrutura é: sentineloneops/frontend")
else:
    print("✅ Pasta 'frontend' encontrada!")
    if (FRONTEND_DIR / "index.html").exists():
        print("✅ Arquivo 'index.html' encontrado!")
    else:
        print("❌ AVISO: 'index.html' não está dentro da pasta frontend!")
print("-" * 40)

# Rota Raiz (Resolve o problema do F5/404)
@app.get("/")
def read_root():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "index.html não encontrado", "path_procurado": str(index_path)}

# Monta arquivos estáticos (CSS/JS)
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")