import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import time
import json
import os
import fcntl

st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

if "rodada" not in st.session_state:
    st.session_state["rodada"] = 1

# Página atual do sistema
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "🏠 Início"

st.markdown("""
<style>
[data-testid="collapsedControl"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

STATE_FILE = os.path.join(os.path.dirname(__file__), "game_state.json")

EMPRESAS = [
    "Empresa Alfa",
    "Empresa Beta",
    "Empresa Gama"
]

SENHA_GERENCIADOR = "G10"

EMPRESA_MAP = {
    "α - Empresa Alfa": "Empresa Alfa",
    "β - Empresa Beta": "Empresa Beta",
    "γ - Empresa Gama": "Empresa Gama",
}


# ─────────────────────────────────────────────────────────────────────────────
# ESTADO INICIAL
# ─────────────────────────────────────────────────────────────────────────────
def _estado_inicial() -> dict:
    return {
        "rodada_atual": 1,
        "historico_noticias": [],
        "historico_noticias_plantao": [],   # notícias do plantão CVM (fase 1 da R4)
        "historico_noticias_veredicto": [], # notícias do veredicto (fase 2 da R4)
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
        if "sessoes_ativas" not in estado:
            estado["sessoes_ativas"] = []
        if "historico_noticias_plantao" not in estado:
            estado["historico_noticias_plantao"] = []
        if "historico_noticias_veredicto" not in estado:
            estado["historico_noticias_veredicto"] = []
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
# IMPACTOS / LABELS
# ─────────────────────────────────────────────────────────────────────────────
IMPACTOS = {
    1: {"A": 0.75, "B": 0.95, "C": 1.05},
    2: {"A": 0.40, "B": 0.82, "C": 1.143},
    3: {"A": 0.30, "B": 0.60, "C": 1.10},
}

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

def get_labels(rodada: int) -> dict:
    if rodada == 1: return LABELS_R1
    if rodada == 2: return LABELS_R2
    if rodada == 3: return LABELS_R3
    return LABELS_R1

# ─────────────────────────────────────────────────────────────────────────────
# NARRATIVAS
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# DRE
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
    if v1 == "A":
        juros = -310_000_000.0
    elif v1 == "B":
        outras_desp -= 200_000_000.0
        score_gr += 2
    elif v1 == "C":
        pdd = -100_000_000.0
        score_gr += 3

    v2 = votos.get("r2")
    if v2 == "A":
        cmv -= 30_000_000.0
    elif v2 == "B":
        depreciacao += 20_000_000.0
        score_gr += 2
    elif v2 == "C":
        pdd -= 50_000_000.0
        score_gr += 3

    v3 = votos.get("r3")
    carteira_recebiveis = receita * 0.30
    pecld_dinamica = carteira_recebiveis * 0.12

    if v3 == "A":
        pdd -= pecld_dinamica
    elif v3 == "B":
        juros -= pecld_dinamica
        score_gr += 2
    elif v3 == "C":
        receita += pecld_dinamica
        score_gr += 3

    lucro_bruto = receita + cmv
    ebitda      = lucro_bruto + pdd + outras_desp
    lucro_liq   = ebitda + depreciacao + juros

    return {
        "receita": receita, "cmv": cmv, "lucro_bruto": lucro_bruto,
        "pdd": pdd, "depreciacao": depreciacao, "outras_desp": outras_desp,
        "ebitda": ebitda, "juros": juros, "lucro_liq": lucro_liq,
        "pecld_dinamica": pecld_dinamica, "score_gr": score_gr,
    }

def exibir_dre(votos_empresa: dict, rodada_exibida: int, mostrar_score: bool = False):
    """Exibe a DRE. mostrar_score=True apenas no Gerenciador."""
    dre = calcular_dre_dinamico(votos_empresa)
    st.markdown(f"### 📋 DRE Acumulada — Exercício {rodada_exibida}")

    def fmt(v, negativo=False):
        sinal = "-" if negativo else ""
        return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    linhas = [
        ("(=) Receita Bruta de Vendas",           fmt(dre["receita"]),            False),
        ("(-) Custo das Mercadorias (CMV)",        fmt(dre["cmv"],        True),   False),
        ("(=) Lucro Bruto Operacional",            fmt(dre["lucro_bruto"]),        True),
        ("(-) Provisão para Calotes (PDD/PECLD)",  fmt(dre["pdd"],        True),   False),
        ("(-) Depreciação de Lojas/Ativos",        fmt(dre["depreciacao"], True),  False),
        ("(-) Outras Despesas Operacionais",       fmt(dre["outras_desp"], True),  False),
        ("(=) EBITDA APURADO",                     fmt(dre["ebitda"]),             True),
        ("(-) Result. Financeiro (Dívidas/Juros)", fmt(dre["juros"],      True),   False),
        ("(=) LUCRO LÍQUIDO DO EXERCÍCIO",         fmt(dre["lucro_liq"]),          True),
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
    if mostrar_score:
        st.markdown(f"**Score Ético/Discricionário acumulado:** {dre['score_gr']}")

# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DE PREÇOS
# ─────────────────────────────────────────────────────────────────────────────
def calcular_novo_preco(estado: dict, empresa_nome: str, rodada: int) -> float:
    d         = estado["dados_empresas"][empresa_nome]
    preco_ant = d["precos"][-1]
    voto      = d.get(f"voto_r{rodada}")
    if voto is None:
        return preco_ant

    # 1) Aplica o multiplicador da rodada
    impacto = IMPACTOS.get(rodada, {}).get(voto, 1.0)
    novo    = preco_ant * impacto

   # 2) Ranking de velocidade (bônus/penalidade de tempo)
    tempos = [
        (n, estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}"))
        for n in EMPRESAS
        if n != empresa_nome
           and estado["dados_empresas"][n].get(f"voto_r{rodada}") is not None
           and estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}") is not None
    ]
    
    ordem_resposta = len(tempos)
    
    if ordem_resposta == 0:
        novo += 0.10
        d[f"bonus_velocidade_r{rodada}"] = "primeiro"
        d[f"msg_bonus_r{rodada}"] = (
            "🚀 Sua empresa foi a primeira a responder e recebeu um bônus de R$ 0,10 por ação. "
            "O mercado aprecia a agilidade."
        )
    
    elif ordem_resposta == 1:
        d[f"bonus_velocidade_r{rodada}"] = "meio"
        d[f"msg_bonus_r{rodada}"] = (
            "⏱️ Posicionamento no tempo médio. Sem bônus ou penalidade de velocidade.."
        )
    
    elif ordem_resposta == 2:
        novo -= 0.10
        d[f"bonus_velocidade_r{rodada}"] = "ultimo"
        d[f"msg_bonus_r{rodada}"] = (
            "🐢 Sua empresa foi a última a responder e sofreu uma redução de R$ 0,10 por ação. "
            "Tempo é dinheiro!"
        )
    # 3) Penalidade por score ético alto (>= 6)
    votos_emp = {f"r{r}": d.get(f"voto_r{r}") for r in range(1, 4)}
    score = calcular_dre_dinamico(votos_emp)["score_gr"]
    if score >= 6:
        novo *= 0.95

    return round(novo, 2)


def processar_rodada_4_consolidada(estado: dict, empresa_nome: str) -> float:
    d = estado["dados_empresas"][empresa_nome]
    if len(d["precos"]) >= 5:
        return d["precos"][-1]
    r1, r2, r3 = d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")
    qtd_c = [r1, r2, r3].count("C")
    qtd_b = [r1, r2, r3].count("B")
    if qtd_c == 3:              pct = 0.70
    elif qtd_c == 2:            pct = 0.50
    elif qtd_c == 1 and qtd_b >= 1: pct = 0.45
    elif qtd_c == 1:            pct = 0.40
    elif qtd_b >= 2:            pct = 0.15
    elif qtd_b == 1:            pct = 0.05
    else:                       pct = 0.0
    novo_preco = round(d["precos"][-1] * (1.0 - pct), 2)
    d["precos"].append(novo_preco)
    return novo_preco

# ─────────────────────────────────────────────────────────────────────────────
# CARTA DO DESTINO (Rodada 4 — exibida na página da empresa após apuração)
# ─────────────────────────────────────────────────────────────────────────────
def gerar_carta_destino(nome: str, r1, r2, r3) -> str:
    """Retorna HTML da carta de destino da empresa na Rodada 4."""
    qtd_c = [r1, r2, r3].count("C")
    qtd_b = [r1, r2, r3].count("B")

    if qtd_c == 3:
        manchete = f"⛓️ OPERAÇÃO EXCEL CRIATIVO — PRISÃO DOS EXECUTIVOS DA {nome.upper()}!"
        texto = (
            f"Após três exercícios consecutivos de criatividade contábil, a Operação 'Excel Criativo' "
            f"foi deflagrada pela CVM e pela Polícia Federal 🚔.\n\n"
            f"CEO e CFO foram afastados e conduzidos para prestar esclarecimentos e seguem em prisão preventiva ⛓️👮.\n"
            f"O Conselho alegou ter sido 'induzido ao erro' 🤷.\n"
            f"O Comitê de Auditoria entrou em reunião permanente ☕.\n"
            f"E o estagiário do financeiro afirmou que sempre achou estranho 🫠.\n\n"
            f"☠️💀 GAME OVER 💀☠️"
        )
        cor = "#b71c1c"
        icone = "⛓️"
    elif qtd_c == 2:
        manchete = f"💰🚫 JUSTIÇA BLOQUEIA BENS DA {nome.upper()}!"
        texto = (
            f"A investigação da CVM identificou graves falhas de governança na {nome}. 🚨\n\n"
            f"A Justiça determinou o bloqueio cautelar dos bens dos ex-executivos 💰⚖️.\n"
            f"CEO, CFO e Diretor de RI foram substituídos por cautela 🚪👔.\n"
            f"Os conselheiros declararam estar 'profundamente surpresos' 🤡,\n"
            f"embora tenham aprovado todas as apresentações dos últimos exercícios.\n\n"
            f"📉🔥 GAME OVER 🔥📉"
        )
        cor = "#c62828"
        icone = "💰"
    elif qtd_c == 1 and qtd_b >= 1:
        manchete = f"💸🚪 CEO E CFO DA {nome.upper()} VIRAM EX-FUNCIONÁRIOS"
        texto = (
            f"A combinação entre ajustes por accruals discrionários legais e ilegais— a famosa "
            f"'brechinha na lei' — finalmente chegou à conta. 💸\n\n"
            f"Após pressão dos investidores, o Conselho decidiu substituir CEO e CFO 🚪👔.\n"
            f"Ambos descobriram que EBITDA ajustado não cobre honorários advocatícios ⚖️.\n"
            f"O Comitê de Auditoria afirmou estar 'profundamente surpreso' 🤡.\n"
            f"Já os auditores responderam apenas: 'Nós avisamos'. 📚\n\n"
            f"O PowerPoint de Ética e Integridade foi atualizado pela quinta vez em três anos 📖.\n"
            f"E os dois executivos informaram em seus LinkedIns que estão 'abertos a novas oportunidades' 💼😂.\n\n"
            f"📉💼 GAME OVER 💼📉"
        )
        cor = "#e65100"
        icone = "💸"
    elif qtd_c == 1:
        manchete = f"🥲 {nome.upper()} — FRAUDE PONTUAL, MAS A CONTA CHEGOU"
        texto = (
            f"A irregularidade foi considerada pontual, mas suficiente para destruir a confiança dos investidores. 📉\n\n"
            f"O CEO foi convidado a perseguir novos desafios profissionais 💼.\n"
            f"O CFO permaneceu para explicar aos auditores o significado de 'ajuste temporário'. "
            f"O Excel aceitaria coisas que a CVM não aceitou 🤓.\n"
            f"Seu LinkedIn foi atualizado em tempo recorde. 💼😂\n\n"
            f"📋 GAME OVER 📋"
        )
        cor = "#f57f17"
        icone = "🥲"
    elif qtd_b >= 2:
        manchete = f"📉 {nome.upper()} — O MESTRE DO PÔQUER CONTÁBIL"
        texto = (
            f"Sem identificar fraude, a CVM concluiu que a {nome} apenas exagerou na criatividade. 🎰\n\n"
            f"O CFO ganhou o apelido de 'Mestre do Pôquer Contábil' ♠️.\n"
            f"Seu acesso ao Excel passou a ser monitorado por três auditores independentes 👀.\n"
            f"O CEO sobreviveu, mas envelheceu cinco anos em três exercícios 👴.\n\n"
            f"🎲 GAME OVER 🎲"
        )
        cor = "#1565c0"
        icone = "📉"
    elif qtd_b == 1:
        manchete = f"ℹ️ {nome.upper()} — EPISÓDIO ISOLADO, VIGILÂNCIA REDOBRADA"
        texto = (
            f"A investigação concluiu que houve apenas um episódio isolado de gerenciamento de resultados por accruals discrionários. 📚\n\n"
            f"CEO e CFO permaneceram nos cargos 👔.\n"
            f"Contudo, qualquer nova planilha aberta pelo financeiro agora é acompanhada por "
            f"auditoria, compliance e pelo estagiário desconfiado 👀😂.\n\n"
            f"😮‍💨 GAME OVER 😮‍💨"
        )
        cor = "#2e7d32"
        icone = "ℹ️"
    else:
        manchete = f"💼☠️ {nome.upper()} MORREU ABRAÇADA COM A ÉTICA"
        texto = (
            f"A diretoria escolheu reconhecer todas as perdas e respeitar rigorosamente os CPCs. 📚\n\n"
            f"Os auditores aplaudiram 👏.\n"
            f"Os investidores venderam 📉.\n"
            f"E os bônus desapareceram 💸.\n\n"
            f"Após a maior queda das ações da história recente, o Conselho decidiu substituir CEO e CFO 🚪👔.\n"
            f"Ambos atualizaram o LinkedIn 💼 e comunicaram estar 'abertos a novas oportunidades'. 😂\n\n"
            f"A reputação sobreviveu.\nO preço da ação, não. 📉\n\n"
            f"💼☠️ GAME OVER ☠️💼"
        )
        cor = "#4a148c"
        icone = "☠️"

    texto_html = texto.replace("\n\n", "</p><p style='margin:8px 0;'>").replace("\n", "<br>")

    return f"""
    <div style="
        background: linear-gradient(135deg, {cor}dd, {cor}88);
        border: 3px solid {cor};
        border-radius: 16px;
        padding: 28px 32px;
        margin: 20px 0;
        box-shadow: 0 6px 24px rgba(0,0,0,0.4);
        font-family: 'Arial', sans-serif;
    ">
        <div style="font-size:48px;text-align:center;margin-bottom:12px;">{icone}</div>
        <div style="
            background:rgba(0,0,0,0.35);
            color:#fff;
            font-size:18px;
            font-weight:900;
            text-transform:uppercase;
            letter-spacing:1px;
            padding:12px 16px;
            border-radius:8px;
            text-align:center;
            margin-bottom:16px;
        ">{manchete}</div>
        <div style="
            background:rgba(255,255,255,0.12);
            border-radius:10px;
            padding:16px 20px;
            color:#fff;
            font-size:14px;
            line-height:1.7;
            white-space:pre-line;
        "><p style='margin:8px 0;'>{texto_html}</p></div>
    </div>
    """

# ─────────────────────────────────────────────────────────────────────────────
# MANCHETES (rodadas 1-3 e plantão/veredicto R4)
# ─────────────────────────────────────────────────────────────────────────────

def gerar_manchete_plantao_cvm() -> str:
    """Plantão CVM — fase 1 da Rodada 4 (disparado pelo Gerenciador)."""
    return """
    <div style="background-color:#fff;border:1px solid #ddd;font-family:'Arial',sans-serif;max-width:600px;margin:0 auto 20px auto;box-shadow:0 4px 10px rgba(0,0,0,0.15);border-radius:4px;overflow:hidden;">
        <div style="background-color:#1a1a1a;color:#fff;display:flex;justify-content:space-between;align-items:center;padding:12px 20px;">
            <div style="font-size:24px;font-weight:900;letter-spacing:1px;">GC NEWS</div>
            <div style="font-size:12px;font-weight:bold;background:rgba(255,0,0,0.5);padding:4px 8px;border-radius:4px;">🚨 AO VIVO</div>
        </div>
        <div style="padding:20px 15px;">
            <div style="background-color:#b71c1c;color:#fff;padding:12px 15px;border-radius:2px;font-size:16px;font-weight:bold;text-transform:uppercase;line-height:1.3;">
                🚨 PLANTÃO URGENTE — CVM INICIA FISCALIZAÇÃO EXTRAORDINÁRIA
            </div>
            <div style="margin-top:6px;border-left:4px solid #b71c1c;padding:8px 12px;background-color:#ffebee;">
                <p style="font-size:13px;color:#333;margin:0;text-align:justify;line-height:1.4;">
                    SÃO PAULO — A Comissão de Valores Mobiliários instaurou, nesta data, auditoria extraordinária
                    em todas as companhias listadas do setor. O  mercado aguarda os resultados da fiscalização.
                </p>
            </div>
        </div>
    </div>"""


def gerar_manchete_dinamica(estado: dict, rodada_encerrada: int) -> str:
    """Gera a notícia de mídia para rodadas 1-3 (melhor e pior resultado)
       e o veredicto completo na Rodada 4."""



    # ── RODADAS 1-3: melhor e pior ───────────────────────────────────────────
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

    if todos_empatados:
        topo_manchete = f"EMPATE GERAL NA RODADA {rodada_encerrada}"
        topo_texto    = f"SÃO PAULO — Todas as companhias fecharam pareadas em R$ {lider_dados['atual']:.2f}."
        secao_baixo   = ""
    else:
        topo_manchete = f"{lider_nome} dispara {fmt_var(lider_dados['var'])}!"
        topo_texto    = f"SÃO PAULO — A {lider_nome} subiu de R$ {lider_dados['anterior']:.2f} para R$ {lider_dados['atual']:.2f}."
        baixo_manchete = f"{lanterna_nome} despenca {fmt_var(lanterna_dados['var'])}"
        baixo_texto    = f"SÃO PAULO — A {lanterna_nome} caiu para R$ {lanterna_dados['atual']:.2f}."
        secao_baixo = f"""
        <div style="background-color:#c62828;color:#fff;padding:12px 15px;border-radius:2px;
                    font-size:15px;font-weight:bold;text-transform:uppercase;">{baixo_manchete}</div>
        <div style="margin-top:6px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;">
            <p style="font-size:13px;color:#333;margin:0;text-align:justify;">{baixo_texto}</p>
        </div>"""

    return f"""
    <div style="background-color:#fff;border:1px solid #ddd;font-family:'Arial',sans-serif;
                max-width:600px;margin:0 auto 20px auto;
                box-shadow:0 4px 10px rgba(0,0,0,0.15);border-radius:4px;overflow:hidden;">
        <div style="background-color:#cc0000;color:#fff;display:flex;
                    justify-content:space-between;align-items:center;padding:12px 20px;">
            <div style="font-size:24px;font-weight:900;letter-spacing:1px;">GC NEWS</div>
            <div style="font-size:12px;font-weight:bold;background:rgba(0,0,0,0.2);
                        padding:4px 8px;border-radius:4px;">EXERCÍCIO {rodada_encerrada}</div>
        </div>
        <div style="padding:20px 15px;">
            <div style="background-color:#2e7d32;color:#fff;padding:12px 15px;border-radius:2px;
                        font-size:15px;font-weight:bold;text-transform:uppercase;
                        line-height:1.3;">{topo_manchete}</div>
            <div style="margin-top:6px;margin-bottom:20px;border-left:4px solid #2e7d32;
                        padding:8px 12px;background-color:#f1f8e9;">
                <p style="font-size:13px;color:#333;margin:0;text-align:justify;
                           line-height:1.4;">{topo_texto}</p>
            </div>
            {secao_baixo}
        </div>
    </div>"""

def _limpar_html(html: str) -> str:
    """Remove linhas vazias/só-espaço que fazem o Markdown tratar o HTML
    como bloco de código em vez de renderizar."""
    linhas = [linha for linha in html.split("\n") if linha.strip() != ""]
    return "\n".join(linhas)


def gerar_manchete_veredicto(estado: dict) -> str:
    """Veredicto final — fase 2 da Rodada 4 (gerado após Conferir Apuração)."""
    manchetes_empresas = []
    for nome in EMPRESAS:
        d = estado["dados_empresas"][nome]
        r1, r2, r3 = d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")
        qtd_c = [r1, r2, r3].count("C")
        qtd_b = [r1, r2, r3].count("B")
        preco_final = d["precos"][-1]

        if qtd_c == 3:
            manchete_emp = f"⛓️ PRISÃO DOS EXECUTIVOS DA {nome.upper()}!"
            texto_emp    = f"A CVM e a Polícia Federal deflagraram a Operação Excel Criativo 🚔. CEO e CFO presos preventivamente 🔗⛓️. Preço final: R$ {preco_final:.2f}."
        elif qtd_c == 2:
            manchete_emp = f"💰🚫 JUSTIÇA BLOQUEIA BENS DA {nome.upper()}!"
            texto_emp    = f"Bloqueio cautelar dos bens dos ex-executivos 💰⚖️. CEO, CFO e Diretor de RI substituídos. Preço final: R$ {preco_final:.2f}."
        elif qtd_c == 1 and qtd_b >= 1:
            manchete_emp = f"💸 {nome.upper()} MULTADA! 🚪 CEO E CFO OS MAIS NOVOS EX-FUNCIONÁRIOS"
            texto_emp    = f"Combinação entre fraude pontual e accruals discricionários resultou em demissão de CEO e CFO 🚪👔. + multa milionária 💸 Preço final: R$ {preco_final:.2f}."
        elif qtd_c == 1:
            manchete_emp = f"🥲 {nome.upper()} — FRAUDE PONTUAL x ERRO? NÃO IMPORTA ...."
            texto_emp    = f"Irregularidade considerada pontual, mas o CEO foi convidado a 'buscar novos desafios' 💼. Preço final: R$ {preco_final:.2f}."
        elif qtd_b >= 2:
            manchete_emp = f"📉 {nome.upper()} — MESTRE DO PÔQUER CONTÁBIL"
            texto_emp    = f"Sem fraude identificada, mas accruals discricionários excessivos colocam o CFO sob monitoramento permanente 👀♠️. Preço final: R$ {preco_final:.2f}."
        elif qtd_b == 1:
            manchete_emp = f"ℹ️ CFO É O SALVADOR DA PÁTRIA OU APENAS DAS AÇÕES DA {nome.upper()}"
            texto_emp    = f"Um episódio isolado de accruals discricionários, para um bem maior... TODOS FELIZES! Preço final: R$ {preco_final:.2f}."
        else:
            manchete_emp = f"☠️ {nome.upper()} MORREU ABRAÇADA COM A ÉTICA"
            texto_emp    = f"Transparência total, mas o mercado não perdoou as perdas reconhecidas 📉. Massacrada na Faria Lima com ação em baixa 🩸 Preço final: R$ {preco_final:.2f}."

        manchetes_empresas.append(f"""<div style="background-color:#c62828;color:#fff;padding:12px 15px;border-radius:2px;font-size:14px;font-weight:bold;text-transform:uppercase;line-height:1.3;margin-top:10px;">{manchete_emp}</div>
        <div style="margin-top:4px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;">
            <p style="font-size:13px;color:#333;margin:0;text-align:justify;line-height:1.4;">{texto_emp}</p>
        </div>""")

    html = f"""
    <div style="background-color:#fff;border:1px solid #ddd;font-family:'Arial',sans-serif;max-width:600px;margin:0 auto 20px auto;box-shadow:0 4px 10px rgba(0,0,0,0.15);border-radius:4px;overflow:hidden;">
        <div style="background-color:#1a1a1a;color:#fff;display:flex;justify-content:space-between;align-items:center;padding:12px 20px;">
            <div style="font-size:24px;font-weight:900;letter-spacing:1px;">GC NEWS</div>
            <div style="font-size:12px;font-weight:bold;background:rgba(0,0,0,0.3);padding:4px 8px;border-radius:4px;">🏁 VEREDICTO FINAL</div>
        </div>
        <div style="padding:20px 15px;">
            <div style="background-color:#2e7d32;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;line-height:1.3;">
                🏁 CVM DIVULGA VEREDITO FINAL — DESTINO DOS EXECUTIVOS
            </div>
            <div style="margin-top:6px;margin-bottom:12px;border-left:4px solid #2e7d32;padding:8px 12px;background-color:#f1f8e9;">
                <p style="font-size:13px;color:#333;margin:0;text-align:justify;line-height:1.4;">
                    SÃO PAULO — A CVM concluiu a auditoria extraordinária e divulgou os resultados individuais
                    de cada companhia investigada. Os mercados reagiram com volatilidade histórica.
                </p>
            </div>
            {"".join(manchetes_empresas)}
        </div>
    </div>"""
    return _limpar_html(html)

# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICOS
# ─────────────────────────────────────────────────────────────────────────────
matplotlib.use("Agg")

def plotar_grafico_empresa(estado: dict, nome_empresa: str):
    precos = estado["dados_empresas"][nome_empresa]["precos"]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#1e222b")
    ax.plot(range(len(precos)), precos, marker="o", color="#00ffa3", linewidth=3, markersize=8)
    labels_disp = ["Abertura", "R1", "R2", "R3", "Auditoria"]
    ax.set_xticks(range(len(precos)))
    ax.set_xticklabels(labels_disp[:len(precos)])
    ax.tick_params(colors="white")
    ax.grid(color="#333", linestyle="--", alpha=0.5)
    st.pyplot(fig)
    plt.close(fig)

def plotar_grafico_geral(estado: dict):
    tamanhos  = [len(estado["dados_empresas"][emp]["precos"]) for emp in EMPRESAS]
    maior_tam = max(tamanhos)
    labels_disp = ["Abertura", "R1", "R2", "R3", "Auditoria"]
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#1e222b")
    cores = ["#00ffa3", "#ff6b6b", "#ffd700"]
    for i, emp in enumerate(EMPRESAS):
        precos = estado["dados_empresas"][emp]["precos"]
        ax.plot(range(len(precos)), precos, label=emp, marker="o", color=cores[i], linewidth=2.5, markersize=7)
    ax.set_xticks(range(maior_tam))
    ax.set_xticklabels(labels_disp[:maior_tam])
    ax.tick_params(colors="white")
    ax.legend(facecolor="#1e222b", edgecolor="#444", labelcolor="white")
    ax.grid(color="#333", linestyle="--", alpha=0.5)
    st.pyplot(fig)
    plt.close(fig)
# ─────────────────────────────────────────────────────────────────────────────
# NAVEGAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "🏠 Início"

perfis_navegacao = [
    "🏠 Início", "🎛️ Painel Gerenciador", 
    "α - Empresa Alfa", "β - Empresa Beta", "γ - Empresa Gama",
]

def ir_para(pagina: str, origem: str | None = None):
    """
    Navega para outra página do app.
    """
    if origem is not None:
        st.session_state["empresa_origem"] = origem

    st.session_state["pagina_atual"] = pagina
    st.rerun()


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────

pagina_atual = st.session_state["pagina_atual"]

if pagina_atual in perfis_navegacao:
    _idx_atual = perfis_navegacao.index(pagina_atual)
else:
    _idx_atual = 0

perfil_sidebar = st.sidebar.selectbox(
    "Navegação Lateral:",
    perfis_navegacao,
    index=_idx_atual,
    key="nav_sidebar_select",
)

if (
    perfil_sidebar != st.session_state["pagina_atual"]
    and st.session_state["pagina_atual"] in perfis_navegacao
):
    if (
        st.session_state["pagina_atual"] == "🎛️ Painel Gerenciador"
        and perfil_sidebar != "🎛️ Painel Gerenciador"
    ):
        st.session_state["gerenciador_autenticado"] = False

    ir_para(perfil_sidebar)

perfil = st.session_state["pagina_atual"]
# ─────────────────────────────────────────────────────────────────────────────
# TELA: INÍCIO
# ─────────────────────────────────────────────────────────────────────────────
if perfil == "🏠 Início":
    estado = carregar_estado()
    st.title("🔒 Simulador de Governança")
    st.markdown("### Selecione o seu ambiente de acesso abaixo:")
    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.markdown("### 🎛️ Gerenciador")
            st.write("Acesso restrito para o Apresentador controlar as rodadas.")
            senha_g = st.text_input("Senha do Gerenciador:", type="password", key="senha_gerenciador_inicio")
            if st.button("Acessar Painel Gerenciador", use_container_width=True, type="primary"):
                if senha_g == SENHA_GERENCIADOR:
                    st.success("✅ Acesso autorizado!")
                    st.session_state["gerenciador_autenticado"] = True
                    ir_para("🎛️ Painel Gerenciador")
                else:
                    st.error("❌ Senha incorreta.")

       with c2:
        with st.container(border=True):
            st.markdown("### 🏢 Empresas")
    
            opcoes = list(EMPRESA_MAP.keys())
            empresa_escolhida = st.selectbox("Escolha sua empresa:", opcoes)
    
            if st.button("Entrar como representante da empresa", use_container_width=True, type="primary"):
    
                st.session_state["empresa_logada"] = empresa_escolhida
                ir_para(empresa_escolhida)

# ─────────────────────────────────────────────────────────────────────────────
# TELA: PAINEL DO GERENCIADOR
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "🎛️ Painel Gerenciador":
    estado = carregar_estado()

    # Autenticação persistente na sessão
    if not st.session_state.get("gerenciador_autenticado", False):
        st.title("🎛️ Painel Gerenciador")
        st.markdown("### 🔑 Acesso Restrito")
        senha_g = st.text_input("Digite a senha do Gerenciador:", type="password", key="senha_gerenciador_painel")
        if st.button("Entrar", use_container_width=True, type="primary"):
            if senha_g == SENHA_GERENCIADOR:
                st.session_state["gerenciador_autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
        st.stop()

    st.title("🎛️ Painel Gerenciador")
    rodada = estado["rodada_atual"]
    st.markdown(f"## Rodada Atual: **{rodada}**")

    # Score geral sempre visível no gerenciador
    st.markdown("### 📊 Score Ético/Discricionário por Empresa")
    score_cols = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        d = estado["dados_empresas"][emp]
        votos_emp = {f"r{r}": d.get(f"voto_r{r}") for r in range(1, 4)}
        score = calcular_dre_dinamico(votos_emp)["score_gr"]
        with score_cols[i]:
            cor_score = "#c62828" if score >= 6 else "#f57f17" if score >= 3 else "#2e7d32"
            st.markdown(
                f"<div style='background:{cor_score};color:#fff;border-radius:8px;padding:10px;text-align:center;'>"
                f"<b>{emp}</b><br>Score: <b>{score}</b></div>",
                unsafe_allow_html=True
            )

    st.divider()

    # Timer — botão de início + exibição
    chave_timer = f"timer_inicio_r{rodada}" if rodada <= 3 else None
    ts_inicio = estado.get(chave_timer) if chave_timer else None

    if rodada <= 3 and not ts_inicio:
        if st.button(f"⏱️ Iniciar Timer — Rodada {rodada}", use_container_width=True, type="primary"):
            estado[chave_timer] = time.time()
            salvar_estado(estado)
            st.rerun()
    elif ts_inicio and rodada <= 3:
        restante_i = max(0, int(10 * 60 - (time.time() - ts_inicio)))
        minutos = restante_i // 60
        segundos = restante_i % 60

        if restante_i >= 7 * 60:
            cor_timer, bg_timer, emoji_timer = "#2e7d32", "#e8f5e9", "🟢"
        elif restante_i >= 3 * 60:
            cor_timer, bg_timer, emoji_timer = "#f57f17", "#fff8e1", "🟡"
        else:
            cor_timer, bg_timer, emoji_timer = "#c62828", "#ffebee", "🔴"

        st.markdown(
            f"<div style='background:{bg_timer};border:1px solid {cor_timer};border-radius:8px;"
            f"padding:8px 14px;color:{cor_timer};font-weight:bold;font-size:16px;display:inline-block;'>"
            f"{emoji_timer} Tempo restante — Rodada {rodada}: {minutos:02d}:{segundos:02d}</div>",
            unsafe_allow_html=True
        )

    st.markdown("### Status de Votos")

    cols = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        d    = estado["dados_empresas"][emp]
        voto = d.get(f"voto_r{rodada}") if rodada <= 3 else "—"
        with cols[i]:
            if voto:
                st.success(f"**{emp}**: ✅ {voto}")
            else:
                st.warning(f"**{emp}**: ⏳ Aguardando")

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
                use_container_width=True, type="primary"
            ):
                for emp in EMPRESAS:
                    d = estado["dados_empresas"][emp]
                    if len(d["precos"]) == rodada:
                        d["precos"].append(calcular_novo_preco(estado, emp, rodada))

                html_noticia = gerar_manchete_dinamica(estado, rodada)
                estado["historico_noticias"].append(html_noticia)
                estado[f"apurado_r{rodada}"] = True
                salvar_estado(estado)
                st.success(f"✅ Resultados apurados! Mídia Rodada {rodada} liberada.")
                st.rerun()
        else:
            st.success(f"✅ Rodada {rodada} apurada. Mídia {rodada} liberada.")

            premiacao_feita = estado.get(f"premiacao_r{rodada}", False)
            if not premiacao_feita:
                st.markdown("### 🏆 Premiação dos Acionistas")
                if st.button("🏆 Liberar Bônus", key=f"premio_r{rodada}", use_container_width=True):
                    ranking = sorted(EMPRESAS, key=lambda e: estado["dados_empresas"][e]["precos"][-1], reverse=True)
                    estado["dados_empresas"][ranking[0]]["precos"][-1] += 2
                    estado["dados_empresas"][ranking[1]]["precos"][-1] += 1
                    estado[f"premiacao_r{rodada}"] = True
                    salvar_estado(estado)
                    st.success(f"✅ Bônus aplicado! {ranking[0]} +R$2, {ranking[1]} +R$1")
                    st.rerun()
            else:
                st.success("🏆 Premiação dos acionistas já aplicada.")

            if rodada < 3:
                if st.button(f"▶️ Avançar para Rodada {rodada + 1}", use_container_width=True):
                    estado["rodada_atual"] = rodada + 1
                    estado[f"timer_inicio_r{rodada + 1}"] = time.time()
                    salvar_estado(estado)
                    st.rerun()
            elif rodada == 3:
                if st.button("▶️ Avançar para Rodada 4 — Auditoria Final", use_container_width=True):
                    estado["rodada_atual"] = 4
                    salvar_estado(estado)
                    st.rerun()

    elif rodada == 4:
        st.markdown("## 🚨 Plantão CVM — Auditoria Final")

        plantao_disparado = bool(estado.get("historico_noticias_plantao"))
        apuracao_feita    = estado.get("apuracao_r4_feita", False)

        # FASE 1 — Disparar Plantão CVM
        if not plantao_disparado:
            if st.button("🔎 Disparar Plantão CVM", use_container_width=True, type="primary"):
                html_plantao = gerar_manchete_plantao_cvm()
                estado["historico_noticias_plantao"].append(html_plantao)
                salvar_estado(estado)
                st.success("✅ Plantão CVM disparado! Mídia liberada.")
                st.rerun()
        else:
            st.success("✅ Plantão CVM já disparado.")
        # FASE 2 — Conferir Apuração Final
        if not apuracao_feita:
            if st.button("🏁 Conferir Apuração Final", use_container_width=True, type="primary"):
                for emp in EMPRESAS:
                    processar_rodada_4_consolidada(estado, emp)
                html_veredicto = gerar_manchete_veredicto(estado)
                estado["historico_noticias_veredicto"].append(html_veredicto)
                estado["apuracao_r4_feita"] = True
                salvar_estado(estado)
                st.success("✅ Auditoria concluída! Veredicto e cartas liberadas para as empresas.")
                st.rerun()
        else:
            st.success("✅ Apuração final já realizada. Veredicto liberado na Mídia.")

    st.divider()

    if st.button("♻️ Resetar Simulação", use_container_width=True):
        resetar_estado()
        st.session_state["gerenciador_autenticado"] = False
        for emp in ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]:
            st.session_state.pop(f"auth_{emp}", None)
        st.success("✅ Simulação resetada.")
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: TELÃO
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📈 Telão (Bolsa)":
    estado = carregar_estado()
    st.title("📈 Telão Comercial")

    _origem = st.session_state.get("empresa_origem", "🎛️ Painel Gerenciador")
    nav1, nav2, nav3, _ = st.columns([1, 1, 1, 3])
    with nav1:
        if st.button("📋 Rodada", use_container_width=True):
            ir_para(_origem)
    with nav2:
        if st.button("📈 Telão", use_container_width=True, type="primary"):
            st.rerun()
    with nav3:
        if st.button("📰 Mídia", use_container_width=True):
            ir_para("📰 Mídia (Notícias)")

    plotar_grafico_geral(estado)
    time.sleep(5)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: MÍDIA
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📰 Mídia (Notícias)":
    estado = carregar_estado()
    st.title("📰 GC News — Central de Notícias")

    _origem = st.session_state.get("empresa_origem", "🎛️ Painel Gerenciador")
    st.session_state["empresa_origem"] = perfil
    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")

    # Veredicto final (R4 fase 2) 
    if estado.get("historico_noticias_veredicto"):
        for n_html in reversed(estado["historico_noticias_veredicto"]):
            st.markdown(n_html, unsafe_allow_html=True)
    
    # Plantão CVM (R4 fase 1)
    if estado.get("historico_noticias_plantao"):
        for n_html in reversed(estado["historico_noticias_plantao"]):
            st.markdown(n_html, unsafe_allow_html=True)
    
    # Notícias das rodadas 1-3
    if estado.get("historico_noticias"):
        st.write("Qtd notícias:", len(estado["historico_noticias"]))
    
        for n_html in reversed(estado["historico_noticias"]):
            st.markdown(n_html, unsafe_allow_html=True)
    
    # Nenhuma notícia
    if (
        not estado.get("historico_noticias")
        and not estado.get("historico_noticias_plantao")
        and not estado.get("historico_noticias_veredicto")
    ):
        st.info("⏳ Nenhuma notícia publicada neste ciclo.")

# ── TELA DA EMPRESA (autenticada) ────────────────────────────────────────
# ── TELA DA EMPRESA (autenticada) ────────────────────────────────────────

if perfil not in EMPRESA_MAP:
    st.stop()

# pega empresa corretamente
empresa_nome = EMPRESA_MAP[perfil]
estado = carregar_estado()
d = estado["dados_empresas"][empresa_nome]
rodada = estado.get("rodada_atual", 1)

# Mensagem do bônus/penalidade da rodada anterior (mostra uma única vez)
if rodada > 1:
    msg = d.get(f"msg_bonus_r{rodada-1}")
    if msg:
        st.success(msg)
        d.pop(f"msg_bonus_r{rodada-1}", None)
        salvar_estado(estado)

# origem de navegação
st.session_state["empresa_origem"] = perfil
st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")

# ── TIMER ───────────────────────────────────────────────────────────────
chave_timer = f"timer_inicio_r{rodada}" if rodada <= 3 else None
ts_inicio = estado.get(chave_timer) if chave_timer else None

if ts_inicio and rodada <= 3:
    restante_i = max(0, int(10 * 60 - (time.time() - ts_inicio)))
    minutos = restante_i // 60
    segundos = restante_i % 60

    if restante_i >= 7 * 60:
        cor_timer, bg_timer, emoji_timer = "#2e7d32", "#e8f5e9", "🟢"
    elif restante_i >= 3 * 60:
        cor_timer, bg_timer, emoji_timer = "#f57f17", "#fff8e1", "🟡"
    else:
        cor_timer, bg_timer, emoji_timer = "#c62828", "#ffebee", "🔴"

    st.markdown(
        f"""
        <div style='background:{bg_timer};border:1px solid {cor_timer};
        border-radius:8px;padding:8px 14px;color:{cor_timer};
        font-weight:bold;font-size:16px;display:inline-block;'>
        {emoji_timer} Tempo restante — Rodada {rodada}: {minutos:02d}:{segundos:02d}
        </div>
        """,
        unsafe_allow_html=True
    )


    # ── RODADAS 1-3 ──────────────────────────────────────────────────────────
    if rodada <= 3:
        if not ts_inicio:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1a237e,#283593);border-radius:16px;
                        padding:48px 32px;margin:24px 0;text-align:center;color:#fff;
                        box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-size:72px;margin-bottom:16px;">🔒</div>
                <div style="font-size:24px;font-weight:900;margin-bottom:12px;">AGUARDANDO INÍCIO</div>
                <div style="font-size:15px;opacity:0.85;">O Gerenciador ainda não iniciou esta rodada.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if rodada == 1:
                st.markdown(narrativa_rodada_1())
            elif rodada == 2:
                st.markdown(narrativa_rodada_2())
            elif rodada == 3:
                st.markdown(narrativa_rodada_3())

            voto_atual = d.get(f"voto_r{rodada}")
            if voto_atual is None:
                escolha = st.radio(
                    "Selecione o tratamento contábil:",
                    ["A", "B", "C"],
                    format_func=lambda x: get_labels(rodada)[x]
                )
                if st.button("✅ Homologar Resolução", use_container_width=True):
                    ja_votaram = sum(
                        1 for e in EMPRESAS
                        if estado["dados_empresas"][e].get(f"voto_r{rodada}") is not None
                    )
                    d[f"voto_r{rodada}"] = escolha
                    d[f"tempo_voto_r{rodada}"] = time.time()

                    if ja_votaram == 0:
                        d[f"bonus_velocidade_r{rodada}"] = "primeiro"
                    elif ja_votaram == 1:
                        d[f"bonus_velocidade_r{rodada}"] = "meio"
                    else:
                        d[f"bonus_velocidade_r{rodada}"] = "ultimo"

                    votos_total = [estado["dados_empresas"][e].get(f"voto_r{rodada}") for e in EMPRESAS]
                    if all(v is not None for v in votos_total):
                        chave_timer_global = f"timer_inicio_r{rodada}"
                        if estado.get(chave_timer_global):
                            estado[chave_timer_global] = time.time() - 10 * 60

                    salvar_estado(estado)
                    st.rerun()

            else:
                st.success(f"📌 Estratégia Adotada — Opção {voto_atual}")

                apurado = estado.get(f"apurado_r{rodada}", False)
                if apurado:
                    exibir_dre({f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada + 1)}, rodada, mostrar_score=False)
                    bonus_vel = d.get(f"bonus_velocidade_r{rodada}")
                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32);border-radius:12px;
                                padding:20px 24px;margin:16px 0;text-align:center;color:#fff;">
                        <div style="font-size:32px;margin-bottom:8px;">📰</div>
                        <div style="font-size:18px;font-weight:bold;">Resultados apurados!</div>
                        <div style="font-size:14px;margin-top:6px;opacity:0.9;">Acesse a aba <b>Mídia</b> para ver a cobertura completa da rodada.</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#e65100,#bf360c);border-radius:12px;
                                padding:24px;margin:16px 0;text-align:center;color:#fff;">
                        <div style="font-size:48px;margin-bottom:10px;">⏳</div>
                        <div style="font-size:20px;font-weight:bold;">Aguardando apuração...</div>
                        <div style="font-size:14px;margin-top:8px;opacity:0.9;">Sua decisão foi registrada. Aguarde o Gerenciador apurar os resultados.</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── RODADA 4 ──────────────────────────────────────────────────────────────
    else:
        apuracao_feita = estado.get("apuracao_r4_feita", False)

        if not apuracao_feita:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1a237e,#283593);border-radius:16px;padding:48px 32px;margin:24px 0;text-align:center;color:#fff;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-size:72px;margin-bottom:16px;animation:spin 2s linear infinite;">⏳</div>
                <div style="font-size:28px;font-weight:900;letter-spacing:1px;margin-bottom:12px;">AUDITORIA EM ANDAMENTO</div>
                <div style="font-size:16px;opacity:0.85;">A CVM está analisando os demonstrativos financeiros dos últimos três exercícios.</div>
                <div style="font-size:14px;margin-top:16px;opacity:0.7;">Aguarde o resultado...</div>
            </div>
            <style>
            @keyframes spin { 0%{transform:rotate(0deg)} 50%{transform:rotate(15deg)} 100%{transform:rotate(0deg)} }
            </style>
            """, unsafe_allow_html=True)

        else:
            r1 = d.get("voto_r1")
            r2 = d.get("voto_r2")
            r3 = d.get("voto_r3")
            qtd_c = [r1, r2, r3].count("C")
            qtd_b = [r1, r2, r3].count("B")

            if qtd_c == 3:
                icone_res, cor_res = "⛓️", "#b71c1c"
                titulo_res = "OPERAÇÃO EXCEL CRIATIVO — PRISÃO DOS EXECUTIVOS! O Direito de Permanecer Calado é uma garantia fundamental que eles vão usar."
                texto_res  = "A CVM e a Polícia Federal deflagraram operação contra sua empresa. CEO e CFO presos preventivamente 🔗."
            elif qtd_c == 2:
                icone_res, cor_res = "💰🚫", "#c62828"
                titulo_res = "JUSTIÇA BLOQUEIA BENS DOS EXECUTIVOS!"
                texto_res  = "A Justiça determinou o bloqueio cautelar dos bens dos executivos. CEO, CFO e Diretor de RI foram substituídos. Os conselheiros estão 'profundamente surpresos'."
            elif qtd_c == 1 and qtd_b >= 1:
                icone_res, cor_res = "💸", "#e65100"
                titulo_res = "CEO E CFO VIRAM EX-FUNCIONÁRIOS!"
                texto_res  = "A CVM identificou fraude combinada com accruals. CEO e CFO foram demitidos 🚪. O LinkedIn deles foi atualizado em tempo recorde."
            elif qtd_c == 1:
                icone_res, cor_res = "🥲", "#f57f17"
                titulo_res = "FRAUDE/ ERRO PONTUAL — CEO DEMITIDO!"
                texto_res  = "Mesmo considerada pontual, a irregularidade destruiu a confiança dos investidores. CEO foi convidado a 'buscar novos desafios profissionais' 💼."
            elif qtd_b >= 2:
                icone_res, cor_res = "📉", "#1565c0"
                titulo_res = "MESTRE DO PÔQUER CONTÁBIL! e VIGILÂNCIA REDOBRADA"
                texto_res  = "Sem fraude identificada, mas o abuso de accruals discricionário colocou o CFO sob monitoramento permanente de três auditores independentes ♠️ e do estagiário de compliance 👀."
            elif qtd_b == 1:
                icone_res, cor_res = "ℹ️", "#2e7d32"
                titulo_res = "🦸‍♂️ CFO vira HERÓI/ HEROÍNA DO MERCADO!"
                texto_res  = "Com apenas um ajuste contábil estratégico, salvou a operação sem cruzar a linha vermelha da CVM. Alguns heróis usam capa!!! A empresa está salva e a gestão foi aplaudida!"
            else:
                icone_res, cor_res = "☠️", "#4a148c"
                titulo_res = "ÉTICA PRESERVADA — AÇÕES AFUNDARAM"
                texto_res  = "Transparência total. Governança check ✅. Orgulho da professora ❤️! Os auditores aplaudiram 👏. Os investidores venderam 📉. Os bônus desapareceram 💸. A reputação sobreviveu. O preço da ação, não."

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{cor_res}dd,{cor_res}88);border:2px solid {cor_res};border-radius:16px;padding:32px;margin:24px 0;text-align:center;color:#fff;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-size:56px;margin-bottom:12px;">{icone_res}</div>
                <div style="font-size:22px;font-weight:900;letter-spacing:1px;margin-bottom:16px;text-transform:uppercase;">{titulo_res}</div>
                <div style="background:rgba(255,255,255,0.12);border-radius:10px;padding:16px 20px;font-size:14px;line-height:1.7;text-align:left;">
                    {texto_res}
                </div>
            </div>
            """, unsafe_allow_html=True)

            carta_html = gerar_carta_destino(empresa_nome, r1, r2, r3)
            st.markdown(carta_html, unsafe_allow_html=True)

            st.markdown("""
            <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32);border-radius:12px;padding:16px 24px;margin:12px 0;text-align:center;color:#fff;">
                <div style="font-size:14px;">Acesse a aba <b>Mídia</b> para ver o veredicto completo de todas as empresas.</div>
            </div>
            """, unsafe_allow_html=True)

    # Auto-refresh
    time.sleep(6)
    st.rerun()
