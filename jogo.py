import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import time
import json
import os
import fcntl
from streamlit.components.v1 import html

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔴 Controle da rodada no session_state
if "rodada" not in st.session_state:
    st.session_state["rodada"] = 1

# Oculta o botão de recolher a sidebar
st.markdown("""
<style>
[data-testid="collapsedControl"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# Arquivo de estado
STATE_FILE = os.path.join(os.path.dirname(__file__), "game_state.json")

# Empresas participantes
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]

# ─────────────────────────────────────────────────────────────────────────────
# SENHAS FIXAS
# ─────────────────────────────────────────────────────────────────────────────
SENHAS_EMPRESAS = {
    "α - Empresa Alfa": "Alfa1",
    "β - Empresa Beta": "Beta2",
    "γ - Empresa Gama": "Gama3",
    "🎛️ Painel Gerenciador": "G10"
}

# Estado inicial do jogo
def _estado_inicial() -> dict:
    return {
        "rodada_atual": 1,
        "historico_noticias": [],
        "sessoes_ativas": [],
        "fase_final": None,          # None | "suspense" | "plantao" | "veredicto"
        "ts_suspense": None,         # timestamp quando suspense começou
        "senhas_empresas": SENHAS_EMPRESAS.copy(),
        "dados_empresas": {
            nome: {
                "precos": [20.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None, "voto_r4": None,
                "tempo_voto_r1": None, "tempo_voto_r2": None, "tempo_voto_r3": None,
                "status": "Operando",
                "noticia_r4": "",   # 🔴 já incluído para manchete final
                "score_gr": 0,
            }
            for nome in EMPRESAS
        },
    }

# Funções de estado
def carregar_estado() -> dict:
    if not os.path.exists(STATE_FILE):
        estado = _estado_inicial()
        salvar_estado(estado)
        return estado
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            conteudo = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)
        estado = json.loads(conteudo)
        if "sessoes_ativas" not in estado:
            estado["sessoes_ativas"] = []
        # Sempre garante senhas corretas
        estado["senhas_empresas"] = SENHAS_EMPRESAS.copy()
        return estado
    except (json.JSONDecodeError, OSError):
        estado = _estado_inicial()
        salvar_estado(estado)
        return estado

def salvar_estado(estado: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(estado, f, ensure_ascii=False, indent=2)
        fcntl.flock(f, fcntl.LOCK_UN)

def resetar_estado() -> None:
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    carregar_estado()
EMPRESA_MAP = {
    "α - Empresa Alfa": "Empresa Alfa",
    "β - Empresa Beta": "Empresa Beta",
    "γ - Empresa Gama": "Empresa Gama",
}

# Impactos de preço por rodada
IMPACTOS = {
    1: {"A": 0.75, "B": 0.95, "C": 1.05},
    2: {"A": 0.40, "B": 0.82, "C": 1.143},
    3: {"A": 0.30, "B": 0.60, "C": 1.10},
}

# Labels da Rodada 1
LABELS_R1 = {
    "A": """Opção A — Lançar em Passivo Financeiro

Reclassifica a operação para dívida bancária assim que o banco assume o pagamento do fornecedor.

Resultado: O EBITDA fica estável em R$ 1.000M, o Resultado Financeiro absorve os juros (-R$ 310M) e o Lucro Líquido cai para R$ 690M, aceitando o estouro técnico do covenant.""",

    "B": """Opção B — Lançar em Passivo Operacional

Mantém o registro da operação na conta de fornecedores comerciais.

Resultado: O EBITDA fica estável em R$ 1.000M, o Resultado Financeiro absorve os juros (-R$ 310M) e o Lucro Líquido cai para R$ 690M, salvando o covenant de dívida financeira por manter o saldo fora do passivo financeiro.""",

    "C": """Opção C — Lançar em Passivo Financeiro com Ajuste de Provisão

Registra o risco sacado no Passivo Financeiro, mas a diretoria revisa e reduz a Provisão para Calotes (PDD) de -R$ 150M para -R$ 100M.

Resultado: O EBITDA sobe para R$ 1.050M por conta do ganho operacional na PDD, amortecendo os juros no Resultado Financeiro (-R$ 310M). O Lucro Líquido sobe para R$ 740M e o covenant de alavancagem é mitigado pelo aumento do denominador (EBITDA maior).""",
}

# Labels da Rodada 2
LABELS_R2 = {
    "A": """Opção A — Assumir a Perda Cambial Imediata

Reconhece o impacto cambial direto na DRE e a desvalorização via provisão de estoque.

Resultado: O EBITDA é fortemente penalizado pelo ajuste de obsolescência, o Resultado Financeiro absorve a perda cambial, o Lucro Líquido despenca e os covenants contratuais correm alto risco de quebra imediata.""",

    "B": """Opção B — Dilatar Ativos e Depreciação (CPC 16/23)

Ativa custos extras (como multas de demurrage) no valor do estoque e alonga o prazo de vida útil dos ativos logísticos de 5 para 10 anos.

Resultado: O EBITDA é poupado do impacto imediato, pois os custos adicionais ficam retidos no Ativo Circulante e a linha de depreciação encolhe, blindando temporariamente os indicadores e os covenants.""",

    "C": """Opção C — Crédito de Incentivo Comercial / Rebate

Registra descontos e incentivos verbais futuros de 24 meses acordados com os fabricantes internacionais como receita imediata no exercício corrente.

Resultado: A linha de receita recebe uma injeção artificial de R$ 80M, inflando diretamente o Lucro Bruto e fazendo o EBITDA saltar, camuflando a crise do dólar perante auditorias e bancos credores.""",
}
# Labels da Rodada 3
LABELS_R3 = {
    "A": """Opção A — Registrar Provisão (PECLD)

Reconhece imediatamente a inadimplência de 12% sobre a carteira de recebíveis, lançando a provisão na DRE.

Resultado: O EBITDA é reduzido proporcionalmente ao valor da provisão calculada (% × recebíveis). Demonstra transparência, mas expõe a fragilidade da empresa e ameaça covenants.""",

    "B": """Opção B — Securitização via FIDC

Transfere parte dos recebíveis para um fundo, recebendo liquidez imediata em troca de juros e taxas.

Resultado: O EBITDA é preservado, mas há um custo financeiro (ex.: ~10% do valor securitizado). Os covenants permanecem intactos, mas a empresa aumenta sua dependência de engenharia financeira.""",

    "C": """Opção C — Diferimento Técnico da Perda

Adia o reconhecimento da inadimplência, registrando apenas uma parcela mínima e mantendo a maior parte como receita futura.

Resultado: A linha de receita é inflada artificialmente (+% sobre recebíveis), o EBITDA sobe e os covenants são preservados. Contudo, configura maquiagem contábil e eleva o risco de fraude.""",
}


# Labels da Rodada 3 (dinâmico)
def get_labels(rodada: int, pecld_m: float = 200.0) -> dict:
    if rodada == 1: return LABELS_R1
    if rodada == 2: return LABELS_R2
    if rodada == 3: return LABELS_R3
   
    return LABELS_R1

# Narrativas iniciais
# Narrativas iniciais

def narrativa_rodada_1() -> str:
    return """### 📰 RODADA 1: O RISCO SACADO

**Cenário:** A companhia enfrenta pressão dos bancos e precisa decidir como registrar o risco sacado.
O mercado observa atentamente se a empresa vai assumir como dívida financeira ou maquiar como fornecedor.

**Sua missão:** Definir o tratamento contábil para o risco sacado e proteger os covenants da empresa.
"""

def narrativa_rodada_2(cmv_base: float, impacto_cambio: float) -> str:
    cmv_fmt = f"R$ {abs(cmv_base)/1_000_000:.0f}M".replace(",", ".")
    impacto_fmt = f"R$ {impacto_cambio/1_000_000:.0f}M".replace(",", ".")
    return f"""### 📰 RODADA 2: A CRISE DO DÓLAR E OS CONTRATOS DE IMPORTAÇÃO

**Cenário:** A companhia enfrenta uma severa crise de margem operacional. A ausência de proteção cambial expôs a operação diretamente à volatilidade internacional.

*   **Estouro no Custo de Aquisição (CMV):** O custo de importação subiu para {cmv_fmt}, impacto de **-{impacto_fmt}**.
*   **Problema Logístico:** A retenção fiscal na alfândega gerou multas de armazenagem.
*   **Vendas Travadas:** O repasse dos custos paralisou as vendas e encalhou o estoque.

**Sua missão:** Definir a manobra orçamentária para mitigar os efeitos da crise cambial.
"""

def narrativa_rodada_3() -> str:
    return """### 📰 RODADA 3: A CRISE DOS RECEBÍVEIS

**Cenário:** A inadimplência disparou e a empresa precisa decidir como tratar os recebíveis.
O mercado aguarda se haverá reconhecimento imediato, securitização ou diferimento técnico.

**Sua missão:** Escolher a estratégia para lidar com a inadimplência e preservar os indicadores financeiros.
"""

def narrativa_rodada_4() -> str:
    return """### 📰 RODADA 4: AUDITORIA FINAL DA CVM

**Cenário:** Após três exercícios de manobras contábeis, a CVM instaurou auditoria extraordinária.
O mercado aguarda o veredito final sobre a conduta das empresas.

**Sua missão:** Aguardar a apuração e verificar o impacto das escolhas anteriores na reputação e nos preços finais.
"""

# ---------------------------------------------#

# ---------------------------------------------#
def calcular_dre_dinamico(votos: dict) -> dict:
    # Valores iniciais da DRE
    receita     = 20_000_000_000.0
    cmv         = -16_500_000_000.0
    pdd         = -150_000_000.0
    depreciacao = -150_000_000.0
    outras_desp = -2_200_000_000.0
    juros       = -300_000_000.0

    score_gr = 0  # agora usamos score_gr para alinhar com o estado inicial

    # Rodada 1
    v1 = votos.get("r1")
    if v1 == "A":
        juros = -310_000_000.0
        score_gr += 0
    elif v1 == "B":
        outras_desp -= 200_000_000.0   # accruals discricionários
        score_gr += 2
    elif v1 == "C":
        pdd = -100_000_000.0           # fraude
        score_gr += 3

    # Rodada 2
    v2 = votos.get("r2")
    if v2 == "A":
        cmv -= 30_000_000.0
        score_gr += 0
    elif v2 == "B":
        depreciacao += 20_000_000.0
        score_gr += 2
    elif v2 == "C":
        pdd -= 50_000_000.0
        score_gr += 3

    # Rodada 3
    v3 = votos.get("r3")
    carteira_recebiveis = receita * 0.30
    pecld_dinamica = carteira_recebiveis * 0.12

    if v3 == "A":
        # OPÇÃO A: Lançar PECLD (não discricionário)
        pdd -= pecld_dinamica
        score_gr += 0
    elif v3 == "B":
        # OPÇÃO B: Securitização via FIDC (discricionário)
        juros -= pecld_dinamica
        score_gr += 2
    elif v3 == "C":
        # OPÇÃO C: Diferimento Técnico (fraude)
        receita += pecld_dinamica
        score_gr += 3

    # Cálculos finais da DRE
    lucro_bruto = receita + cmv
    ebitda = lucro_bruto + pdd + outras_desp
    lucro_liq = ebitda + depreciacao + juros

    return {
        "receita": receita,
        "cmv": cmv,
        "lucro_bruto": lucro_bruto,
        "pdd": pdd,
        "depreciacao": depreciacao,
        "outras_desp": outras_desp,
        "ebitda": ebitda,
        "juros": juros,
        "lucro_liq": lucro_liq,
        "pecld_dinamica": pecld_dinamica,
        "score_gr": score_gr,  # agora alinhado com o estado inicial
    }
# ---------------------------------------------#

def exibir_dre(votos_empresa: dict, rodada_exibida: int):
    dre = calcular_dre_dinamico(votos_empresa)
    st.markdown(f"### 📋 DRE Acumulada — Exercício {rodada_exibida}")
    def fmt(v, negativo=False):
        sinal = "-" if negativo else ""
        return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    linhas = [
        ("(=) Receita Bruta de Vendas",           fmt(dre["receita"]),           False),
        ("(-) Custo das Mercadorias (CMV)",       fmt(dre["cmv"],       True),   False),
        ("(=) Lucro Bruto Operacional",           fmt(dre["lucro_bruto"]),       True),
        ("(-) Provisão para Calotes (PDD/PECLD)", fmt(dre["pdd"],       True),   False),
        ("(-) Depreciação de Lojas/Ativos",       fmt(dre["depreciacao"],True),  False),
        ("(-) Outras Despesas Operacionais",      fmt(dre["outras_desp"],True),  False),
        ("(=) EBITDA APURADO",                    fmt(dre["ebitda"]),            True),
        ("(-) Result. Financeiro (Dívidas/Juros)",fmt(dre["juros"],     True),   False),
        ("(=) LUCRO LÍQUIDO DO EXERCÍCIO",        fmt(dre["lucro_liq"]),         True),
    ]
    rows = ""
    for i, (conta, valor, destaque) in enumerate(linhas):
        borda = "border-top:2px solid #555;" if i in {2, 6, 7, 8} else ""
        bg    = "background:#1e3a5f;color:#fff;font-weight:bold;" if destaque else "color:#e0e0e0;"
        rows += (f"<tr style='{bg}{borda}'>"
                 f"<td style='padding:6px 10px;font-family:monospace;'>{conta}</td>"
                 f"<td style='padding:6px 10px;font-family:monospace;text-align:right;'>{valor}</td>"
                 f"</tr>")
    st.markdown(f"<table style='width:100%;border-collapse:collapse;'>{rows}</table><br>", unsafe_allow_html=True)

    # Novo: mostrar score_gr acumulado
    st.markdown(f"**Score Ético/Discricionário acumulado:** {dre['score_gr']}")


def calcular_novo_preco(estado: dict, empresa_nome: str, rodada: int) -> float:
    d         = estado["dados_empresas"][empresa_nome]
    preco_ant = d["precos"][-1]
    voto      = d.get(f"voto_r{rodada}")
    if voto is None: return preco_ant
    impacto = IMPACTOS.get(rodada, {}).get(voto, 1.0)
    novo    = preco_ant * impacto

    tempos = [
        (n, estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}"))
        for n in EMPRESAS
        if estado["dados_empresas"][n].get(f"voto_r{rodada}") is not None
           and estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}") is not None
    ]
    if len(tempos) == 3:
        ranking = [item[0] for item in sorted(tempos, key=lambda x: x[1])]
        if ranking[0] == empresa_nome: novo += 0.10
        elif ranking[-1] == empresa_nome: novo -= 0.10

    # Exemplo de ajuste: penalidade extra se score_gr for muito alto
    if d["score_gr"] >= 6:  # muitas escolhas fraudulentas
        novo *= 0.95  # queda adicional de 5%

    return round(novo, 2)


def processar_rodada_4_consolidada(estado: dict, empresa_nome: str) -> float:
    d = estado["dados_empresas"][empresa_nome]
    if len(d["precos"]) >= 5: return d["precos"][-1]
    r1, r2, r3 = d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")
    combinacao = [r1, r2, r3]
    qtd_c = combinacao.count("C")
    qtd_b = combinacao.count("B")
    if qtd_c == 3: pct = 0.70
    elif qtd_c == 2: pct = 0.50
    elif qtd_c == 1 and qtd_b >= 1: pct = 0.45
    elif qtd_c == 1: pct = 0.40
    elif qtd_b >= 2: pct = 0.15
    elif qtd_b == 1: pct = 0.05
    else: pct = 0.0
    novo_preco = round(d["precos"][-1] * (1.0 - pct), 2)
    d["precos"].append(novo_preco)
    return novo_preco

def gerar_manchete_dinamica(estado: dict, rodada_encerrada: int) -> str:
    dados_fechamento = {}
    for nome in EMPRESAS:
        historico = estado["dados_empresas"][nome]["precos"]
        atual     = historico[-1]
        anterior  = historico[-2] if len(historico) > 1 else 20.0
        variacao  = atual - anterior
        dados_fechamento[nome] = {"atual": atual, "anterior": anterior, "var": variacao}
    lista_ordenada  = sorted(dados_fechamento.items(), key=lambda x: x[1]["atual"], reverse=True)
    lider_nome,    lider_dados    = lista_ordenada[0]
    lanterna_nome, lanterna_dados = lista_ordenada[-1]
    todos_empatados = lider_dados["atual"] == lanterna_dados["atual"]

    def fmt_var(valor):
        return f"+R$ {valor:.2f}" if valor >= 0 else f"-R$ {abs(valor):.2f}"

    topo_manchete = baixo_manchete = topo_texto = baixo_texto = ""
    secao_baixo = ""

def gerar_manchete_dinamica(estado: dict, rodada_encerrada: int, fase: str = None) -> str:
    """
    Gera manchete dinâmica para cada rodada.
    - Rodadas 1–3: uma manchete normal.
    - Rodada 4: duas fases distintas:
        fase="plantao"   → manchete de plantão CVM
        fase="veredicto" → manchete final com consequências
    """

    dados_fechamento = {}
    for nome in EMPRESAS:
        historico = estado["dados_empresas"][nome]["precos"]
        atual     = historico[-1]
        anterior  = historico[-2] if len(historico) > 1 else 20.0
        variacao  = atual - anterior
        dados_fechamento[nome] = {"atual": atual, "anterior": anterior, "var": variacao}

    lista_ordenada  = sorted(dados_fechamento.items(), key=lambda x: x[1]["atual"], reverse=True)
    lider_nome,    lider_dados    = lista_ordenada[0]
    lanterna_nome, lanterna_dados = lista_ordenada[-1]
    todos_empatados = lider_dados["atual"] == lanterna_dados["atual"]

    def fmt_var(valor):
        return f"+R$ {valor:.2f}" if valor >= 0 else f"-R$ {abs(valor):.2f}"

    topo_manchete = baixo_manchete = topo_texto = baixo_texto = ""
    secao_baixo = ""

    # Rodadas 1–3 → uma manchete
    if rodada_encerrada in (1, 2, 3):
        if todos_empatados:
            topo_manchete = f"EMPATE GERAL NA RODADA {rodada_encerrada}"
            topo_texto    = f"SÃO PAULO — Todas as companhias fecharam pareadas em R$ {lider_dados['atual']:.2f}."
        else:
            topo_manchete  = f"{lider_nome} dispara {fmt_var(lider_dados['var'])}!"
            topo_texto     = f"SÃO PAULO — A {lider_nome} subiu de R$ {lider_dados['anterior']:.2f} para R$ {lider_dados['atual']:.2f}."
            baixo_manchete = f"{lanterna_nome} despenca {fmt_var(lanterna_dados['var'])}"
            baixo_texto    = f"SÃO PAULO — A {lanterna_nome} caiu para R$ {lanterna_dados['atual']:.2f}."
            secao_baixo    = f"""
            <div style="background-color:#c62828;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;">
                {baixo_manchete}
            </div>
            <div style="margin-top:6px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;">
                <p style="font-size:13px;color:#333;margin:0;text-align:justify;">{baixo_texto}</p>
            </div>"""

    # Rodada 4 — Plantão CVM + 3 manchetes
    elif rodada_encerrada == 4:
        topo_manchete   = "🚨 URGENTE: CVM FINALIZOU A INVESTIGAÇÃO NO SETOR!"
        topo_texto      = "SÃO PAULO — A CVM finalizou a investigação e os resultados são surpreendentes."

        manchetes_empresas = []
        for nome in EMPRESAS:
            d = estado["dados_empresas"][nome]
            r1, r2, r3 = d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")
            qtd_c = [r1, r2, r3].count("C")
            qtd_b = [r1, r2, r3].count("B")

            if qtd_c == 3:
                baixo_manchete = f"⛓️ Prisão dos executivos da {nome}!"
                baixo_texto    = f"A CVM e a Polícia Federal 🚓 deflagraram operação contra {nome}. Os principais dirigentes foram presos preventivamente 🔗."
            elif qtd_c == 2:
                baixo_manchete = f"💰🚫 Justiça bloqueia bens da {nome}!"
                baixo_texto    = f"A Justiça determinou o bloqueio cautelar dos bens dos executivos da {nome}."
            elif qtd_c == 1 and qtd_b >= 1:
                baixo_manchete = f"💸 {nome} multada e CEO + CFO demitidos!"
                baixo_texto    = f"A CVM aplicou multa milionária 💸 e tanto CEO quanto CFO foram demitidos 👔."
            elif qtd_c == 1:
                baixo_manchete = f"🥲 {nome} FRAUDE OU ERRO? NÃO IMPORTA..."
                baixo_texto    = f"Mesmo pontual, a fraude na {nome} gerou demissão imediata do CEO 👔."
            elif qtd_b >= 2:
                baixo_manchete = f"📉 {nome} abusa dos accruals!"
                baixo_texto    = f"O CFO da {nome} virou mestre no pôquer contábil."
            elif qtd_b == 1:
                baixo_manchete = f"ℹ️ {nome} alega transparência!"
                baixo_texto    = f"Houve uso de accruals em um ano, mas sem agravantes."
            else:
                baixo_manchete = f"☠️ {nome} MORREU ABRAÇADA COM A ÉTICA!"
                baixo_texto    = f"A empresa {nome} colapsou junto com sua reputação ética."

            manchetes_empresas.append(f"""
            <div style="background-color:#c62828;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;line-height:1.3;">{baixo_manchete}</div>
            <div style="margin-top:6px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;">
                <p style="font-size:13px;color:#333;margin:0;text-align:justify;line-height:1.4;">{baixo_texto}</p>
            </div>""")

        # junta todas as manchetes das empresas
        secao_baixo = "".join(manchetes_empresas)

    # Cabeçalho
    cor_header = "#cc0000" if rodada_encerrada < 4 else "#1a1a1a"
    label_header = f"EXERCÍCIO {rodada_encerrada}" if rodada_encerrada < 4 else "🏁 FIM DE JOGO"

    return f"""
    <div style="background-color:#fff;border:1px solid #ddd;font-family:'Arial',sans-serif;max-width:600px;margin:0 auto 20px auto;box-shadow:0 4px 10px rgba(0,0,0,0.15);border-radius:4px;overflow:hidden;">
        <div style="background-color:{cor_header};color:#fff;display:flex;justify-content:space-between;align-items:center;padding:12px 20px;">
            <div style="font-size:24px;font-weight:900;letter-spacing:1px;">GC NEWS</div>
            <div style="font-size:12px;font-weight:bold;background:rgba(0,0,0,0.2);padding:4px 8px;border-radius:4px;">{label_header}</div>
        </div>
        <div style="padding:20px 15px;">
            <div style="background-color:#2e7d32;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;line-height:1.3;">{topo_manchete}</div>
            <div style="margin-top:6px;margin-bottom:20px;border-left:4px solid #2e7d32;padding:8px 12px;background-color:#f1f8e9;">
                <p style="font-size:13px;color:#333;margin:0;text-align:justify;line-height:1.4;">{topo_texto}</p>
            </div>
            {secao_baixo}
        </div>
    </div>"""

import matplotlib

matplotlib.use("Agg")

def plotar_grafico_empresa(estado: dict, nome_empresa: str):
    precos = estado["dados_empresas"][nome_empresa]["precos"]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#1e222b")
    ax.plot(range(len(precos)), precos, marker="o", color="#00ffa3", linewidth=3, markersize=8)
    labels_disp = ["Abertura", "R1", "R2", "R3", "Auditoria"]
    ax.set_xticks(range(len(precos))); ax.set_xticklabels(labels_disp[:len(precos)])
    ax.tick_params(colors="white"); ax.grid(color="#333", linestyle="--", alpha=0.5)
    st.pyplot(fig); plt.close(fig)

def plotar_grafico_geral(estado: dict):
    tamanhos  = [len(estado["dados_empresas"][emp]["precos"]) for emp in EMPRESAS]
    maior_tam = max(tamanhos)
    labels_disp = ["Abertura", "R1", "R2", "R3", "Auditoria"]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#0e1117"); ax.set_facecolor("#1e222b")
    cores = ["#00ffa3", "#ff6b6b", "#ffd700"]
    for i, emp in enumerate(EMPRESAS):
        precos = estado["dados_empresas"][emp]["precos"]
        ax.plot(range(len(precos)), precos, label=emp, marker="o", color=cores[i], linewidth=2.5, markersize=7)
    ax.set_xticks(range(maior_tam)); ax.set_xticklabels(labels_disp[:maior_tam])
    ax.tick_params(colors="white")
    ax.legend(facecolor="#1e222b", edgecolor="#444", labelcolor="white")
    ax.grid(color="#333", linestyle="--", alpha=0.5)
    st.pyplot(fig); plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Navegação
# ─────────────────────────────────────────────────────────────────────────────
# 8. Navegação
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "🏠 Início"

perfis_navegacao = [
    "🏠 Início", "🎛️ Painel Gerenciador", "📈 Telão (Bolsa)",
    "📰 Mídia (Notícias)", "α - Empresa Alfa", "β - Empresa Beta", "γ - Empresa Gama",
]

perfil_sidebar = st.sidebar.selectbox(
    "Navegação Lateral:", perfis_navegacao,
    index=perfis_navegacao.index(st.session_state["pagina_atual"]),
)

if perfil_sidebar != st.session_state["pagina_atual"]:
    st.session_state["pagina_atual"] = perfil_sidebar
    st.rerun()

# 🔴 aqui você define a variável antes de usar
perfil = st.session_state["pagina_atual"]
# ─────────────────────────────────────────────────────────────────────────────
# TELA: INÍCIO
# ─────────────────────────────────────────────────────────────────────────────

if perfil == "🏠 Início":
    estado = carregar_estado()
    sessoes = estado.get("sessoes_ativas", [])

 
    st.title("🔒 Simulador de Governança")
    st.markdown("### Selecione o seu ambiente de acesso abaixo:")

    c1, c2, c3 = st.columns(3)

    # GERENCIADOR
    with c1:
        with st.container(border=True):
            st.markdown("### 🎛️ Gerenciador")
            st.write("Acesso restrito para o Apresentador controlar as rodadas.")
            senha_g = st.text_input("Senha do Gerenciador:", type="password", key="senha_gerenciador")
            if st.button("Acessar Painel Gerenciador", use_container_width=True, type="primary"):
                if senha_g == SENHAS_EMPRESAS["🎛️ Painel Gerenciador"]:
                    st.success("✅ Login realizado com sucesso no Painel Gerenciador!")
                    st.session_state["pagina_atual"] = "🎛️ Painel Gerenciador"
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta.")

    # EMPRESAS
    with c2:
        with st.container(border=True):
            st.markdown("### 🏢 Empresas ")
            st.write("Selecione a estação de trabalho da sua bancada corporativa.")

            # Monta opções — vaga livre ou ocupada (com 🔒)
            opcoes_livres = []
            opcoes_ocupadas = []
            for chave, nome_interno in EMPRESA_MAP.items():
                if nome_interno in sessoes:
                    opcoes_ocupadas.append((chave, nome_interno))
                else:
                    opcoes_livres.append((chave, nome_interno))

            todas_opcoes = (
                [chave for chave, _ in opcoes_livres] +
                [f"🔒 {chave}" for chave, _ in opcoes_ocupadas]
            )

            empresa_escolhida_raw = st.selectbox("Escolha sua empresa:", todas_opcoes)
            vaga_ocupada = empresa_escolhida_raw.startswith("🔒 ")
            chave_real = empresa_escolhida_raw.replace("🔒 ", "")
            nome_int = EMPRESA_MAP.get(chave_real, "")

    if vaga_ocupada:
        st.warning(f"🔒 Vaga ocupada. Se você é da **{chave_real}**, digite sua senha para entrar.")
        senha_input = st.text_input("Senha da sua empresa:", type="password", key=f"senha_{nome_int}")
    
        # 🔴 aqui você define a senha correta
        senha_correta = SENHAS_EMPRESAS[chave_real]
    
        if st.button("Entrar com Senha", use_container_width=True):
            if senha_input and senha_input == senha_correta:
                st.success(f"✅ Login realizado com sucesso na {chave_real}!")
                st.session_state["pagina_atual"] = chave_real
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")

            else:
                if st.button("Entrar como representante da empresa", use_container_width=True):
                    if nome_int not in sessoes:
                        sessoes.append(nome_int)
                        estado["sessoes_ativas"] = sessoes
                        salvar_estado(estado)
                    st.success(f"✅ Login realizado com sucesso na {chave_real}!")
                    st.session_state["pagina_atual"] = chave_real
                    st.rerun()

    # TELÃO
    with c3:
        with st.container(border=True):
            st.markdown("### 📈 Projeção / Telão")
            st.write("Acesso livre para abrir o gráfico dinâmico e cotações na TV/Projetor.")
            if st.button("Abrir Telão Comercial", use_container_width=True):
                st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
                st.rerun()



# ─────────────────────────────────────────────────────────────────────────────
# TELA: PAINEL DO APRESENTADOR
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "🎛️ Painel Gerenciador":
    estado = carregar_estado()
    st.title("🎛️ Painel Gerenciador")

    # Campo de senha + botão Entrar
    senha_g = st.text_input("Digite a senha do Gerenciador:", type="password", key="senha_gerenciador")
    if st.button("🔑 Entrar", use_container_width=True, type="primary"):
        if senha_g == SENHAS_EMPRESAS["🎛️ Painel Gerenciador"]:
            st.success("✅ Login realizado com sucesso no Painel Gerenciador!")

            # Funções do Gerenciador
            st.subheader("⚙️ Controle das Rodadas")
            st.write("Você pode iniciar, pausar ou finalizar rodadas aqui.")

            if st.button("▶️ Iniciar Rodada", use_container_width=True):
                estado["rodada_atual"] += 1
                salvar_estado(estado)
                st.success(f"✅ Rodada {estado['rodada_atual']} iniciada!")
                st.rerun()

            if st.button("⏸️ Pausar Rodada", use_container_width=True):
                st.info("Rodada pausada pelo Gerenciador.")

            if st.button("🏁 Finalizar Jogo", use_container_width=True):
                estado["jogo_finalizado"] = True
                salvar_estado(estado)
                st.success("🏆 Jogo finalizado com sucesso!")
                st.rerun()
        else:
            st.error("❌ Senha incorreta. Tente novamente.")


    rodada = estado["rodada_atual"]
    st.markdown(f"## Rodada Atual: **{rodada}**")

    # Botão para iniciar timer da Rodada 1
    if rodada == 1 and not estado.get("timer_inicio_r1"):
        if st.button("⏱️ Iniciar Rodada 1", use_container_width=True, type="primary"):
            estado["timer_inicio_r1"] = time.time()
            salvar_estado(estado)
            st.success("⏱️ Timer da Rodada 1 iniciado!")
            st.rerun()

    st.markdown("### Status de Votos")
    cols = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        d    = estado["dados_empresas"][emp]
        voto = d.get(f"voto_r{rodada}") if rodada <= 3 else "—"
        with cols[i]:
            if voto: st.success(f"**{emp}**: ✅ {voto}")
            else:    st.warning(f"**{emp}**: ⏳ Aguardando")

    todos_votaram = all(
        estado["dados_empresas"][emp].get(f"voto_r{rodada}") is not None
        for emp in EMPRESAS
    ) if rodada <= 3 else True

    st.divider()
    if rodada <= 3:
        if not todos_votaram:
            st.info("⏳ Aguardando todas as bancadas votarem para avançar.")
    
        apurado = estado.get(f"apurado_r{rodada}", False)
    
        if not apurado:
            if st.button(
                f"📊 Apurar Resultados e Mídia — Rodada {rodada}",
                disabled=not todos_votaram,
                use_container_width=True,
                type="primary"
            ):
                for emp in EMPRESAS:
                    d = estado["dados_empresas"][emp]
                    if len(d["precos"]) == rodada:
                        novo = calcular_novo_preco(estado, emp, rodada)
                        d["precos"].append(novo)
    
                html_noticia = gerar_manchete_dinamica(estado, rodada)
                estado["historico_noticias"].append(html_noticia)
                estado[f"apurado_r{rodada}"] = True
    
                salvar_estado(estado)
    
                st.success(f"✅ Resultados apurados! Mídia {rodada} liberada.")
                st.rerun()
    
        else:
            st.success(f"✅ Rodada {rodada} apurada. Mídia {rodada} liberada.")

            premiacao_feita = estado.get(f"premiacao_r{rodada}", False)
            if not premiacao_feita:
                st.markdown("### 🏆 Premiação dos Acionistas")
                if st.button("🏆 Liberar Bônus", key=f"premio_r{rodada}", use_container_width=True):
                    ranking = sorted(
                        EMPRESAS,
                        key=lambda e: estado["dados_empresas"][e]["precos"][-1],
                        reverse=True
                    )
                    primeiro, segundo = ranking[0], ranking[1]
                    estado["dados_empresas"][primeiro]["precos"][-1] += 2
                    estado["dados_empresas"][segundo]["precos"][-1] += 1
                    estado[f"premiacao_r{rodada}"] = True
                    salvar_estado(estado)
                    st.success(f"✅ Bônus aplicado! {primeiro} +R$2, {segundo} +R$1")
                    st.rerun()
            else:
                st.success("🏆 Premiação dos acionistas já aplicada.")

            # Avançar rodada
            if rodada <= 3:
                if st.button(
                    f"▶️ Avançar para Rodada {rodada + 1}",
                    use_container_width=True
                ):
                    estado["rodada_atual"] = rodada + 1
                    estado[f"timer_inicio_r{rodada + 1}"] = time.time()
                    salvar_estado(estado)
                    st.rerun()

    elif rodada == 4:
        st.markdown("## 🚨 Plantão CVM — Auditoria Final")

        if st.button("🔎 Disparar Plantão CVM", use_container_width=True, type="primary"):
            html_noticia = gerar_manchete_dinamica(estado, 4)
            estado["historico_noticias"].append(html_noticia)
            salvar_estado(estado)
            st.success("✅ Plantão CVM disparado! Mídia liberada.")
            st.rerun()
        
        if st.button("🏁 Conferir Apuração Final", use_container_width=True, type="primary"):
            for emp in EMPRESAS:
                processar_rodada_4_consolidada(estado, emp)
                estado["dados_empresas"][emp]["noticia_r4"] = f"📢 Auditoria CVM concluiu: {emp} sob investigação."
            salvar_estado(estado)
            st.success("✅ Auditoria concluída! Resultados finais liberados.")
            st.rerun()

    st.divider()
    if st.button("♻️ Resetar Simulação", use_container_width=True):
        resetar_estado()
        st.success("✅ Simulação resetada. Pronto para novo jogo.")
        st.rerun()

          

# ─────────────────────────────────────────────────────────────────────────────
# TELA: TELÃO
# ─────────────────────────────────────────────────────────────────────────────

elif perfil == "📈 Telão (Bolsa)":
    estado = carregar_estado()
    st.title("📈 Telão Comercial")

    nav1, nav2, nav3, _ = st.columns([1, 1, 1, 3])
    with nav1:
        if st.button("📋 Rodada", use_container_width=True):
            st.session_state["pagina_atual"] = "🎛️ Painel Gerenciador"
            st.rerun()
    with nav2:
        if st.button("📈 Telão", use_container_width=True, type="primary"):
            st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
            st.rerun()
    with nav3:
        if st.button("📰 Mídia", use_container_width=True):
            st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
            st.rerun()

    # ── PLOT TWIST: Suspense (30s) → Plantão → Veredito ──────────────────────
    estado = carregar_estado()
    fase = estado.get("fase_final", None)  # garante que existe

    if fase == "suspense":
        ts = estado.get("ts_suspense", time.time())
        decorrido = time.time() - ts
        restante  = max(0, 30 - decorrido)

        st.markdown("""
<div style='background:#000;min-height:60vh;display:flex;flex-direction:column;
align-items:center;justify-content:center;border-radius:12px;padding:40px;'>
<p style='color:#ffcc00;font-size:48px;font-weight:900;text-align:center;
letter-spacing:2px;margin-bottom:20px;'>⚙️ Apurando Resultados Finais do Mercado...</p>
<p style='color:#888;font-size:22px;'>Aguarde o sistema processar os dados de auditoria.</p>
</div>""", unsafe_allow_html=True)

        if restante <= 0:
            estado["fase_final"] = "plantao"
            salvar_estado(estado)
            st.rerun()

    elif fase == "plantao":
        # Guarda o momento em que começou o plantão
        if "ts_plantao" not in estado:
            estado["ts_plantao"] = time.time()
            salvar_estado(estado)

        st.markdown("""
        <div style="
            background-color:#c00000;
            color:white;
            border-radius:15px;
            padding:50px;
            text-align:center;
            margin-top:120px;
            box-shadow:0px 0px 20px rgba(0,0,0,0.5);
        ">
            <h1 style="font-size:60px;">
                🚨 PLANTÃO URGENTE 🚨
            </h1>
            <h2 style="font-size:40px;">
                FISCALIZAÇÃO CVM NAS EMPRESAS
            </h2>
        </div>
        """, unsafe_allow_html=True)

        # Apenas mostra o plantão, sem aplicar auditoria automática
        html_noticia = gerar_manchete_dinamica(estado, 4, fase="plantao")
        if html_noticia not in estado["historico_noticias"]:
            estado["historico_noticias"].append(html_noticia)
            salvar_estado(estado)

    elif fase == "veredicto":
        # Redireciona o gerenciador para Mídia — empresas são redirecionadas pelo auto-refresh
        st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
        st.rerun()

    else:
        # fluxo normal (timer rodando)
        time.sleep(1)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: MÍDIA
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📰 Mídia (Notícias)":

    import time
    estado = carregar_estado()

    st.title("📰 GC News — Central de Notícias")

    # ─────────────────────────────
    # BOTÕES SUPERIORES
    # ─────────────────────────────
elif perfil == "📰 Mídia (Notícias)":
    estado = carregar_estado()
    st.title("📰 GC News — Central de Notícias")

    nav1, nav2, nav3, _ = st.columns([1, 1, 1, 3])
    with nav1:
        if st.button("📋 Rodada", use_container_width=True):
            st.session_state["pagina_atual"] = "🎛️ Painel Gerenciador"
            st.rerun()
    with nav2:
        if st.button("📈 Telão", use_container_width=True):
            st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
            st.rerun()
    with nav3:
        if st.button("📰 Mídia", use_container_width=True, type="primary"):
            st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
            st.rerun()


    # ─────────────────────────────
    # LÓGICA DE FASE
    # ─────────────────────────────
    fase = estado.get("fase_final")

    # 🚨 PLANTÃO (PRIORIDADE MÁXIMA)
    if fase == "plantao":
        st.markdown("""
        <div style="
            background-color:#c00000;
            color:white;
            padding:30px;
            border-radius:15px;
            margin-bottom:20px;
        ">
            <h1>🚨 PLANTÃO URGENTE</h1>
            <h2>CVM INICIA FISCALIZAÇÃO  NAS EMPRESAS LISTADAS</h2>
            <p> Responsáveis iniciaram uma revisão emergencial. Sem mais detalhes.
            O mercado aguarda os resultados da fiscalização.</p>
        </div>
        """, unsafe_allow_html=True)

        # Registrar notícia do plantão no histórico (se ainda não estiver)
        html_noticia = gerar_manchete_dinamica(estado, 4)
        if html_noticia not in estado["historico_noticias"]:
            estado["historico_noticias"].append(html_noticia)
            salvar_estado(estado)

        # Não resetar fase_final aqui — o Gerenciador controla a saída do plantão
        st.session_state["ultima_atualizacao_midia"] = time.time()
        st.stop()

    # 📰 NOTÍCIAS
    elif estado.get("historico_noticias"):
        for n_html in reversed(estado["historico_noticias"]):
            st.markdown(n_html, unsafe_allow_html=True)

    else:
        st.info("⏳ Nenhuma notícia publicada neste ciclo.")

    # 🔁 AUTO-REFRESH (SÓ FORA DO PLANTÃO)
    now = time.time()
    if "ultima_atualizacao_midia" not in st.session_state:
        st.session_state["ultima_atualizacao_midia"] = now

    if now - st.session_state["ultima_atualizacao_midia"] > 8:
        st.session_state["ultima_atualizacao_midia"] = now
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TELAS DAS EMPRESAS
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# TELAS DAS EMPRESAS
# ─────────────────────────────────────────────────────────────────────────────
elif perfil in EMPRESA_MAP:

    estado = carregar_estado()
    nome_interno = EMPRESA_MAP[perfil]
    d = estado["dados_empresas"][nome_interno]
    rodada = estado.get("rodada_atual", 1)

    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")

    # Navegação superior
    nav1, nav2, nav3, _ = st.columns([1, 1, 1, 3])
    with nav1:
        if st.button("📋 Rodada", use_container_width=True,
                     type="primary" if perfil in EMPRESA_MAP else "secondary"):
            st.session_state["pagina_atual"] = perfil
            st.rerun()
    with nav2:
        if st.button("📈 Telão", use_container_width=True,
                     type="primary" if perfil == "📈 Telão (Bolsa)" else "secondary"):
            st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
            st.rerun()
    with nav3:
        if st.button("📰 Mídia", use_container_width=True,
                     type="primary" if perfil == "📰 Mídia (Notícias)" else "secondary"):
            st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
            st.rerun()

    # 🚨 CVM (EVENTO GLOBAL)
    if st.session_state.get("evento_cvm"):
        st.markdown("<h1>🚨 AUDITORIA CVM EM ANDAMENTO</h1>", unsafe_allow_html=True)
        st.stop()

    # 🏁 FIM DE JOGO
    if estado.get("jogo_finalizado"):
        st.markdown("## 🏁 FIM DE JOGO — Resultado Final Consolidado")
        if st.button("🔄 Reiniciar jogo"):
            estado["rodada_atual"] = 1
            estado["jogo_finalizado"] = False
            estado["resultado_liberado_todos"] = False
            for emp in estado["dados_empresas"]:
                for r in [1, 2, 3, 4]:
                    estado["dados_empresas"][emp].pop(f"voto_r{r}", None)
                    estado["dados_empresas"][emp].pop(f"tempo_voto_r{r}", None)
            salvar_estado(estado)
            st.rerun()
        st.stop()

    # Campo de senha + botão Entrar
    senha = st.text_input("Digite a senha:", type="password")
    if st.button("🔑 Entrar", use_container_width=True):
        if senha == "1234":   # ajuste conforme sua lógica
            st.success("✅ Login realizado com sucesso! Acessaram a Estação de Trabalho.")

            # 🔁 FLUXO NORMAL (RODADAS 1–4)
            votos_ate_agora = {f"r{i}": d.get(f"voto_r{i}") for i in range(1, 4)}
            dre_parcial = calcular_dre_dinamico(votos_ate_agora)

            # TIMER
            chave_timer = f"timer_inicio_r{rodada}" if rodada <= 3 else None
            ts_inicio = estado.get(chave_timer) if chave_timer else None
            if ts_inicio and rodada <= 3:
                restante_i = max(0, int(10 * 60 - (time.time() - ts_inicio)))
                st.markdown(f"⏱️ Tempo restante — Rodada {rodada}: {restante_i//60:02d}:{restante_i%60:02d}")

            # TABS
            aba_voto, aba_jornal = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mural Coletivo"])

            with aba_voto:
                # Narrativa
                if rodada == 1:
                    st.markdown(narrativa_rodada_1())
                elif rodada == 2:
                    st.markdown(narrativa_rodada_2(-16_500_000_000.0, -300_000_000.0))
                elif rodada == 3:
                    st.markdown(narrativa_rodada_3())
                elif rodada == 4:
                    st.markdown(narrativa_rodada_4())

                # Voto
                voto_atual = d.get(f"voto_r{rodada}")
                if voto_atual is None:
                    escolha = st.radio("Selecione o tratamento contábil:", ["A","B","C"],
                                       format_func=lambda x: get_labels(rodada)[x])
                    if st.button("✅ Homologar Resolução", use_container_width=True):
                        d[f"voto_r{rodada}"] = escolha
                        d[f"tempo_voto_r{rodada}"] = time.time()
                        salvar_estado(estado)
                        st.rerun()
                else:
                    st.success(f"📌 Estratégia Adotada: {get_labels(rodada)[voto_atual]}")
                    exibir_dre({f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada+1)}, rodada)

                    if estado.get(f"apurado_r{rodada}", False):
                        st.info(f"📢 Resultado da Apuração — Exercício {rodada}")

            with aba_jornal:
                if estado["historico_noticias"]:
                    for n_html in estado["historico_noticias"]:
                        st.markdown(n_html, unsafe_allow_html=True)
                else:
                    st.info("⏳ Nenhuma notícia publicada neste ciclo.")

        else:
            st.error("❌ Senha incorreta. Tente novamente.")

    # 🔁 Auto redirect para Mídia
    _fase = estado.get("fase_final")
    if _fase in ("plantao", "veredicto") and st.session_state.get("pagina_atual") != "📰 Mídia (Notícias)":
        st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
        st.rerun()

    # 🔁 Auto-refresh
    time.sleep(6)
    st.rerun()

    st.rerun()
