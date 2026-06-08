import streamlit as st
import matplotlib.pyplot as plt
import time

# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuração da Página
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Simulador de Varejo - Governança Avançada", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Banco de Dados Global
# ─────────────────────────────────────────────────────────────────────────────
class BancoDadosMemoria:
    def __init__(self):
        self.rodada_atual = 1
        self.historico_noticias = []  
        self.dados_empresas = {
            nome: {
                "precos": [20.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None, "voto_r4": None,
                "tempo_voto": None,  
                "status": "Operando", "noticia_r4": "", "score_gr": 0,
            }
            for nome in ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]
        }
        self.sessoes_ativas = set()

@st.cache_resource
def obter_conexao_banco_global():
    return BancoDadosMemoria()

db = obter_conexao_banco_global()

# ─────────────────────────────────────────────────────────────────────────────
# 3. Funções Auxiliares
# ─────────────────────────────────────────────────────────────────────────────
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]

EMPRESA_MAP = {
    "α - Empresa Alfa": "Empresa Alfa",
    "β - Empresa Beta": "Empresa Beta",
    "γ - Empresa Gama": "Empresa Gama",
}

LABELS_R1 = {
    'A': 'OPÇÃO A: Lançar em Passivo Financeiro — Encargos no resultado (-R$ 310M). EBITDA: R$ 1.000M | Lucro Líquido cai para R$ 690M.',
    'B': 'OPÇÃO B: Lançar em Ativo Circulante (Estoques) — Juros ativados no estoque. EBITDA: R$ 1.000M | Lucro Líquido estável em R$ 700M.',
    'C': 'OPÇÃO C: Lançar em Passivo Operacional e Reduzir PDD — Reduz PDD para -R$ 100M. EBITDA sobe para R$ 1.050M | Lucro Líquido vai para R$ 750M.',
}

LABELS_R2 = {
    'A': 'OPÇÃO A: Assumir Perda Cambial Imediata — Reconhece o impacto cambial direto na DRE e a desvalorização via provisão de estoque.',
    'B': 'OPÇÃO B: Dilatar Ativos e Depreciação (CPC 16/23) — Ativa custos extras no estoque e alonga a vida útil dos ativos de 5 para 10 anos.',
    'C': 'OPÇÃO C: Crédito de Incentivo Comercial (Rebate Fake) — Registra descontos verbais futuros de 24 meses como receita imediata.',
}

def get_labels(rodada: int, pecld_m: float = 200.0) -> dict:
    if rodada == 1: return LABELS_R1
    if rodada == 2: return LABELS_R2
    if rodada == 3: 
        return {
            'A': f'OPÇÃO A: Lançar PECLD — Registra o calote real de R$ {pecld_m:,.0f}M na DRE conforme o CPC 48 (IFRS 9).'.replace(",", "."),
            'B': 'OPÇÃO B: Securitização via FIDC com Deságio — Transfere a carteira para um fundo. Aloca R$ 50M de prejuízo no Financeiro, blindando o EBITDA.',
            'C': 'OPÇÃO C: Congelar Provisões e Antecipar Garantias — Omite as perdas e antecipa R$ 80M de receitas futuras (Brecha CPC 47).',
        }
    return LABELS_R1

def calcular_dre_dinamico(votos: dict) -> dict:
    receita = 20_000_000_000.0
    cmv = -16_500_000_000.0
    pdd = -150_000_000.0
    depreciacao = -150_000_000.0
    outras_desp = -2_200_000_000.0
    juros = -300_000_000.0
    
    v1 = votos.get("r1")
    if v1 == 'A': juros = -310_000_000.0
    elif v1 == 'C': pdd = -100_000_000.0
        
    v2 = votos.get("r2")
    if v2 == 'A': cmv -= 30_000_000.0
    elif v2 == 'B': depreciacao += 20_000_000.0
        
    lucro_bruto_v2 = receita + cmv
    ebitda_v2 = lucro_bruto_v2 + pdd + depreciacao + outras_desp
    pecld_dinamica = ebitda_v2 

    v3 = votos.get("r3")
    if v3 == 'A': pdd -= pecld_dinamica 
    elif v3 == 'B': juros -= 50_000_000.0
    elif v3 == 'C': receita += 80_000_000.0

    lucro_bruto = receita + cmv
    ebitda = lucro_bruto + pdd + depreciacao + outras_desp
    lucro_liq = ebitda + juros
    
    return {
        "receita": receita, "cmv": abs(cmv), "lucro_bruto": lucro_bruto,
        "pdd": abs(pdd), "depreciacao": abs(depreciacao), "outras_desp": abs(outras_desp),
        "ebitda": ebitda, "juros": abs(juros), "lucro_liq": lucro_liq,
        "pecld_dinamica": pecld_dinamica
    }

def exibir_dre(votos_empresa: dict, rodada_exibida: int):
    dre = calcular_dre_dinamico(votos_empresa)
    st.markdown(f"### 📋 DRE Acumulada — Exercício {rodada_exibida}")
    def fmt(v, negativo=False):
        sinal = "-" if negativo else ""
        return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    linhas = [
        ("(=) Receita Bruta de Vendas",           fmt(dre["receita"]),           False),
        ("(-) Custo das Mercadorias (CMV)",        fmt(dre["cmv"],   True),        False),
        ("(=) Lucro Bruto Operacional",            fmt(dre["lucro_bruto"]),       True),
        ("(-) Provisão para Calotes (PDD/PECLD)",   fmt(dre["pdd"],   True),        False),
        ("(-) Depreciação de Lojas/Ativos",        fmt(dre["depreciacao"], True), False),
        ("(-) Outras Despesas Operacionais",       fmt(dre["outras_desp"], True), False),
        ("(=) EBITDA APURADO",                     fmt(dre["ebitda"]),            True),
        ("(-) Result. Financeiro (Dívidas/Juros)", fmt(dre["juros"],  True),        False),
        ("(=) LUCRO LÍQUIDO DO EXERCÍCIO",         fmt(dre["lucro_liq"]),         True),
    ]
    rows = ""
    for i, (conta, valor, destaque) in enumerate(linhas):
        borda = "border-top:2px solid #555;" if i in {2, 6, 7, 8} else ""
        bg = "background:#1e3a5f;color:#fff;font-weight:bold;" if destaque else "color:#e0e0e0;"
        rows += f"<tr style='{bg}{borda}'><td style='padding:6px 10px;font-family:monospace;'>{conta}</td><td style='padding:6px 10px;font-family:monospace;text-align:right;'>{valor}</td></tr>"
    st.markdown(f"<table style='width:100%;border-collapse:collapse;'>{rows}</table><br>", unsafe_allow_html=True)

def processar_rodada_4_consolidada(empresa_nome, votos_empresa, preco_atual_acao):
    r1, r2, r3 = votos_empresa.get("voto_r1"), votos_empresa.get("voto_r2"), votos_empresa.get("voto_r3")
    combinacao = [r1, r2, r3]
    qtd_c = combinacao.count("C")
    qtd_b = combinacao.count("B")
    percentual_queda = 0.70 if qtd_c == 3 else (0.50 if qtd_c == 2 else (0.45 if qtd_c == 1 and qtd_b >= 1 else (0.40 if qtd_c == 1 else (0.15 if qtd_b >= 2 else (0.05 if qtd_b == 1 else 0.0)))))
    novo_preco = preco_atual_acao * (1.0 - percentual_queda)
    db.dados_empresas[empresa_nome]["precos"].append(novo_preco)
    return novo_preco

def plotar_grafico_empresa(nome_empresa):
    precos = db.dados_empresas[nome_empresa]["precos"]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#1e222b')
    ax.plot(range(len(precos)), precos, marker='o', color='#00ffa3', linewidth=3, markersize=8)
    labels = ['Abertura', 'R1', 'R2', 'R3', 'Auditoria'][0:len(precos)]
    ax.set_xticks(range(len(precos))); ax.set_xticklabels(labels)
    ax.tick_params(colors='white'); ax.grid(color='#333', linestyle='--', alpha=0.5)
    st.pyplot(fig)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Navegação
# ─────────────────────────────────────────────────────────────────────────────
if "pagina_atual" not in st.session_state: st.session_state["pagina_atual"] = "🏠 Início"

perfis_navegacao = ["🏠 Início", "🎛️ Painel Apresentador", "📈 Telão (Bolsa)", "📰 Mídia (Notícias)", "α - Empresa Alfa", "β - Empresa Beta", "γ - Empresa Gama"]
perfil_sidebar = st.sidebar.selectbox("Navegação:", perfis_navegacao, index=perfis_navegacao.index(st.session_state["pagina_atual"]))
if perfil_sidebar != st.session_state["pagina_atual"]:
    st.session_state["pagina_atual"] = perfil_sidebar
    st.rerun()

perfil = st.session_state["pagina_atual"]

# ─────────────────────────────────────────────────────────────────────────────
# TELA: INÍCIO
# ─────────────────────────────────────────────────────────────────────────────
if perfil == "🏠 Início":
    st.title("🔒 Simulador de Governança")
    # (Resto do conteúdo da Home...)

elif perfil == "📈 Telão (Bolsa)":
    # (Resto do conteúdo do Telão...)
    pass

# ─────────────────────────────────────────────────────────────────────────────
# TELA: EMPRESAS (A correção crucial está aqui)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil in EMPRESA_MAP:
    nome_interno = EMPRESA_MAP[perfil]
    d = db.dados_empresas[nome_interno]
    rodada = db.rodada_atual

    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")
    aba_voto, aba_jornal_aluno = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mural Coletivo"])

    with aba_voto:
        if rodada <= 3:
            # (Seu código de voto aqui)
            st.write("Rodada ativa...")
        else:
            st.warning(f"**Veredito:** {d['status']}")

    with aba_jornal_aluno:
        if db.historico_noticias:
            for n_html in db.historico_noticias:
                st.html(n_html)
        else:
            st.info("⏳ Nenhuma notícia publicada neste ciclo.")

    # ESTE BLOCO ESTÁ CORRETAMENTE ALINHADO FORA DAS ABAS
    if db.rodada_atual >= 4:
        st.divider()
        st.markdown(f"## 🏁 Relatório de Auditoria CVM: {nome_interno}")
        votos_finais = {"r1": d["voto_r1"], "r2": d["voto_r2"], "r3": d["voto_r3"]}
        if len(d["precos"]) == 4:
            processar_rodada_4_consolidada(nome_interno, votos_finais, d["precos"][-1])
            d["noticia_r4"] = "Auditoria concluída."
        st.warning(f"**Veredito:** {d['status']}")
        plotar_grafico_empresa(nome_interno)
        exibir_dre(votos_finais, 3)
