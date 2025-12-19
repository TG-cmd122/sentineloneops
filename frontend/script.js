// === CONFIGURAÇÃO ===
const API_BASE = "https://sentineloneops-660011594323.southamerica-east1.run.app";

// === ELEMENTOS DA TELA ===
const tabela = document.getElementById("incTable");
const statusBadge = document.getElementById("backendStatus");
const btnRefresh = document.getElementById("btnRefresh");
const btnCreate = document.getElementById("btnCreateIncident");

// Variável para guardar o gráfico (para poder deletar e recriar)
let myChart = null;

// === FUNÇÕES DE AJUDA ===
function toast(titulo, msg) {
    const div = document.createElement("div");
    div.className = "toast";
    div.innerHTML = `<b>${titulo}</b><br>${msg}`;
    document.getElementById("toasts").appendChild(div);
    setTimeout(() => div.remove(), 4000);
}

function getBadge(severity) {
    const cores = { crit: "crit", warn: "warn", info: "info", ok: "ok" };
    const tipo = cores[severity] || "info";
    return `<span class="sev ${tipo}"><i></i>${severity.toUpperCase()}</span>`;
}

// === LÓGICA DO GRÁFICO (CHART.JS) ===
function atualizarGrafico(crit, warn, total) {
    const ctx = document.getElementById('kpiChart');
    if (!ctx) return;

    const healthy = total - crit - warn;

    // Se o gráfico já existe, atualizamos os dados apenas
    if (myChart) {
        myChart.data.datasets[0].data = [crit, warn, (healthy < 0 ? 0 : healthy)];
        myChart.update();
        return;
    }

    // Se não existe, criamos um novo
    myChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Crítico', 'Alerta', 'Saudável'],
            datasets: [{
                data: [crit, warn, healthy],
                backgroundColor: [
                    '#ff3fb4', // Mag (Crítico)
                    '#ffc24a', // Amber (Warn)
                    '#b9ff4a'  // Lime (Saudável)
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }, // Esconde legenda padrão para ficar clean
                tooltip: {
                    backgroundColor: '#111',
                    bodyColor: '#fff',
                    borderColor: '#333',
                    borderWidth: 1
                }
            },
            cutout: '75%' // Deixa a rosca mais fina
        }
    });
}

// === LÓGICA PRINCIPAL ===

async function carregarDados() {
    try {
        const res = await fetch(`${API_BASE}/api/incidents`);
        if (!res.ok) throw new Error("Erro na API");

        const lista = await res.json();
        
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

function atualizarContadores(lista) {
    const crit = lista.filter(i => i.severity === "crit").length;
    const warn = lista.filter(i => i.severity === "warn").length;
    const total = lista.length;
    
    const elCrit = document.getElementById("countCrit");
    const elWarn = document.getElementById("countWarn");
    const elTotal = document.getElementById("countTotal");

    if (elCrit) elCrit.textContent = crit;
    if (elWarn) elWarn.textContent = warn;
    if (elTotal) elTotal.textContent = total;

    // Atualiza o gráfico com os novos números
    atualizarGrafico(crit, warn, total);
}

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
        carregarDados();
    } catch (erro) {
        toast("Erro", "Não foi possível criar o incidente.");
    }
}

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
        if (content) content.innerHTML = "Erro ao consultar IA.";
    }
};

// === INICIALIZAÇÃO ===
if (btnCreate) btnCreate.addEventListener("click", criarIncidente);
if (btnRefresh) btnRefresh.addEventListener("click", carregarDados);

carregarDados();

// Auto-Refresh a cada 5 segundos
setInterval(carregarDados, 5000);