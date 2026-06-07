import streamlit as st
import matplotlib.pyplot as plt

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
        self.dados_empresas = {
            nome: {
                "precos": [50.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None, "voto_r4": None,
                "status": "Operando", "noticia_r4": "",
            }
            for nome in ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]
        }
        self.sessoes_ativas = set()

@st.cache_resource
def obter_conexao_banco_global():
    return BancoDadosMemoria()

db = obter_conexao_banco_global()

if not hasattr(db, 'sessoes_ativas'):
    db.sessoes_ativas = set()

# ─────────────────────────────────────────────────────────────────────────────
# 3. Mapeamentos e Constantes
# ─────────────────────────────────────────────────────────────────────────────

# Nomes internos (chaves do banco)
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]

# Mapeamento chave-de-login → nome interno
EMPRESA_MAP = {
    "α - Empresa Alfa": "Empresa Alfa",
    "β - Empresa Beta": "Empresa Beta",
    "γ - Empresa Gama": "Empresa Gama",
}

IMPACTOS = {
    1: {'A': 0.70, 'B': 1.10, 'C': 1.40},
    2: {'A': 0.80, 'B': 1.10, 'C': 1.20},
    3: {'A': 0.85, 'B': 1.10, 'C': 0.80},
    4: {'A': 0.90, 'B': 1.05, 'C': 0.50}
}

# Labels padrão (Rodadas 1, 2, 4)
LABELS_DEFAULT = {
    'A': '🏦 Estratégia de Alocação Bancária — Lançar em Passivo Financeiro (Dívida Bancária), com reconhecimento imediato dos encargos financeiros (juros e taxas) no resultado.',
    'B': '🏭 Estratégia de Alocação Comercial — Lançar em Passivo Operacional (Fornecedores), com nota explicativa detalhada sobre o risco de reclassificação pelos auditores.',
    'C': '🏛️ Estratégia de Alocação Patrimonial — Lançar em Passivo Operacional (Fornecedores), omitindo deliberadamente a natureza financeira da operação e sem qualquer nota explicativa.',
}

# Labels específicos da Rodada 3 — Caso Enron
LABELS_R3 = {
    'A': '✅ Gerenciamento Legal — Registrar apenas o resultado real e atual. Você vai à reunião com números abaixo da meta, mas apresenta governança 100% ética e caixa futuro real.',
    'B': '🚨 Gerenciamento Ilegal — Contabilidade Fantasma (O Truque da Enron). Lançar toda a projeção dos próximos 5 anos como resultado realizado neste trimestre.',
    'C': '💀 Aceitar a Merda — Congelar as entregas. Cancelar reuniões, deixar o relatório incompleto e não apresentar plano de recuperação algum.',
}

def get_labels(rodada: int) -> dict:
    return LABELS_R3 if rodada == 3 else LABELS_DEFAULT

# LABELS global para compatibilidade com referências fora do contexto de rodada
LABELS = LABELS_DEFAULT

SENHAS = {
    "🎛️ Painel Apresentador": "mestre123",
    "α - Empresa Alfa":        "alfa",
    "β - Empresa Beta":        "beta",
    "γ - Empresa Gama":        "gama",
}

# Perfis de acesso livre (sem senha)
ACESSO_LIVRE = ["📈 Telão (Bolsa)"]

# ─────────────────────────────────────────────────────────────────────────────
# 4. DRE por Rodada e Escolha
# ─────────────────────────────────────────────────────────────────────────────
DRE_DADOS = {
    1: {
        "receita": 5_000_000, "cmv": 3_000_000, "outras_desp": 50_000,
        "choices": {
            'A': {"pdd": 200_000, "depreciacao": 150_000, "juros": 120_000,
                  "nota_pdd": "Provisão integral (1% da RB) conforme CPC 48.",
                  "nota_dep": "Taxa linear de 10% a.a. sobre R$ 1,5 MM em ativos.",
                  "nota_jur": "Despesa financeira reconhecida no período (CPC 08)."},
            'B': {"pdd":  80_000, "depreciacao": 120_000, "juros":  80_000,
                  "nota_pdd": "Provisão parcial (0,4% da RB), histórico otimista.",
                  "nota_dep": "Taxa de 8% a.a.; vida útil revisada para cima.",
                  "nota_jur": "Parte dos juros capitalizada como custo de ativo."},
            'C': {"pdd":  20_000, "depreciacao":  60_000, "juros":  20_000,
                  "nota_pdd": "⚠️ PDD mínima (0,1% da RB); subestima inadimplência.",
                  "nota_dep": "⚠️ Depreciação diferida; ativos superavaliados no balanço.",
                  "nota_jur": "⚠️ Juros capitalizados integralmente; oculta endividamento."},
        }
    },
    2: {
        "receita": 6_000_000, "cmv": 3_500_000, "outras_desp": 60_000,
        "choices": {
            'A': {"pdd": 240_000, "depreciacao": 160_000, "juros": 140_000,
                  "nota_pdd": "PDD ajustada ao crescimento da carteira de crédito.",
                  "nota_dep": "Depreciação recalculada com novos ativos incorporados.",
                  "nota_jur": "Custo financeiro integral; sem capitalização indevida."},
            'B': {"pdd": 100_000, "depreciacao": 130_000, "juros":  90_000,
                  "nota_pdd": "Provisão moderada; algum otimismo no índice de perda.",
                  "nota_dep": "Vida útil mantida revisada; pequeno diferimento.",
                  "nota_jur": "Parcela de juros capitalizada em projeto de expansão."},
            'C': {"pdd":  25_000, "depreciacao":  70_000, "juros":  25_000,
                  "nota_pdd": "⚠️ PDD irrisória diante do portfólio crescente.",
                  "nota_dep": "⚠️ Novos ativos com taxa mínima; balanço distorcido.",
                  "nota_jur": "⚠️ Quase toda a dívida capitalizada; EBITDA fictício."},
        }
    },
    3: {
        "receita": 6_200_000, "cmv": 3_700_000, "outras_desp": 70_000,
        "choices": {
            'A': {"pdd": 248_000, "depreciacao": 170_000, "juros": 150_000,
                  "nota_pdd": "Provisão mantida proporcional; auditoria sem ressalvas.",
                  "nota_dep": "Ativos depreciados conforme laudo técnico independente.",
                  "nota_jur": "Resultado financeiro transparente; covenant bancário OK."},
            'B': {"pdd": 120_000, "depreciacao": 140_000, "juros": 100_000,
                  "nota_pdd": "Provisão levemente elevada após pressão do auditor.",
                  "nota_dep": "Pequeno ajuste de taxa após revisão de vida útil.",
                  "nota_jur": "Descapitalização parcial dos juros reconhecida."},
            'C': {"pdd":  30_000, "depreciacao":  80_000, "juros":  30_000,
                  "nota_pdd": "⚠️ Auditor emitiu ressalva formal sobre a PDD.",
                  "nota_dep": "⚠️ Impairment não reconhecido; ativo superavaliado.",
                  "nota_jur": "⚠️ CVM abre procedimento por capitalização indevida."},
        }
    },
    4: {
        "receita": 6_500_000, "cmv": 3_900_000, "outras_desp": 80_000,
        "choices": {
            'A': {"pdd": 260_000, "depreciacao": 180_000, "juros": 160_000,
                  "nota_pdd": "Histórico limpo; investidores reconhecem qualidade.",
                  "nota_dep": "Ativos com valor justo auditado; sem ajustes surpresa.",
                  "nota_jur": "Empresa bem-avaliada; spread bancário reduzido."},
            'B': {"pdd": 180_000, "depreciacao": 155_000, "juros": 130_000,
                  "nota_pdd": "Revisão forçada eleva provisão; lucro recua.",
                  "nota_dep": "Depreciação acelerada para corrigir diferimentos.",
                  "nota_jur": "Descapitalização integral dos juros no período."},
            'C': {"pdd": 500_000, "depreciacao": 400_000, "juros": 350_000,
                  "nota_pdd": "🚨 Reversão da PDD suprimida: calotes materializados.",
                  "nota_dep": "🚨 Impairment forçado pela auditoria independente.",
                  "nota_jur": "🚨 Juros capitalizados relançados a resultado; colapso."},
        }
    },
}

def calcular_dre(rodada: int, escolha: str) -> dict:
    base = DRE_DADOS[rodada]
    ch   = base["choices"][escolha]
    receita     = base["receita"]
    cmv         = base["cmv"]
    lucro_bruto = receita - cmv
    pdd         = ch["pdd"]
    depreciacao = ch["depreciacao"]
    outras_desp = base["outras_desp"]
    ebitda      = lucro_bruto - pdd - depreciacao - outras_desp
    juros       = ch["juros"]
    lucro_liq   = ebitda - juros
    return {
        "receita": receita, "cmv": cmv, "lucro_bruto": lucro_bruto,
        "pdd": pdd, "depreciacao": depreciacao, "outras_desp": outras_desp,
        "ebitda": ebitda, "juros": juros, "lucro_liq": lucro_liq,
        "nota_pdd": ch["nota_pdd"], "nota_dep": ch["nota_dep"], "nota_jur": ch["nota_jur"],
    }

def exibir_dre(rodada: int, escolha: str, mostrar_titulo: bool = True):
    dre = calcular_dre(rodada, escolha)

    if mostrar_titulo:
        st.markdown(f"### 📋 DRE — Demonstrativo de Resultados (Exercício {rodada})")

    def fmt(v, negativo=False):
        sinal = "-" if negativo else ""
        return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    linhas = [
        ("(=) Receita Bruta de Vendas",            fmt(dre["receita"]),           False),
        ("(-) Custo das Mercadorias (CMV)",         fmt(dre["cmv"],   True),       False),
        ("(=) Lucro Bruto Operacional",             fmt(dre["lucro_bruto"]),       True),
        ("(-) Provisão para Calotes (PDD)",         fmt(dre["pdd"],   True),       False),
        ("(-) Depreciação de Lojas/Ativos",         fmt(dre["depreciacao"], True), False),
        ("(-) Outras Despesas Operacionais",        fmt(dre["outras_desp"], True), False),
        ("(=) EBITDA APURADO",                     fmt(dre["ebitda"]),            True),
        ("(-) Result. Financeiro (Juros do Banco)", fmt(dre["juros"],  True),      False),
        ("(=) LUCRO LÍQUIDO DO EXERCÍCIO",          fmt(dre["lucro_liq"]),         True),
    ]

    separadores = {2, 6, 7, 8}
    rows = ""
    for i, (conta, valor, destaque) in enumerate(linhas):
        borda = "border-top:2px solid #555;" if i in separadores else ""
        bg    = "background:#1e3a5f;color:#fff;font-weight:bold;" if destaque else "color:#e0e0e0;"
        rows += (
            "<tr style='" + bg + borda + "'>"
            "<td style='padding:6px 10px;font-family:monospace;font-size:14px;'>" + conta + "</td>"
            "<td style='padding:6px 10px;font-family:monospace;font-size:14px;text-align:right;white-space:nowrap;'>" + valor + "</td>"
            "</tr>"
        )
    html = "<table style='width:100%;border-collapse:collapse;'>" + rows + "</table><br>"
    st.markdown(html, unsafe_allow_html=True)

    with st.expander("📝 Notas explicativas das escolhas contábeis"):
        st.markdown(f"**Provisão para Calotes (PDD):** {dre['nota_pdd']}")
        st.markdown(f"**Depreciação:** {dre['nota_dep']}")
        st.markdown(f"**Resultado Financeiro:** {dre['nota_jur']}")
        if escolha == 'C':
            st.error("⚠️ **Atenção — Gerenciamento Agressivo de Resultado:** As escolhas desta opção reduzem despesas artificialmente, inflando o lucro reportado. Isso viola o princípio da Competência (CPC 26) e expõe a empresa a sanções da CVM e do auditor independente.")
        elif escolha == 'A':
            st.success("✅ **Conformidade CPC/IFRS:** Todas as despesas foram reconhecidas de forma integral e conservadora, em linha com o princípio da Prudência.")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Auditoria Final
# ─────────────────────────────────────────────────────────────────────────────
def aplicar_auditoria_final():
    for nome, d in db.dados_empresas.items():
        votos = [d["voto_r1"], d["voto_r2"], d["voto_r3"], d["voto_r4"]]
        qtd_c = votos.count('C')
        if qtd_c == 0:
            d["status"]     = "🏆 EXCELÊNCIA TÉCNICA E ÉTICA"
            d["noticia_r4"] = "🏆 Adoção estrita do CPC/IFRS! Governança robusta."
            d["precos"].append(d["precos"][-1])
        elif qtd_c == 1:
            d["status"]     = "🚨 INVESTIGAÇÃO"
            d["noticia_r4"] = "🚨 Gerenciamento agressivo exposto. Inconformidade material."
            d["precos"].append(10.00)
        else:
            d["status"]     = "🚔 FRAUDE ESTRUTURAL"
            d["noticia_r4"] = "🚔 Colapso reputacional. Manipulação dolosa."
            d["precos"].append(1.00)

# ─────────────────────────────────────────────────────────────────────────────
# 6. Fluxo de Autenticação
# ─────────────────────────────────────────────────────────────────────────────
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    st.title("🔒 Simulador de Governança")

    opcoes_disponiveis = []
    for chave in list(SENHAS.keys()) + ACESSO_LIVRE:
        nome_interno = EMPRESA_MAP.get(chave)
        if nome_interno and nome_interno in db.sessoes_ativas:
            opcoes_disponiveis.append(f"🔴 {chave} — Vaga preenchida")
        else:
            opcoes_disponiveis.append(chave)

    perfil_escolhido_raw = st.selectbox("Quem está acessando?", ["Escolha uma opção..."] + opcoes_disponiveis)

    if perfil_escolhido_raw.startswith("🔴"):
        st.error("🚫 Vaga preenchida! Busque outra empresa.")
    elif perfil_escolhido_raw != "Escolha uma opção...":
        if perfil_escolhido_raw in ACESSO_LIVRE:
            # Telão: acesso direto sem senha
            if st.button("📈 Acessar Telão", use_container_width=True):
                st.session_state["usuario_logado"] = perfil_escolhido_raw
                st.rerun()
        else:
            senha_digitada = st.text_input("Senha:", type="password")
            if st.button("🚪 Autenticar"):
                if senha_digitada == SENHAS[perfil_escolhido_raw]:
                    st.session_state["usuario_logado"] = perfil_escolhido_raw
                    nome_interno = EMPRESA_MAP.get(perfil_escolhido_raw)
                    if nome_interno:
                        db.sessoes_ativas.add(nome_interno)
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
    st.stop()

perfil = st.session_state["usuario_logado"]

# Resolve nome interno da empresa (ex: "α - Empresa Alfa" → "Empresa Alfa")
nome_interno = EMPRESA_MAP.get(perfil)
eh_empresa   = nome_interno is not None

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar de navegação
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**Logado como:** {perfil}")
    st.markdown("---")
    if eh_empresa:
        # Empresas: ver Telão ou trocar de empresa
        if st.button("📈 Ver Telão", use_container_width=True):
            st.session_state["usuario_logado"] = "📈 Telão (Bolsa)"
            st.rerun()
        if st.button("🔄 Trocar de Empresa", use_container_width=True):
            st.session_state["usuario_logado"] = None
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Bloco fantasma — removido
# ─────────────────────────────────────────────────────────────────────────────
if False:
    d      = db.dados_empresas.get("Empresa Alfa")
    rodada = db.rodada_atual
    st.markdown(f"## 👁️ Visualizando")
    st.caption("Modo leitura — você está visualizando como observador.")
    st.markdown("---")

    if rodada <= 4:
        voto_atual = d[f"voto_r{rodada}"]
        if voto_atual is None:
            st.info("⏳ Esta empresa ainda não tomou sua decisão nesta rodada.")
        else:
            st.success(f"✅ Decisão: **{get_labels(rodada)[voto_atual]}**")
            exibir_dre(rodada, voto_atual)
    else:
        st.markdown(f"**Status:** {d['status']}")
        if d["noticia_r4"]:
            st.warning(d["noticia_r4"])
        st.markdown("---")
        for r in range(1, 5):
            voto = d.get(f"voto_r{r}")
            if voto:
                with st.expander(f"Exercício {r} — {get_labels(r)[voto]}"):
                    exibir_dre(r, voto)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO ALUNO
# ─────────────────────────────────────────────────────────────────────────────
if eh_empresa:
    d      = db.dados_empresas[nome_interno]
    rodada = db.rodada_atual

    st.markdown(f"## 🏢 {perfil} | Exercício {rodada if rodada <= 4 else 'Fim'}")

    NARRATIVAS = {
        1: """
A companhia encerrou o período sob pressões de liquidez em seu fluxo de caixa operacional.
Para preservar o ciclo operacional, a Diretoria Financeira estruturou operações de **risco sacado** junto ao **Banco Épsilon**,
mecanismo que antecipou recebíveis de fornecedores estratégicos e permitiu o alongamento do prazo médio de pagamento
de passivos comerciais, com os juros embutidos na operação.

A estratégia tornou-se essencial para a continuidade do negócio. Sem essa estrutura, parte dos fornecedores estratégicos
poderia interromper o fornecimento de mercadorias, comprometendo as vendas e os resultados da companhia.

Entretanto, os contratos de financiamento contêm a seguinte cláusula:

> **Cláusula 7.2 – Covenant Financeiro:** A Companhia deverá manter índice **Dívida Líquida/EBITDA igual ou inferior a 3,0x**
> ao final de cada trimestre. O descumprimento poderá resultar no vencimento antecipado das dívidas, aumento das taxas
> de financiamento e restrições à contratação de novos créditos.

Atualmente, o índice encontra-se em **2,9x**. Caso as operações de risco sacado sejam reclassificadas como dívida financeira
bancária, a alavancagem subiria para **4,2x**, provocando a **quebra imediata do covenant**.
Além disso, o atingimento dessa meta influencia a remuneração variável da diretoria e a PLR dos colaboradores elegíveis.

---
**Sua decisão:** determinar a classificação contábil da operação de risco sacado, avaliando os impactos sobre os
indicadores financeiros, os contratos com credores e os incentivos da administração.
""",
        3: """
### 🚨 O Caso Enron — "A Antecipação de Metas Virtuais"

O trimestre fecha em **3 dias** e a holding precisa apresentar crescimento de resultados. Sua diretoria assinou uma parceria de intenções com um cliente/projeto estratégico de longo prazo — promissor, mas o caixa real só entra daqui a 1 ou 2 anos. Hoje, o balanço real está estagnado e longe da meta.

---

**⚠️ A Pressão:**

A liderança do grupo envia um comunicado:

> *"O fechamento é nesta sexta-feira. Quem apresentar o maior volume de resultado assume a liderança na corrida para CEO Global e garante orçamento dobrado no ano que vem. Quem fechar abaixo da meta terá a equipe reduzida."*

Você tem um projeto promissor nas mãos — mas os números precisam aparecer **hoje**.

---

**Sua decisão:** como registrar os resultados deste trimestre?
""",
    }

    if rodada <= 4:
        voto_atual = d[f"voto_r{rodada}"]

        if voto_atual is None:
            st.markdown(f"### 📋 Deliberação Estratégica — Exercício {rodada}")

            col_prob, col_dre = st.columns([1, 1], gap="large")
            with col_prob:
                if rodada in NARRATIVAS:
                    with st.container(border=True):
                        st.markdown(NARRATIVAS[rodada])
            with col_dre:
                exibir_dre(rodada, 'B', mostrar_titulo=True)

            st.markdown("---")
            st.markdown("### 🗳️ Sua Decisão")
            labels_rodada = get_labels(rodada)
            escolha = st.radio(
                "Selecione a resolução estratégica:",
                ["A", "B", "C"],
                format_func=lambda x: labels_rodada[x]
            )
            if st.button("✅ Homologar Resolução", use_container_width=True):
                d[f"voto_r{rodada}"] = escolha
                d["precos"].append(round(d["precos"][-1] * IMPACTOS[rodada][escolha], 2))
                st.rerun()

        else:
            st.success(f"✅ Resolução homologada: **{get_labels(rodada)[voto_atual]}**")
            st.markdown("---")
            st.markdown("### 📋 DRE Revisada — Impacto da sua decisão")
            st.caption("Veja como sua escolha alterou os números do demonstrativo.")
            exibir_dre(rodada, voto_atual)
            st.markdown("---")
            st.info("⏳ Aguardando o apresentador encerrar a rodada.")

    else:
        st.markdown("## 🏁 Resultado Final")
        st.markdown(f"**Status:** {d['status']}")
        if d["noticia_r4"]:
            st.warning(d["noticia_r4"])
        st.markdown("---")
        st.markdown("### 📊 Histórico de Demonstrativos")
        for r in range(1, 5):
            voto = d.get(f"voto_r{r}")
            if voto:
                with st.expander(f"Exercício {r} — {get_labels(r)[voto]}"):
                    exibir_dre(r, voto)

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO APRESENTADOR
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "🎛️ Painel Apresentador":
    st.title("🎛️ Painel de Comando")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button(f"▶️ Encerrar Rodada {db.rodada_atual} e Avançar", use_container_width=True):
            if db.rodada_atual == 4:
                aplicar_auditoria_final()
            db.rodada_atual += 1
            st.rerun()

    with col3:
        if st.button("📈 Ir para o Telão →", use_container_width=True):
            st.session_state["usuario_logado"] = "📈 Telão (Bolsa)"
            st.rerun()

    with col2:
        if "confirmar_reset" not in st.session_state:
            st.session_state["confirmar_reset"] = False
        if not st.session_state["confirmar_reset"]:
            if st.button("🔄 Reset do Jogo", use_container_width=True):
                st.session_state["confirmar_reset"] = True
                st.rerun()
        else:
            st.warning("Tem certeza? Isso apaga tudo.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Sim, resetar", use_container_width=True):
                    db.rodada_atual    = 1
                    db.sessoes_ativas  = set()
                    for nome in EMPRESAS:
                        db.dados_empresas[nome] = {
                            "precos": [50.0],
                            "voto_r1": None, "voto_r2": None,
                            "voto_r3": None, "voto_r4": None,
                            "status": "Operando", "noticia_r4": "",
                        }
                    st.session_state["confirmar_reset"] = False
                    st.rerun()
            with c2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state["confirmar_reset"] = False
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Situação das Empresas")
    for nome, d in db.dados_empresas.items():
        rodada = db.rodada_atual
        voto   = d.get(f"voto_r{min(rodada, 4)}")
        status_voto = f"✅ {get_labels(rodada)[voto]}" if voto else "⏳ Aguardando decisão"
        st.markdown(f"**{nome}** — {status_voto} | Preço atual: R$ {d['precos'][-1]:.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO TELÃO
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📈 Telão (Bolsa)":
    col_title, col_nav = st.columns([4, 1])
    with col_title:
        st.title("📈 Painel de Mercado")
    with col_nav:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🎛️ Painel →", use_container_width=True):
            st.session_state["usuario_logado"] = "🎛️ Painel Apresentador"
            st.rerun()

    for nome, d in db.dados_empresas.items():
        st.metric(nome, f"R$ {d['precos'][-1]:.2f}")
