mport streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import time
import json
import os
import fcntl

# Configuração da página - DEVE ser a primeira linha de comando Streamlit
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Simulador de Governança")

# ─────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO DO SESSION STATE (Crucial para navegação e memória de origem)
# ─────────────────────────────────────────────────────────────────────────────
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "🏠 Início"

if "origem_usuario" not in st.session_state:
    st.session_state["origem_usuario"] = "🏠 Início"

if "gerenciador_autenticado" not in st.session_state:
    st.session_state["gerenciador_autenticado"] = False

# Estilo CSS original + melhorias para botões
st.markdown("""
<style>
[data-testid="collapsedControl"] { display: none; }
.stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

STATE_FILE = os.path.join(os.path.dirname(__file__), "game_state.json")
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]
SENHA_GERENCIADOR = "G10"

EMPRESA_MAP = {
    "α - Empresa Alfa": "Empresa Alfa",
    "β - Empresa Beta": "Empresa Beta",
    "γ - Empresa Gama": "Empresa Gama",
}

SENHAS_EMPRESAS = {
    "Empresa Alfa": "ALFA10",
    "Empresa Beta": "BETA20",
    "Empresa Gama": "GAMA30",
}

# ─────────────────────────────────────────────────────────────────────────────
# ESTADO INICIAL (Original)
# ─────────────────────────────────────────────────────────────────────────────
def _estado_inicial() -> dict:
    return {
        "rodada_atual": 1,
        "historico_noticias": [],
        "historico_noticias_plantao": [],
        "historico_noticias_veredicto": [],
        "sessoes_ativas": [],
        "fase_final": None,
        "ts_suspense": None,
        "dados_empresas": {
            nome: {
                "precos": [20.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None,
                "tempo_voto_r1": None, "tempo_voto_r2": None, "tempo_voto_r3": None,
                "status": "Operando",
                "noticia_r4": "",
                "score_gr": 0,
            }
            for nome in EMPRESAS
        },
    }

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
        if "sessoes_ativas" not in estado: estado["sessoes_ativas"] = []
        if "historico_noticias_plantao" not in estado: estado["historico_noticias_plantao"] = []
        if "historico_noticias_veredicto" not in estado: estado["historico_noticias_veredicto"] = []
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

# ─────────────────────────────────────────────────────────────────────────────
# IMPACTOS / LABELS (Originais)
# ─────────────────────────────────────────────────────────────────────────────
IMPACTOS = {
    1: {"A": 0.75, "B": 0.95, "C": 1.05},
    2: {"A": 0.40, "B": 0.82, "C": 1.143},
    3: {"A": 0.30, "B": 0.60, "C": 1.10},
}

LABELS_R1 = {
    "A": """Opção A — Lançar em Passivo Financeiro\n\nReclassifica a operação para dívida bancária assim que o banco assume o pagamento do fornecedor.\n\nResultado: O EBITDA fica estável em R$ 1.000M, o Resultado Financeiro absorve os juros (-R$ 310M) e o Lucro Líquido cai para R$ 690M, aceitando o estouro técnico do covenant.""",
    "B": """Opção B — Lançar em Passivo Operacional\n\nMantém o registro da operação na conta de fornecedores comerciais.\n\nResultado: O EBITDA fica estável em R$ 1.000M, o Resultado Financeiro absorve os juros (-R$ 310M) e o Lucro Líquido cai para R$ 690M, salvando o covenant de dívida financeira por manter o saldo fora do passivo financeiro.""",
    "C": """Opção C — Lançar em Passivo Financeiro com Ajuste de Provisão\n\nRegistra o risco sacado no Passivo Financeiro, mas a diretoria revisa e reduz a Provisão para Calotes (PDD) de -R$ 150M para -R$ 100M.\n\nResultado: O EBITDA sobe para R$ 1.050M por conta do ganho operacional na PDD, amortecendo os juros no Resultado Financeiro (-R$ 310M). O Lucro Líquido sobe para R$ 740M e o covenant de alavancagem é mitigado pelo aumento do denominador (EBITDA maior).""",
}

LABELS_R2 = {
    "A": """Opção A — Assumir a Perda Cambial Imediata\n\nReconhece o impacto cambial direto na DRE e a desvalorização via provisão de estoque.\n\nResultado: O EBITDA é fortemente penalizado pelo ajuste de obsolescência, o Resultado Financeiro absorve a perda cambial, o Lucro Líquido despenca e os covenants contratuais correm alto risco de quebra imediata.""",
    "B": """Opção B — Dilatar Ativos e Depreciação (CPC 16/23)\n\nAtiva custos extras (como multas de demurrage) no valor do estoque e alonga o prazo de vida útil dos ativos logísticos de 5 para 10 anos.\n\nResultado: O EBITDA é poupado do impacto imediato, pois os custos adicionais ficam retidos no Ativo Circulante e a linha de depreciação encolhe, blindando temporariamente os indicadores e os covenants.""",
    "C": """Opção C — Crédito de Incentivo Comercial / Rebate\n\nRegistra descontos e incentivos verbais futuros de 24 meses acordados com os fabricantes internacionais como receita imediata no exercício corrente.\n\nResultado: A linha de receita recebe uma injeção artificial de R$ 80M, inflando diretamente o Lucro Bruto e fazendo o EBITDA saltar, camuflando a crise do dólar perante auditorias e bancos credores.""",
}

LABELS_R3 = {
    "A": """Opção A — Registrar Provisão (PECLD)\n\nReconhece imediatamente a inadimplência de 12% sobre a carteira de recebíveis, lançando a provisão na DRE.\n\nResultado: O EBITDA é reduzido proporcionalmente ao valor da provisão calculada (% × recebíveis). Demonstra transparência, mas expõe a fragilidade da empresa e ameaça covenants.""",
    "B": """Opção B — Securitização via FIDC\n\nTransfere parte dos recebíveis para um fundo, recebendo liquidez imediata em troca de juros e taxas.\n\nResultado: O EBITDA é preservado, mas há um custo financeiro (ex.: ~10% do valor securitizado). Os covenants permanecem intactos, mas a empresa aumenta sua dependência de engenharia financeira.""",
    "C": """Opção C — Diferimento Técnico da Perda\n\nAdia o reconhecimento da inadimplência, registrando apenas uma parcela mínima e mantendo a maior parte como receita futura.\n\nResultado: A linha de receita é inflada artificialmente (+% sobre recebíveis), o EBITDA sobe e os covenants são preservados. Contudo, configura maquiagem contábil e eleva o risco de fraude.""",
}

def get_labels(rodada: int) -> dict:
    if rodada == 1: return LABELS_R1
    if rodada == 2: return LABELS_R2
    if rodada == 3: return LABELS_R3
    return LABELS_R1

# ─────────────────────────────────────────────────────────────────────────────
# NARRATIVAS (Originais)
# ─────────────────────────────────────────────────────────────────────────────
def narrativa_rodada_1() -> str:
    return """### 📰 RODADA 1: O RISCO SACADO\n\n**Cenário:** A companhia enfrenta pressão dos bancos e precisa decidir como registrar o risco sacado.\nO mercado observa atentamente se a empresa vai assumir como dívida financeira ou maquiar como fornecedor.\n\n**Sua missão:** Definir o tratamento contábil para o risco sacado e proteger os covenants da empresa.\n"""

def narrativa_rodada_2(cmv_base: float, impacto_cambio: float) -> str:
    cmv_fmt = f"R$ {abs(cmv_base)/1_000_000:.0f}M".replace(",", ".")
    impacto_fmt = f"R$ {impacto_cambio/1_000_000:.0f}M".replace(",", ".")
    return f"""### 📰 RODADA 2: A CRISE DO DÓLAR E OS CONTRATOS DE IMPORTAÇÃO\n\n**Cenário:** A companhia enfrenta uma severa crise de margem operacional. A ausência de proteção cambial expôs a operação diretamente à volatilidade internacional.\n\n*   **Estouro no Custo de Aquisição (CMV):** O custo de importação subiu para {cmv_fmt}, impacto de **-{impacto_fmt}**.\n*   **Problema Logístico:** A retenção fiscal na alfândega gerou multas de armazenagem.\n*   **Vendas Travadas:** O repasse dos custos paralisou as vendas e encalhou o estoque.\n\n**Sua missão:** Definir a manobra orçamentária para mitigar os efeitos da crise cambial.\n"""

def narrativa_rodada_3() -> str:
    return """### 📰 RODADA 3: A CRISE DOS RECEBÍVEIS\n\n**Cenário:** A inadimplência disparou e a empresa precisa decidir como tratar os recebíveis.\nO mercado aguarda se haverá reconhecimento imediato, securitização ou diferimento técnico.\n\n**Sua missão:** Escolher a estratégia para lidar com a inadimplência e preservar os indicadores financeiros.\n"""

# ─────────────────────────────────────────────────────────────────────────────
# DRE (Original)
# ─────────────────────────────────────────────────────────────────────────────
def calcular_dre_dinamico(votos: dict) -> dict:
    receita     = 20_000_000_000.0
    cmv         = -16_500_000_000.0
    pdd         = -150_000_000.0
    depreciacao = -150_000_000.0
    outras_desp = -2_200_000_000.0
    juros       = -300_000_000.0
    score_gr    = 0
    v1 = votos.get("r1")
    if v1 == "A": juros = -310_000_000.0
    elif v1 == "B": outras_desp -= 200_000_000.0; score_gr += 2
    elif v1 == "C": pdd = -100_000_000.0; score_gr += 3
    v2 = votos.get("r2")
    if v2 == "A": cmv -= 30_000_000.0
    elif v2 == "B": depreciacao += 20_000_000.0; score_gr += 2
    elif v2 == "C": pdd -= 50_000_000.0; score_gr += 3
    v3 = votos.get("r3")
    pecld = receita * 0.30 * 0.12
    if v3 == "A": pdd -= pecld
    elif v3 == "B": juros -= pecld; score_gr += 2
    elif v3 == "C": receita += pecld; score_gr += 3
    lb = receita + cmv
    eb = lb + pdd + outras_desp
    ll = eb + depreciacao + juros
    return {"receita": receita, "cmv": cmv, "lucro_bruto": lb, "pdd": pdd, "depreciacao": depreciacao, "outras_desp": outras_desp, "ebitda": eb, "juros": juros, "lucro_liq": ll, "score_gr": score_gr}

def exibir_dre(votos_empresa: dict, rodada_exibida: int, mostrar_score: bool = False):
    dre = calcular_dre_dinamico(votos_empresa)
    st.markdown(f"### 📋 DRE Acumulada — Exercício {rodada_exibida}")
    fmt = lambda v, n=False: f"{'-' if n else ''}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    linhas = [("(=) Receita Bruta de Vendas", fmt(dre["receita"]), False), ("(-) Custo das Mercadorias (CMV)", fmt(dre["cmv"], True), False), ("(=) Lucro Bruto Operacional", fmt(dre["lucro_bruto"]), True), ("(-) Provisão para Calotes (PDD/PECLD)", fmt(dre["pdd"], True), False), ("(-) Depreciação de Lojas/Ativos", fmt(dre["depreciacao"], True), False), ("(-) Outras Despesas Operacionais", fmt(dre["outras_desp"], True), False), ("(=) EBITDA APURADO", fmt(dre["ebitda"]), True), ("(-) Result. Financeiro (Dívidas/Juros)", fmt(dre["juros"], True), False), ("(=) LUCRO LÍQUIDO DO EXERCÍCIO", fmt(dre["lucro_liq"]), True)]
    rows = "".join([f"<tr style='{'background:#1e3a5f;color:#fff;font-weight:bold;' if d else 'color:#e0e0e0;'}{'border-top:2px solid #555;' if i in {2,6,7,8} else ''}'><td style='padding:6px 10px;font-family:monospace;'>{c}</td><td style='padding:6px 10px;font-family:monospace;text-align:right;'>{v}</td></tr>" for i, (c, v, d) in enumerate(linhas)])
    st.markdown(f"<table style='width:100%;border-collapse:collapse;'>{rows}</table><br>", unsafe_allow_html=True)
    if mostrar_score: st.markdown(f"**Score Ético/Discricionário acumulado:** {dre['score_gr']}")

# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DE PREÇOS (Original + Correção Centavos)
# ─────────────────────────────────────────────────────────────────────────────
def calcular_novo_preco(estado: dict, empresa_nome: str, rodada: int) -> float:
    d = estado["dados_empresas"][empresa_nome]
    preco = d["precos"][-1]
    voto = d.get(f"voto_r{rodada}")
    if voto is None: return preco
    preco *= IMPACTOS.get(rodada, {}).get(voto, 1.0)
    tempos = [(n, estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}")) for n in EMPRESAS if estado["dados_empresas"][n].get(f"voto_r{rodada}") and estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}")]
    if len(tempos) == 3:
        ranking = [item[0] for item in sorted(tempos, key=lambda x: x[1])]
        if ranking[0] == empresa_nome: preco += 0.10; d[f"bonus_velocidade_r{rodada}"] = "primeiro"
        elif ranking[-1] == empresa_nome: preco -= 0.10; d[f"bonus_velocidade_r{rodada}"] = "ultimo"
        else: d[f"bonus_velocidade_r{rodada}"] = "meio"
    votos_emp = {f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada + 1)}
    if calcular_dre_dinamico(votos_emp)["score_gr"] >= 6: preco *= 0.95
    return round(preco, 2)

def processar_rodada_4_consolidada(estado: dict, empresa_nome: str) -> float:
    d = estado["dados_empresas"][empresa_nome]
    if len(d["precos"]) >= 5: return d["precos"][-1]
    r1, r2, r3 = d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")
    qc, qb = [r1, r2, r3].count("C"), [r1, r2, r3].count("B")
    if qc == 3: pct = 0.70
    elif qc == 2: pct = 0.50
    elif qc == 1 and qb >= 1: pct = 0.45
    elif qc == 1: pct = 0.40
    elif qb >= 2: pct = 0.15
    elif qb == 1: pct = 0.05
    else: pct = 0.0
    np = round(d["precos"][-1] * (1.0 - pct), 2)
    d["precos"].append(np)
    return np

# ─────────────────────────────────────────────────────────────────────────────
# CARTAS E MANCHETES (Originais)
# ─────────────────────────────────────────────────────────────────────────────
def gerar_carta_destino(nome: str, r1, r2, r3) -> str:
    qc, qb = [r1, r2, r3].count("C"), [r1, r2, r3].count("B")
    if qc == 3: m, t, c, i = f"⛓️ OPERAÇÃO EXCEL CRIATIVO — PRISÃO DOS EXECUTIVOS DA {nome.upper()}!", "Após três exercícios consecutivos de criatividade contábil, a Operação 'Excel Criativo' foi deflagrada pela CVM e pela Polícia Federal 🚔.\n\nCEO e CFO foram afastados e conduzidos para prestar esclarecimentos e seguem em prisão preventiva ⛓️👮.\n☠️💀 GAME OVER 💀☠️", "#b71c1c", "⛓️"
    elif qc == 2: m, t, c, i = f"💰🚫 JUSTIÇA BLOQUEIA BENS DA {nome.upper()}!", "A investigação da CVM identificou graves falhas de governança na {nome}. 🚨\nA Justiça determinou o bloqueio cautelar dos bens dos ex-executivos 💰⚖️.\n📉🔥 GAME OVER 🔥📉", "#c62828", "💰"
    elif qc == 1 and qb >= 1: m, t, c, i = f"💸🚪 CEO E CFO DA {nome.upper()} VIRAM EX-FUNCIONÁRIOS", "A combinação entre ajustes por 'erro' e gerenciamento de resultados por accruals discricionários finalmente chegou à conta. 💸\nApós pressão dos investidores, o Conselho decidiu substituir CEO e CFO 🚪👔.\n📉💼 GAME OVER 💼📉", "#e65100", "💸"
    elif qc == 1: m, t, c, i = f"🥲 {nome.upper()} — FRAUDE PONTUAL, MAS A CONTA CHEGOU", "A irregularidade foi considerada pontual, mas suficiente para destruir a confiança dos investidores. 📉\nO CEO foi convidado a perseguir novos desafios profissionais 💼.\n📋 GAME OVER 📋", "#f57f17", "🥲"
    elif qb >= 2: m, t, c, i = f"📉 {nome.upper()} — O MESTRE DO PÔQUER CONTÁBIL", "Sem identificar fraude, a CVM concluiu que a {nome} apenas exagerou na criatividade. 🎰\nO CFO ganhou o apelido de 'Mestre do Pôquer Contábil' ♠️.\n🎲 GAME OVER 🎲", "#1565c0", "📉"
    elif qb == 1: m, t, c, i = f"ℹ️ {nome.upper()} — EPISÓDIO ISOLADO, VIGILÂNCIA REDOBRADA", "A investigação concluiu que houve apenas um episódio isolado de gerenciamento de resultados por accruals discricionários. 📚\nCEO e CFO permaneceram nos cargos 👔.\n😮‍💨 GAME OVER 😮‍💨", "#2e7d32", "ℹ️"
    else: m, t, c, i = f"💼☠️ {nome.upper()} MORREU ABRAÇADA COM A ÉTICA", "A diretoria escolheu reconhecer todas as perdas e respeitar rigorosamente os CPCs. 📚\nOs auditores aplaudiram 👏. Os investidores venderam 📉.\n💼☠️ GAME OVER ☠️💼", "#4a148c", "☠️"
    th = t.replace("\n\n", "</p><p style='margin:8px 0;'>").replace("\n", "<br>")
    return f"""<div style="background:linear-gradient(135deg,{c}dd,{c}88);border:3px solid {c};border-radius:16px;padding:28px 32px;margin:20px 0;box-shadow:0 6px 24px rgba(0,0,0,0.4);font-family:Arial;"><div style="font-size:48px;text-align:center;margin-bottom:12px;">{i}</div><div style="background:rgba(0,0,0,0.35);color:#fff;font-size:18px;font-weight:900;text-transform:uppercase;padding:12px 16px;border-radius:8px;text-align:center;margin-bottom:16px;">{m}</div><div style="background:rgba(255,255,255,0.12);border-radius:10px;padding:16px 20px;color:#fff;font-size:14px;line-height:1.7;white-space:pre-line;"><p style='margin:8px 0;'>{th}</p></div></div>"""

def gerar_manchete_dinamica(estado: dict, rodada_encerrada: int) -> str:
    df = {n: {"a": estado["dados_empresas"][n]["precos"][-1], "ant": estado["dados_empresas"][n]["precos"][-2] if len(estado["dados_empresas"][n]["precos"])>1 else 20.0} for n in EMPRESAS}
    for n in EMPRESAS: df[n]["v"] = df[n]["a"] - df[n]["ant"]
    lo = sorted(df.items(), key=lambda x: x[1]["a"], reverse=True)
    ln, ld, lnn, lnd = lo[0][0], lo[0][1], lo[-1][0], lo[-1][1]
    fv = lambda v: f"{'+' if v>=0 else '-'}R$ {abs(v):.2f}"
    sb = f"""<div style="background-color:#c62828;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;">{lnn} despenca {fv(lnd['v'])}</div><div style="margin-top:6px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;"><p style="font-size:13px;color:#333;margin:0;">SÃO PAULO — A {lnn} caiu para R$ {lnd['a']:.2f}.</p></div>""" if ld["a"] != lnd["a"] else ""
    return f"""<div style="background-color:#fff;border:1px solid #ddd;font-family:Arial;max-width:600px;margin:0 auto 20px auto;box-shadow:0 4px 10px rgba(0,0,0,0.15);border-radius:4px;overflow:hidden;"><div style="background-color:#cc0000;color:#fff;display:flex;justify-content:space-between;padding:12px 20px;"><div style="font-size:24px;font-weight:900;">GC NEWS</div><div style="font-size:12px;font-weight:bold;background:rgba(0,0,0,0.2);padding:4px 8px;border-radius:4px;">EXERCÍCIO {rodada_encerrada}</div></div><div style="padding:20px 15px;"><div style="background-color:#2e7d32;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;">{ln} dispara {fv(ld['v'])}!</div><div style="margin-top:6px;margin-bottom:20px;border-left:4px solid #2e7d32;padding:8px 12px;background-color:#f1f8e9;"><p style="font-size:13px;color:#333;margin:0;">SÃO PAULO — A {ln} subiu de R$ {ld['ant']:.2f} para R$ {ld['a']:.2f}.</p></div>{sb}</div></div>"""

def gerar_manchete_veredicto(estado: dict) -> str:
    me = []
    for n in EMPRESAS:
        d = estado["dados_empresas"][n]
        r1, r2, r3 = d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")
        qc, qb, pf = [r1, r2, r3].count("C"), [r1, r2, r3].count("B"), d["precos"][-1]
        if qc == 3: m, t = f"⛓️ PRISÃO DOS EXECUTIVOS DA {n.upper()}!", f"A CVM e a Polícia Federal deflagraram a Operação Excel Criativo 🚔. CEO e CFO presos preventivamente. Preço: R$ {pf:.2f}."
        elif qc == 2: m, t = f"💰🚫 JUSTIÇA BLOQUEIA BENS DA {n.upper()}!", f"Bloqueio cautelar dos bens dos ex-executivos 💰⚖️. Preço final: R$ {pf:.2f}."
        elif qc == 1 and qb >= 1: m, t = f"💸 {n.upper()} MULTADA! 🚪 CEO E CFO EX-FUNCIONÁRIOS", f"Demissão de CEO e CFO 🚪👔. + multa milionária 💸 Preço final: R$ {pf:.2f}."
        elif qc == 1: m, t = f"🥲 {n.upper()} — FRAUDE PONTUAL", f"Irregularidade considerada pontual, CEO convidado a 'buscar novos desafios' 💼. Preço: R$ {pf:.2f}."
        elif qb >= 2: m, t = f"📉 {n.upper()} — MESTRE DO PÔQUER CONTÁBIL", f"Accruals discricionários excessivos colocam o CFO sob monitoramento 👀♠️. Preço: R$ {pf:.2f}."
        elif qb == 1: m, t = f"ℹ️ {n.upper()} — EPISÓDIO ISOLADO", f"Um episódio isolado de accruals discricionários. Preço final: R$ {pf:.2f}."
        else: m, t = f"☠️ {n.upper()} MORREU ABRAÇADA COM A ÉTICA", f"Transparência total, mercado não perdoou as perdas reconhecidas 🩸 Preço: R$ {pf:.2f}."
        me.append(f"""<div style="background-color:#c62828;color:#fff;padding:12px 15px;border-radius:2px;font-size:14px;font-weight:bold;text-transform:uppercase;margin-top:10px;">{m}</div><div style="margin-top:4px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;"><p style="font-size:13px;color:#333;margin:0;">{t}</p></div>""")
    return f"""<div style="background-color:#fff;border:1px solid #ddd;font-family:Arial;max-width:600px;margin:0 auto 20px auto;box-shadow:0 4px 10px rgba(0,0,0,0.15);border-radius:4px;overflow:hidden;"><div style="background-color:#1a1a1a;color:#fff;display:flex;justify-content:space-between;padding:12px 20px;"><div style="font-size:24px;font-weight:900;">GC NEWS</div><div style="font-size:12px;font-weight:bold;background:rgba(0,0,0,0.3);padding:4px 8px;border-radius:4px;">🏁 VEREDICTO FINAL</div></div><div style="padding:20px 15px;"><div style="background-color:#2e7d32;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;">🏁 CVM DIVULGA VEREDITO FINAL</div><div style="margin-top:6px;margin-bottom:12px;border-left:4px solid #2e7d32;padding:8px 12px;background-color:#f1f8e9;"><p style="font-size:13px;color:#333;margin:0;">SÃO PAULO — Auditoria concluída. Resultados individuais divulgados.</p></div>{"".join(me)}</div></div>"""

# ─────────────────────────────────────────────────────────────────────────────
# NAVEGAÇÃO E BARRA SUPERIOR (Correção de Travamento e Memória)
# ─────────────────────────────────────────────────────────────────────────────
def barra_navegacao():
    if st.session_state["pagina_atual"] != "🏠 Início":
        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
        with c1:
            if st.button("📋 Rodada", key="nav_rodada"):
                st.session_state["pagina_atual"] = st.session_state["origem_usuario"]
                st.rerun()
        with c2:
            if st.button("📈 Telão", key="nav_telao"):
                st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
                st.rerun()
        with c3:
            if st.button("📰 Mídia", key="nav_midia"):
                st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
                st.rerun()
        st.divider()

perfis_nav = ["🏠 Início", "🎛️ Painel Gerenciador", "📈 Telão (Bolsa)", "📰 Mídia (Notícias)", "α - Empresa Alfa", "β - Empresa Beta", "γ - Empresa Gama"]
def on_nav_change():
    st.session_state["pagina_atual"] = st.session_state["nav_sb"]
    if st.session_state["nav_sb"] in ["🎛️ Painel Gerenciador", "α - Empresa Alfa", "β - Empresa Beta", "γ - Empresa Gama"]:
        st.session_state["origem_usuario"] = st.session_state["nav_sb"]

st.sidebar.selectbox("Navegação:", perfis_nav, 
                    index=perfis_nav.index(st.session_state["pagina_atual"]) if st.session_state["pagina_atual"] in perfis_nav else 0,
                    key="nav_sb", on_change=on_nav_change)

perfil = st.session_state["pagina_atual"]

# ─────────────────────────────────────────────────────────────────────────────
# TELAS (Originalmente reconstruídas)
# ─────────────────────────────────────────────────────────────────────────────
if perfil == "🏠 Início":
    estado = carregar_estado()
    st.title("🔒 Simulador de Governança")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.subheader("🎛️ Gerenciador")
            senha_g = st.text_input("Senha:", type="password", key="s_g_ini")
            if st.button("Acessar Painel", type="primary", key="btn_g_ini"):
                if senha_g == SENHA_GERENCIADOR:
                    st.session_state["gerenciador_autenticado"] = True
                    st.session_state["origem_usuario"] = "🎛️ Painel Gerenciador"
                    st.session_state["pagina_atual"] = "🎛️ Painel Gerenciador"
                    st.rerun()
                else: st.error("Senha incorreta")
    with c2:
        with st.container(border=True):
            st.subheader("🏢 Empresas")
            emp_sel = st.selectbox("Empresa:", list(EMPRESA_MAP.keys()), key="sel_emp_ini")
            if st.button("Entrar na Bancada", type="primary", key="btn_emp_ini"):
                st.session_state["origem_usuario"] = emp_sel
                st.session_state["pagina_atual"] = emp_sel
                st.rerun()
    with c3:
        with st.container(border=True):
            st.subheader("📈 Telão")
            if st.button("Abrir Projeção", type="primary", key="btn_t_ini"):
                st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
                st.rerun()

elif perfil == "🎛️ Painel Gerenciador":
    if not st.session_state.get("gerenciador_autenticado"): st.warning("Login necessário"); st.stop()
    barra_navegacao()
    estado = carregar_estado(); rodada = estado["rodada_atual"]
    st.title(f"🎛️ Painel Gerenciador - Rodada {rodada}")
    
    # TIMER (Correção: Para ao apurar)
    ct, ak = f"timer_r{rodada}", f"ap_r{rodada}"
    if not estado.get(ct):
        if st.button("⏱️ Iniciar Timer"): estado[ct] = time.time(); salvar_estado(estado); st.rerun()
    else:
        if estado.get(ak): st.success("✅ Rodada Apurada - Timer Encerrado")
        else:
            r = max(0, int(600 - (time.time() - estado[ct])))
            st.subheader(f"⏳ Tempo: {r//60:02d}:{r%60:02d}")
            if st.button("🔄 Atualizar Tempo"): st.rerun()

    st.divider()
    cols = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        v = estado["dados_empresas"][emp].get(f"voto_r{rodada}")
        cols[i].metric(emp, "✅ Votou" if v else "⏳ Aguardando")
    
    if st.button("📊 APURAR RESULTADOS", type="primary", disabled=estado.get(ak, False)):
        for emp in EMPRESAS: estado["dados_empresas"][emp]["precos"].append(calcular_novo_preco(estado, emp, rodada))
        estado["historico_noticias"].append(gerar_manchete_dinamica(estado, rodada))
        estado[ak] = True; salvar_estado(estado); st.rerun()
        
    if st.button("▶️ Próxima Rodada", disabled=not estado.get(ak)):
        if rodada < 3: estado["rodada_atual"] += 1; salvar_estado(estado); st.rerun()
        elif rodada == 3: # RODADA 4 LÓGICA ORIGINAL
            estado["rodada_atual"] = 4; salvar_estado(estado); st.rerun()

    # RODADA 4 LÓGICA ORIGINAL RESTAURADA
    if rodada == 4:
        st.subheader("🚨 Auditoria Final CVM")
        if not estado.get("hp_r4"):
            if st.button("🔎 Disparar Plantão CVM"):
                estado["historico_noticias_plantao"].append("Plantão CVM disparado!")
                estado["hp_r4"] = True; salvar_estado(estado); st.rerun()
        if not estado.get("ap_r4"):
            if st.button("🏁 Conferir Apuração Final"):
                for e in EMPRESAS: processar_rodada_4_consolidada(estado, e)
                estado["historico_noticias_veredicto"].append(gerar_manchete_veredicto(estado))
                estado["ap_r4"] = True; salvar_estado(estado); st.rerun()

    if st.button("♻️ Resetar Simulação"): resetar_estado(); st.session_state["pagina_atual"]="🏠 Início"; st.rerun()

elif perfil == "📈 Telão (Bolsa)":
    barra_navegacao(); estado = carregar_estado(); st.title("📈 Telão Comercial")
    matplotlib.use("Agg")
    fig, ax = plt.subplots(); fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#1e222b')
    for i, emp in enumerate(EMPRESAS): ax.plot(estado["dados_empresas"][emp]["precos"], label=emp, marker='o')
    ax.legend(); st.pyplot(fig); time.sleep(5); st.rerun()

elif perfil == "📰 Mídia (Notícias)":
    barra_navegacao(); estado = carregar_estado(); st.title("📰 Central de Notícias")
    if estado.get("historico_noticias_veredicto"):
        for h in reversed(estado["historico_noticias_veredicto"]): st.markdown(h, unsafe_allow_html=True)
    for h in reversed(estado.get("historico_noticias", [])): st.markdown(h, unsafe_allow_html=True)
    time.sleep(10); st.rerun()

elif perfil in EMPRESA_MAP:
    nome_emp = EMPRESA_MAP[perfil]
    if not st.session_state.get(f"auth_{nome_emp}"):
        st.title(f"🏢 {perfil}")
        senha = st.text_input("Senha:", type="password", key=f"p_{nome_emp}")
        if st.button("Entrar", key=f"b_{nome_emp}"):
            if senha == SENHAS_EMPRESAS[nome_emp]: st.session_state[f"auth_{nome_emp}"] = True; st.rerun()
        st.stop()
    
    barra_navegacao()
    estado = carregar_estado(); rodada = estado["rodada_atual"]; d = estado["dados_empresas"][nome_emp]
    
    if rodada <= 3:
        if rodada == 1: st.markdown(narrativa_rodada_1())
        elif rodada == 2: st.markdown(narrativa_rodada_2(-16.5e9, -300e6))
        elif rodada == 3: st.markdown(narrativa_rodada_3())
        
        v = d.get(f"voto_r{rodada}")
        if v:
            st.success(f"Estratégia: Opção {v}")
            # CENTAVOS (Correção: Aparece logo após o voto)
            bv = d.get(f"bonus_velocidade_r{rodada}")
            if bv == "primeiro": st.info("🚀 BÔNUS VELOCIDADE: +R$ 0,10")
            elif bv == "ultimo": st.warning("🐢 PENALIDADE VELOCIDADE: -R$ 0,10")
            if estado.get(f"ap_r{rodada}"): exibir_dre({f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada+1)}, rodada)
        else:
            escolha = st.radio("Selecione sua opção:", ["A", "B", "C"], format_func=lambda x: get_labels(rodada)[x])
            if st.button("Confirmar Decisão", type="primary"):
                d[f"voto_r{rodada}"] = escolha; d[f"tempo_voto_r{rodada}"] = time.time()
                salvar_estado(estado); st.rerun()
    else: # RODADA 4 EMPRESA ORIGINAL
        if estado.get("ap_r4"):
            st.markdown(gerar_carta_destino(nome_emp, d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")), unsafe_allow_html=True)
        else: st.info("Aguardando Auditoria Final CVM...")

    st.divider(); st.line_chart(d["precos"]); time.sleep(8); st.rerun()
