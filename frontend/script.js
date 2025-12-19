// === CONFIGURAÇÃO ===
const API_BASE = "https://sentineloneops-660011594323.southamerica-east1.run.app";

// === ELEMENTOS DA TELA ===
const tabela = document.getElementById("incTable");
const statusBadge = document.getElementById("backendStatus");
const btnRefresh = document.getElementById("btnRefresh");
const btnCreate = document.getElementById("btnCreateIncident");

// === FUNÇÕES DE AJUDA ===
function toast(titulo, msg) {
    // Cria um aviso flutuante simples
    const div = document.createElement("div");
    div.className = "toast";
    div.innerHTML = `<b>${titulo}</b><br>${msg}`;
    document.getElementById("toasts").appendChild(div);
    setTimeout(() => div.remove(), 4000);
}

function getBadge(severity) {
    // Retorna a cor certa para cada gravidade
    const cores = {
        crit: "crit",
        warn: "warn",
        info: "info",
        ok: "ok"
    };
    const tipo = cores[severity] || "info";
    return `<span class="sev ${tipo}"><i></i>${severity.toUpperCase()}</span>`;
}

// === LÓGICA PRINCIPAL ===

// 1. Buscar incidentes do Backend
async function carregarDados() {
    try {
        const res = await fetch(`${API_BASE}/api/incidents`);
        if (!res.ok) throw new Error("Erro na API");

        const lista = await res.json();
        
        // Atualizar status para ONLINE
        if (statusBadge) {
            statusBadge.textContent = "ONLINE";
            statusBadge.style.color = "var(--a-lime)";
        }

        renderizarTabela(lista);
        atualizarContadores(lista);

    } catch (erro) {
        console.error(erro);
        if (statusBadge) {
            statusBadge.textContent = "OFFLINE";
            statusBadge.style.color = "var(--a-mag)";
        }
    }
}

// 2. Desenhar a tabela na tela
function renderizarTabela(lista) {
    if (lista.length === 0) {
        tabela.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px; color: var(--muted);">Nenhum incidente encontrado.</td></tr>`;
        return;
    }

    tabela.innerHTML = lista.map(inc => `
        <tr>
            <td>${getBadge(inc.severity)}</td>
            <td><b>${inc.service}</b></td>
            <td class="muted">${inc.summary}</td>
            <td class="mono">${inc.id}</td>
            <td>
                <button class="btn ghost small" onclick="analisarIA('${inc.id}')">🤖 IA</button>
            </td>
        </tr>
    `).join("");
}

// 3. Atualizar os números (KPIs) lá em cima
function atualizarContadores(lista) {
    const crit = lista.filter(i => i.severity === "crit").length;
    const warn = lista.filter(i => i.severity === "warn").length;
    
    // Tenta atualizar se os elementos existirem
    const elCrit = document.getElementById("countCrit");
    const elWarn = document.getElementById("countWarn");
    const elTotal = document.getElementById("countTotal");

    if (elCrit) elCrit.textContent = crit;
    if (elWarn) elWarn.textContent = warn;
    if (elTotal) elTotal.textContent = lista.length;
}

// 4. Criar um novo incidente (Botão Simular)
async function criarIncidente() {
    try {
        await fetch(`${API_BASE}/api/incidents`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                severity: Math.random() > 0.5 ? "crit" : "warn",
                service: "frontend-app",
                summary: "Falha de conexão intermitente (Simulado)"
            })
        });
        toast("Sucesso", "Incidente criado no Backend!");
        carregarDados(); // Recarrega a lista na hora
    } catch (erro) {
        toast("Erro", "Não foi possível criar o incidente.");
    }
}

// 5. Função da IA (chamada pelo botão da tabela)
window.analisarIA = async function(id) {
    const section = document.getElementById("aiSection");
    const content = document.getElementById("aiContent");
    
    if (section) section.style.display = "block";
    if (content) content.innerHTML = "Consultando a IA... aguarde...";

    try {
        const res = await fetch(`${API_BASE}/api/incidents/${id}/explain`);
        const data = await res.json();
        if (content) content.innerHTML = data.explanation || "Sem resposta.";
    } catch (erro) {
        if (content) content.innerHTML = "Erro ao consultar IA (Verifique a API Key no backend).";
    }
};

// === INICIALIZAÇÃO ===
// Liga os botões às funções
if (btnCreate) btnCreate.addEventListener("click", criarIncidente);
if (btnRefresh) btnRefresh.addEventListener("click", carregarDados);

// Carrega dados assim que abre a página
carregarDados();

// Atualiza sozinho a cada 5 segundos
setInterval(carregarDados, 5000);