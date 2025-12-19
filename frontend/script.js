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
    // Nota: O CSS novo usa classes .sev.crit etc.
    return `<span class="sev ${tipo}"><i></i>${severity.toUpperCase()}</span>`;
}

// === LÓGICA DO GRÁFICO (CHART.JS) ===
function atualizarGrafico(crit, warn, total) {
    const ctx = document.getElementById('kpiChart');
    if (!ctx) return;

    const healthy = total - crit - warn;

    // Se o gráfico já existe, atualizamos os dados apenas e saímos da função
    if (myChart) {
        myChart.data.datasets[0].data = [crit, warn, (healthy < 0 ? 0 : healthy)];
        myChart.update();
        return;
    }

    // Se não existe, cria um novo (Estilo Ultranova)
    myChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Crítico', 'Alerta', 'Saudável'],
            datasets: [{
                data: [crit, warn, healthy],
                backgroundColor: [
                    '#ff2a6d', // Neon Red
                    '#ffc24a', // Neon Amber
                    '#00fff2'  // Neon Cyan
                ],
                // Bordas escuras para separar as luzes (cor do fundo --bg-deep)
                borderColor: '#030512', 
                borderWidth: 3,
                hoverOffset: 10,
                
                // BRILHO NO GRÁFICO (Glow Effect)
                shadowColor: 'rgba(0, 255, 242, 0.5)',
                shadowBlur: 20,
                shadowOffsetX: 0,
                shadowOffsetY: 0,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: 20 },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(10, 15, 30, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255,255,255,0.2)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    titleFont: { family: 'Space Grotesk', size: 14 },
                    bodyFont: { family: 'Space Grotesk', size: 14, weight: 'bold' }
                }
            },
            cutout: '70%',
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });
} // <--- O ERRO ESTAVA AQUI: FALTAVA FECHAR ESSA CHAVE

// === LÓGICA PRINCIPAL ===

async function carregarDados() {
    try {
        const res = await fetch(`${API_BASE}/api/incidents`);
        if (!res.ok) throw new Error("Erro na API");

        const lista = await res.json();
        
        if (statusBadge) {
            statusBadge.textContent = "ONLINE";
            // Usando as variáveis CSS novas
            statusBadge.style.color = "var(--neon-lime)";
            statusBadge.style.textShadow = "0 0 10px var(--neon-lime)";
        }

        renderizarTabela(lista);
        atualizarContadores(lista);

    } catch (erro) {
        console.error(erro);
        if (statusBadge) {
            statusBadge.textContent = "OFFLINE";
            statusBadge.style.color = "var(--neon-red)";
            statusBadge.style.textShadow = "0 0 10px var(--neon-red)";
        }
    }
}

function renderizarTabela(lista) {
    if (lista.length === 0) {
        tabela.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px; color: var(--text-dim);">Nenhum incidente encontrado.</td></tr>`;
        return;
    }

    tabela.innerHTML = lista.map(inc => `
        <tr>
            <td>${getBadge(inc.severity)}</td>
            <td><b>${inc.service}</b></td>
            <td style="color: var(--text-muted)">${inc.summary}</td>
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