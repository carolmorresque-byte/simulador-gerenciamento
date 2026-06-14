import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import time
import json
import os
import fcntl

st.set_page_config(page_title="Simulador de Varejo - Governança Avançada", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

STATE_FILE = os.path.join(os.path.dirname(__file__), "game_state.json")
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]

def _estado_inicial() -> dict:
    return {
        "rodada_atual": 1,
        "historico_noticias": [],
        "sessoes_ativas": [],
        "senhas_empresas": {"Empresa Alfa": "alfa", "Empresa Beta": "beta", "Empresa Gama": "gama"},
        "dados_empresas": {
            nome: {
                "precos": [20.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None, "voto_r4": None,
                "tempo_voto_r1": None, "tempo_voto_r2": None, "tempo_voto_r3": None,
                "status": "Operando", "noticia_r4": "", "score_gr": 0,
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
        # Sempre garante senhas corretas (sobrescreve estado antigo)
        estado["senhas_empresas"] = {"Empresa Alfa": "alfa", "Empresa Beta": "beta", "Empresa Gama": "gama"}
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

def get_labels(rodada: int, pecld_m: float = 200.0) -> dict:
    if rodada == 1: return LABELS_R1
    if rodada == 2: return LABELS_R2
    if rodada == 3:
        return {
            "A": f"OPÇÃO A: Lançar PECLD — Registra o calote real de R$ {pecld_m:,.0f}M na DRE conforme o CPC 48 (IFRS 9).".replace(",", "."),
            "B": "OPÇÃO B: Securitização via FIDC com Deságio — Transfere a carteira para um fundo. Aloca R$ 50M de prejuízo no Financeiro, blindando o EBITDA.",
            "C": "OPÇÃO C: Congelar Provisões e Antecipar Garantias — Omite as perdas e antecipa R$ 80M de receitas futuras (Brecha CPC 47).",
        }
    return LABELS_R1

NARRATIVAS = {
    1: """### 🏭 RODADA 1: RISCO SACADO E COVENANTS FINANCEIROS
**Cenário:** A empresa enfrenta pressões de liquidez e, para manter suas operações, utilizou uma estrutura de risco sacado com o Banco Épsilon. Essa operação antecipa o recebimento para fornecedores estratégicos e estende o prazo de pagamento da companhia (com juros de R$ 10MM), evitando o desabastecimento.

O principal problema é o impacto nos covenants financeiros:
*   **Situação Atual:** O índice Dívida Líquida/EBITDA está em 2,9x (o limite contratual é 3,0x).
*   **O Risco:** Se o risco sacado for reclassificado de passivo comercial para dívida financeira, o índice salta para 4,2x. Isso causará o vencimento antecipado das dívidas e travará novos créditos.

**Sua missão:** Definir a classificação contábil dessa operação, ponderando a realidade técnica contra o risco de quebra de contrato e o conflito de interesses na remuneração.""",
    2: """### 📰 RODADA 2: A CRISE DO DÓLAR E OS CONTRATOS DE IMPORTAÇÃO

**Cenário:** A companhia enfrenta uma severa crise de margem operacional. A ausência de proteção cambial (*hedge*) expôs a operação diretamente à volatilidade internacional, agravada por gargalos logísticos.

*   **Estouro no Custo de Aquisição (CMV):** A alta do dólar (de R$ 5,00 para R$ 6,50) elevou o custo de importação de 200 mil smartphones de R$ 100MM para R$ 130MM — impacto de **-R$ 30MM no CMV**.
*   **Problema Logístico:** A retenção fiscal na alfândega por 45 dias extras gerou pesadas multas de armazenagem (*demurrage*), inflando as despesas operacionais.
*   **Vendas Travadas:** A tentativa de repassar os custos paralisou as vendas e encalhou o estoque, disparando o risco de obsolescência tecnológica.

A diretoria se reúne em caráter de urgência para definir a manobra orçamentária.""",
}

def calcular_dre_dinamico(votos: dict) -> dict:
    receita     = 20_000_000_000.0
    cmv         = -16_500_000_000.0
    pdd         = -150_000_000.0
    depreciacao = -150_000_000.0
    outras_desp = -2_200_000_000.0
    juros       = -300_000_000.0

    v1 = votos.get("r1")
    if v1 == "A": juros = -310_000_000.0
    elif v1 == "C": pdd = -100_000_000.0

    v2 = votos.get("r2")
    if v2 == "A": cmv -= 30_000_000.0
    elif v2 == "B": depreciacao += 20_000_000.0

    carteira_recebiveis = receita * 0.30
    pecld_dinamica = carteira_recebiveis * 0.12

    v3 = votos.get("r3")
    if v3 == "A": pdd -= pecld_dinamica
    elif v3 == "B": juros -= 50_000_000.0
    elif v3 == "C": receita += 80_000_000.0

    lucro_bruto = receita + cmv
    # EBITDA não inclui depreciação (ela é deduzida depois)
    ebitda      = lucro_bruto + pdd + outras_desp
    # Lucro Líquido = EBITDA - Depreciação + Resultado Financeiro
    lucro_liq   = ebitda + depreciacao + juros

    return {
        "receita": receita, "cmv": abs(cmv), "lucro_bruto": lucro_bruto,
        "pdd": abs(pdd), "depreciacao": abs(depreciacao), "outras_desp": abs(outras_desp),
        "ebitda": ebitda, "juros": abs(juros), "lucro_liq": lucro_liq,
        "pecld_dinamica": pecld_dinamica,
    }

def exibir_dre(votos_empresa: dict, rodada_exibida: int):
    dre = calcular_dre_dinamico(votos_empresa)
    st.markdown(f"### 📋 DRE Acumulada — Exercício {rodada_exibida}")
    def fmt(v, negativo=False):
        sinal = "-" if negativo else ""
        return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    linhas = [
        ("(=) Receita Bruta de Vendas",           fmt(dre["receita"]),           False),
        ("(-) Custo das Mercadorias (CMV)",        fmt(dre["cmv"],       True),   False),
        ("(=) Lucro Bruto Operacional",            fmt(dre["lucro_bruto"]),       True),
        ("(-) Provisão para Calotes (PDD/PECLD)",  fmt(dre["pdd"],       True),   False),
        ("(-) Depreciação de Lojas/Ativos",        fmt(dre["depreciacao"],True),  False),
        ("(-) Outras Despesas Operacionais",       fmt(dre["outras_desp"],True),  False),
        ("(=) EBITDA APURADO",                    fmt(dre["ebitda"]),            True),
        ("(-) Result. Financeiro (Dívidas/Juros)", fmt(dre["juros"],     True),   False),
        ("(=) LUCRO LÍQUIDO DO EXERCÍCIO",         fmt(dre["lucro_liq"]),         True),
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
    if rodada_encerrada == 1:
        if todos_empatados:
            topo_manchete = "MAR CALMO: EMPRESAS REGISTRAM EQUILÍBRIO ABSOLUTO"
            topo_texto    = f"SÃO PAULO — Todas as companhias fecharam pareadas em R$ {lider_dados['atual']:.2f}."
        else:
            topo_manchete  = f"MAR EM FÚRIA: {lider_nome} SURFA ONDA DE VALORIZAÇÃO E SOBE {fmt_var(lider_dados['var'])}!"
            topo_texto     = f"SÃO PAULO — A agilidade da {lider_nome} impulsionou o papel de R$ {lider_dados['anterior']:.2f} para R$ {lider_dados['atual']:.2f}."
            baixo_manchete = f"NAUFRÁGIO: {lanterna_nome} ENTRA EM REDEMOINHO E PERDE {fmt_var(lanterna_dados['var'])}"
            baixo_texto    = f"SÃO PAULO — Investidores puniram a lentidão da {lanterna_nome}. Papel colapsou para R$ {lanterna_dados['atual']:.2f}."
    elif rodada_encerrada == 2:
        if todos_empatados:
            topo_manchete = "SAFETY CAR NA PISTA: GRID REPETE FECHAMENTO"
            topo_texto    = f"SÃO PAULO — Sem ultrapassagens, os ativos congelaram em R$ {lider_dados['atual']:.2f}."
        else:
            topo_manchete  = f"GP DA TESOURARIA: {lider_nome} ACELERA E SALTA PARA R$ {lider_dados['atual']:.2f}!"
            topo_texto     = f"SÃO PAULO — Com arrancada agressiva, a {lider_nome} registrou alta de {fmt_var(lider_dados['var'])}."
            baixo_manchete = f"RODOU NA CURVA: {lanterna_nome} PERDE TRAÇÃO"
            baixo_texto    = f"SÃO PAULO — A {lanterna_nome} viu seus papéis perderem {fmt_var(lanterna_dados['var'])}, fechando a R$ {lanterna_dados['atual']:.2f}."
    elif rodada_encerrada == 3:
        if todos_empatados:
            topo_manchete = "GONGADO: ÚLTIMO ROUND TERMINA EM EMPATE"
            topo_texto    = f"SÃO PAULO — O combate contra a crise terminou sem vencedor em R$ {lider_dados['atual']:.2f}."
        else:
            topo_manchete  = f"NOCAUTE NA BOLSA: {lider_nome} SEGURA O CINTURÃO COM DISPARADA DE {fmt_var(lider_dados['var'])}!"
            topo_texto     = f"SÃO PAULO — A {lider_nome} viu suas ações saltarem de R$ {lider_dados['anterior']:.2f} para R$ {lider_dados['atual']:.2f}."
            baixo_manchete = f"DIRETO NO QUEIXO: {lanterna_nome} CAI À LONA"
            baixo_texto    = f"SÃO PAULO — A {lanterna_nome} sofreu fuga de capitais. Papéis despencaram para R$ {lanterna_dados['atual']:.2f}."
    elif rodada_encerrada == 4:
        topo_manchete   = "🚨 URGENTE: CVM INICIOU INVESTIGAÇÃO NO SETOR!"
        topo_texto      = "SÃO PAULO — A CVM instaurou auditoria geral para apurar indícios de manipulação contábil e omissão de passivos."
        todos_empatados = True
    cor_header   = "#cc0000" if rodada_encerrada != 4 else "#1a1a1a"
    label_header = f"EXERCÍCIO {rodada_encerrada}" if rodada_encerrada < 4 else "AUDITORIA CVM"
    secao_baixo  = "" if todos_empatados else f"""
        <div style="background-color:#c62828;color:#fff;padding:12px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;line-height:1.3;">{baixo_manchete}</div>
        <div style="margin-top:6px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;">
            <p style="font-size:13px;color:#333;margin:0;text-align:justify;line-height:1.4;">{baixo_texto}</p>
        </div>"""
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
    with c1:
        with st.container(border=True):
            st.markdown("### 🎛️ Gerenciador")
            st.write("Acesso restrito para o Apresentador controlar as rodadas.")
            if st.button("Acessar Painel Gerenciador", use_container_width=True, type="primary"):
                st.session_state["pagina_atual"] = "🎛️ Painel Gerenciador"
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("### 🏢 Empresas / Alunos")
            st.write("Selecione a estação de trabalho da sua bancada corporativa.")

            senhas_emp = estado.get("senhas_empresas", {})

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
                senha_input = st.text_input("Senha da sua empresa:", type="password", key="senha_reentrada")
                if st.button("Entrar com Senha", use_container_width=True):
                    if senha_input and senha_input == senhas_emp.get(nome_int):
                        st.session_state["pagina_atual"] = chave_real
                        st.rerun()
                    else:
                        st.error("❌ Senha incorreta.")
            else:
                if st.button("Entrar como Aluno", use_container_width=True):
                    if nome_int not in sessoes:
                        sessoes.append(nome_int)
                        estado["sessoes_ativas"] = sessoes
                        salvar_estado(estado)
                    st.session_state["pagina_atual"] = chave_real
                    st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown("### 📈 Projeção / Telão")
            st.write("Acesso livre para abrir o gráfico dinâmico e cotações na TV/Projetor.")
            if st.button("Abrir Telão Comercial", use_container_width=True):
                st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
                st.rerun()

elif perfil == "🎛️ Painel Gerenciador":
    estado = carregar_estado()
    st.title("📈 TELÃO - Bolsa de R$")
    
    # 1. Navegação: Home | Rodada | Telão | Mídia
    btn_col_h, btn_col0, btn_col1, btn_col2 = st.columns([1, 1, 1, 1])
    with btn_col_h:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state["pagina_atual"] = "🏠 Início"
            st.rerun()
    with btn_col0:
        st.button("📋 Rodada", use_container_width=True, type="primary", disabled=True)
    with btn_col1:
        if st.button("📈 Telão", use_container_width=True):
            st.session_state["telao_origem_empresa"] = "🎛️ Painel Gerenciador"
            st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
            st.rerun()
    with btn_col2:
        if st.button("📰 Mídia", use_container_width=True):
            st.session_state["telao_origem_empresa"] = "🎛️ Painel Gerenciador"
            st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
            st.rerun()

    rodada = estado["rodada_atual"]
    st.markdown(f"## Rodada Atual: **{rodada}**")

    # 2. Status de Votos
    st.markdown("### Status de Votos")
    cols = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        d    = estado["dados_empresas"][emp]
        voto = d.get(f"voto_r{rodada}") if rodada <= 3 else "—"
        with cols[i]:
            if voto: st.success(f"**{emp}**: ✅ {voto}")
            else:    st.warning(f"**{emp}**: ⏳ Aguardando")

    st.divider()

    # 3. Lógica de Apuração e Liberação
    if rodada <= 3:
        # Botão 1: Processar resultados
        if st.button(f"📊 Processar Resultados da Rodada {rodada}", use_container_width=True):
            for emp in EMPRESAS:
                d = estado["dados_empresas"][emp]
                if len(d["precos"]) == rodada:
                    novo = calcular_novo_preco(estado, emp, rodada)
                    d["precos"].append(novo)
            html_noticia = gerar_manchete_dinamica(estado, rodada)
            estado["historico_noticias"].append(html_noticia)
            salvar_estado(estado)
            st.success(f"Resultados da rodada {rodada} processados!")
            st.rerun()

        # Botão 2: Liberar próxima rodada (Start do Timer)
        # Só libera se os preços já foram atualizados (tamanho da lista precos > rodada)
        rodada_processada = all(len(estado["dados_empresas"][emp]["precos"]) > rodada for emp in EMPRESAS)
        
        if rodada_processada:
            if st.button(f"🚀 Liberar Rodada {rodada + 1} para as Bancadas", type="primary", use_container_width=True):
                estado["rodada_atual"] = rodada + 1
                estado[f"timer_inicio_r{rodada + 1}"] = time.time()
                salvar_estado(estado)
                st.success(f"Rodada {rodada + 1} liberada!")
                st.rerun()
        else:
            st.info(f"Processamento necessário antes de liberar a Rodada {rodada + 1}.")

    elif rodada == 4:
        st.markdown("### 🚨 Auditoria CVM — Aplicar Penalidades Finais")
        if st.button("🔨 Aplicar Penalidade CVM e Encerrar Jogo", use_container_width=True, type="primary"):
            for emp in EMPRESAS:
                processar_rodada_4_consolidada(estado, emp)
                estado["dados_empresas"][emp]["status"] = "Auditada"
            html_noticia = gerar_manchete_dinamica(estado, 4)
            estado["historico_noticias"].append(html_noticia)
            estado["rodada_atual"] = 5
            salvar_estado(estado)
            st.success("Auditoria concluída!")
            st.rerun()

    # 4. Zona de Perigo
    st.divider()
    st.markdown("### ⚠️ Zona de Perigo")
    if st.button("🔄 Resetar Jogo do Zero", use_container_width=True):
        resetar_estado()
        st.success("Estado resetado!")
        st.rerun()

    st.divider()
    st.markdown("### 📊 Cotações em Tempo Real")
    plotar_grafico_geral(estado)
    st.markdown("*Página atualiza automaticamente a cada 10 s.*")
    time.sleep(10)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: TELÃO
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📈 Telão (Bolsa)":
    estado = carregar_estado()
    st.title("📈 TELÃO - Bolsa de R$")
    
    btn_col0, btn_col1, btn_col2, _ = st.columns([1, 1, 1, 3])
    with btn_col0:
        origem = st.session_state.get("telao_origem_empresa", "🏠 Início")
        if st.button("📋 Rodada", use_container_width=True):
            st.session_state["pagina_atual"] = origem
            st.rerun()
    with btn_col1:
        st.button("📈 Telão", use_container_width=True, type="primary", disabled=True)
    with btn_col2:
        if st.button("📰 Mídia", use_container_width=True):
            st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
            st.rerun()
            
    plotar_grafico_geral(estado)
    
    st.markdown("### Cotações Atuais")
    cols = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        precos   = estado["dados_empresas"][emp]["precos"]
        preco_at = precos[-1]
        preco_ant= precos[-2] if len(precos) > 1 else preco_at
        with cols[i]:
            st.metric(emp, f"R$ {preco_at:.2f}", f"{preco_at - preco_ant:+.2f}")
    time.sleep(8)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: MÍDIA
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📰 Mídia (Notícias)":
    estado = carregar_estado()
    st.title("📈 TELÃO - Bolsa de R$")
    
    # Navegação padronizada e limpa (sem duplicação)
    btn_col0, btn_col1, btn_col2, _ = st.columns([1, 1, 1, 3])
    with btn_col0:
        origem = st.session_state.get("telao_origem_empresa", "🏠 Início")
        if st.button("📋 Rodada", use_container_width=True):
            st.session_state["pagina_atual"] = origem
            st.rerun()
    with btn_col1:
        if st.button("📈 Telão", use_container_width=True):
            st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
            st.rerun()
    with btn_col2:
        st.button("📰 Mídia", use_container_width=True, type="primary", disabled=True)

    # Exibição
    if estado["historico_noticias"]:
        for n_html in reversed(estado["historico_noticias"]):
            st.html(n_html)
    else:
        st.info("⏳ Nenhuma notícia publicada.")
    
    time.sleep(8)
    st.rerun()
# ─────────────────────────────────────────────────────────────────────────────
# TELAS DAS EMPRESAS
# ─────────────────────────────────────────────────────────────────────────────
elif perfil in EMPRESA_MAP:
    
    estado       = carregar_estado()
    nome_interno = EMPRESA_MAP[perfil]
    d            = estado["dados_empresas"][nome_interno]
    rodada       = estado["rodada_atual"]

    votos_ate_agora = {"r1": d["voto_r1"], "r2": d["voto_r2"]}
    dre_parcial     = calcular_dre_dinamico(votos_ate_agora)
    pecld_m         = dre_parcial["pecld_dinamica"] / 1_000_000.0

    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")

    # Timer
    chave_timer = f"timer_inicio_r{rodada}" if rodada <= 3 else None
    ts_inicio   = estado.get(chave_timer) if chave_timer else None
    if ts_inicio and rodada <= 3:
        restante_i = max(0, int(5 * 60 - (time.time() - ts_inicio)))
        if restante_i > 120:   cor_t="#1b5e20"; bg_t="#e8f5e9"; brd_t="#66bb6a"
        elif restante_i > 30:  cor_t="#6d4c00"; bg_t="#fff8e1"; brd_t="#ffa000"
        else:                  cor_t="#7f0000"; bg_t="#ffebee"; brd_t="#c62828"
        st.markdown(f"""
        <div id="timer-box" style="border:2px solid {brd_t};background:{bg_t};color:{cor_t};border-radius:8px;
            padding:10px 20px;display:inline-flex;align-items:center;gap:12px;margin-bottom:12px;font-family:monospace;">
            <span style="font-size:22px;">⏱️</span>
            <div>
                <div style="font-size:11px;font-weight:600;letter-spacing:1px;text-transform:uppercase;">Tempo restante — Rodada {rodada}</div>
                <div id="timer-display" style="font-size:28px;font-weight:900;letter-spacing:2px;">{restante_i//60:02d}:{restante_i%60:02d}</div>
            </div>
        </div>
        <script>
        (function(){{var total={restante_i};var el=document.getElementById("timer-display");
        var box=document.getElementById("timer-box");if(!el)return;
        var iv=setInterval(function(){{if(total<=0){{el.textContent="00:00";clearInterval(iv);return;}}
        total--;var m=Math.floor(total/60);var s=total%60;
        el.textContent=(m<10?"0":"")+m+":"+(s<10?"0":"")+s;
        if(total<=30){{box.style.borderColor="#c62828";box.style.background="#ffebee";box.style.color="#7f0000";}}
        else if(total<=120){{box.style.borderColor="#ffa000";box.style.background="#fff8e1";box.style.color="#6d4c00";}}
        }},1000);}})();
        </script>""", unsafe_allow_html=True)
        
# Apenas a navegação sem botões de administração:
    btn_a0, btn_a1, btn_a2, _ = st.columns([1, 1, 1, 3])
    with btn_a0:
        st.button("📋 Rodada", use_container_width=True, type="primary", disabled=True)
    with btn_a1:
        if st.button("📈 Telão", use_container_width=True):
            st.session_state["telao_origem_empresa"] = perfil
            st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
            st.rerun()
    with btn_a2:
        if st.button("📰 Mídia", use_container_width=True):
            st.session_state["telao_origem_empresa"] = perfil
            st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
            st.rerun()

    aba_voto, aba_jornal_aluno = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mural Coletivo"])

    with aba_voto:
        if rodada <= 3:
            voto_atual = d.get(f"voto_r{rodada}")
            if voto_atual is None:
                st.markdown(f"### 📋 Deliberação Estratégica — Exercício {rodada}")
                col_prob, col_dre = st.columns([1.1, 0.9], gap="large")
                with col_prob:
                    if rodada == 3:
                        st.markdown(f"""### 🚨 RODADA 3: O DESAFIO DA INSOLVÊNCIA E DA PECLD
A recessão econômica e o desemprego corroeram a renda das famílias, fazendo a inadimplência no crediário próprio saltar de 3% para 12%. Pelas regras do CPC 48 (IFRS 9), a perda de recebíveis obriga a empresa a registrar uma provisão (PECLD) de **R$ {pecld_m:,.0f} milhões** na DRE. O impacto desse lançamento anula o EBITDA do período, escancara uma situação de insolvência técnica e aciona a revisão dos auditores independentes.""")
                    elif rodada in NARRATIVAS:
                        st.markdown(NARRATIVAS[rodada])
                with col_dre:
                    votos_sim = {f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada)}
                    votos_sim[f"r{rodada}"] = "B"
                    exibir_dre(votos_sim, rodada)
                st.markdown("---")
                escolha = st.radio("Selecione o tratamento contábil adotado:", ["A", "B", "C"],
                                   format_func=lambda x: get_labels(rodada, pecld_m)[x])
                if st.button("✅ Homologar Resolução", use_container_width=True):
                    d[f"voto_r{rodada}"]      = escolha
                    d[f"tempo_voto_r{rodada}"] = time.time()
                    salvar_estado(estado)
                    st.success("Resolução homologada!")
                    st.rerun()
            else:
                st.success(f"📌 Estratégia Adotada: {get_labels(rodada, pecld_m)[voto_atual]}")
                tempos = [(n, estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}"))
                          for n in EMPRESAS
                          if estado["dados_empresas"][n].get(f"voto_r{rodada}") is not None
                          and estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}") is not None]
                qtd_votaram = len(tempos)
                if qtd_votaram >= 1:
                    ranking = [item[0] for item in sorted(tempos, key=lambda x: x[1])]
                    sou_primeiro         = (ranking[0] == nome_interno)
                    sou_ultimo_definitivo= (qtd_votaram == 3 and ranking[-1] == nome_interno)
                    aguardando_mais      = (qtd_votaram < 3 and not sou_primeiro)
                    if sou_primeiro:
                        st.markdown("""<div style='background-color:#c8e6c9;border:1px solid #81c784;color:#1b5e20;
                            padding:10px;border-radius:4px;margin-bottom:8px;font-size:13px;'>
                            ⏱️ <b>Bônus de Agilidade:</b> Sua bancada foi a primeira a homologar! <b>+R$ 0,10</b> na ação.</div>""",
                            unsafe_allow_html=True)
                    elif sou_ultimo_definitivo:
                        st.markdown("""<div style='background-color:#ffcdd2;border:1px solid #ef5350;color:#b71c1c;
                            padding:10px;border-radius:4px;margin-bottom:8px;font-size:13px;'>
                            ⏱️ <b>Penalidade por Atraso:</b> Sua bancada foi a última. <b>-R$ 0,10</b> na ação.</div>""",
                            unsafe_allow_html=True)
                    elif aguardando_mais:
                        st.markdown(f"""<div style='background-color:#fff8e1;border:1px solid #ffd54f;color:#6d4c00;
                            padding:10px;border-radius:4px;margin-bottom:8px;font-size:13px;'>
                            ⏳ <b>Aguardando as demais bancadas...</b> Você foi a <b>{qtd_votaram}ª</b> a votar.</div>""",
                            unsafe_allow_html=True)
                    preco_atual = d["precos"][-1]
                    preco_estimado = round(preco_atual * IMPACTOS.get(rodada, {}).get(voto_atual, 1.0), 2)
                    ajuste_tempo = +0.10 if sou_primeiro else (-0.10 if sou_ultimo_definitivo else 0.0)
                    label_ajuste = (" + R$ 0,10 (bônus)" if sou_primeiro else
                                    " − R$ 0,10 (penalidade)" if sou_ultimo_definitivo else "")
                    preco_fe = round(preco_estimado + ajuste_tempo, 2)
                    variacao = round(preco_fe - preco_atual, 2)
                    sinal    = "▲" if variacao >= 0 else "▼"
                    cor_v    = "#1b5e20" if variacao >= 0 else "#b71c1c"
                    bg_v     = "#e8f5e9" if variacao >= 0 else "#ffebee"
                    brd_v    = "#81c784" if variacao >= 0 else "#ef5350"
                    st.caption(f"Preço atual: R$ {preco_atual:.2f} → Impacto da opção {voto_atual}: R$ {preco_estimado:.2f}{label_ajuste}")
                    st.markdown(f"**{sinal} Estimativa: R$ {preco_fe:.2f} ({variacao:+.2f})**")
                    st.caption("💡 Valor confirmado pelo Gerenciador ao encerrar a rodada.")
                votos_reais = {f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada + 1)}
                exibir_dre(votos_reais, rodada)

        elif rodada == 4:
            st.info("⏳ Aguardando o Apresentador aplicar a auditoria CVM.")
            exibir_dre({f"r{r}": d.get(f"voto_r{r}") for r in range(1, 4)}, 3)

        else:
            preco_abertura = d["precos"][0]; preco_final = d["precos"][-1]
            variacao_total = preco_final - preco_abertura
            pct_total      = (variacao_total / preco_abertura) * 100
            sinal_total    = "▲" if variacao_total >= 0 else "▼"
            cor_total      = "#1b5e20" if variacao_total >= 0 else "#7f0000"
            bg_total       = "#e8f5e9" if variacao_total >= 0 else "#ffebee"
            borda_total    = "#81c784" if variacao_total >= 0 else "#ef5350"
            combo = [d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")]
            qtd_c = combo.count("C"); qtd_b = combo.count("B")
            if qtd_c == 3:   nivel_risco="🔴 CRÍTICO — Manipulação Sistemática"; desc_risco="Autuação máxima aplicada."; cor_r="#7f0000"; bg_r="#ffebee"; brd_r="#c62828"
            elif qtd_c == 2: nivel_risco="🟠 ALTO — Irregularidades Graves"; desc_risco="Penalidade severa aplicada."; cor_r="#6d4c00"; bg_r="#fff8e1"; brd_r="#ffa000"
            elif qtd_c == 1: nivel_risco="🟡 MODERADO — Decisão Oportunista"; desc_risco="Advertência formal registrada."; cor_r="#4a3000"; bg_r="#fffde7"; brd_r="#fdd835"
            elif qtd_b >= 2: nivel_risco="🟢 BAIXO — Boa Governança"; desc_risco="Empresa mantém reputação íntegra."; cor_r="#1b5e20"; bg_r="#e8f5e9"; brd_r="#66bb6a"
            else:            nivel_risco="🔵 NEUTRO — Governança Conservadora"; desc_risco="Transparência total perante auditores."; cor_r="#0d47a1"; bg_r="#e3f2fd"; brd_r="#42a5f5"
            st.markdown("## 🏁 Relatório de Auditoria CVM")
            st.markdown(f"""<div style='border:2px solid {borda_total};background:{bg_total};border-radius:8px;padding:20px;margin-bottom:16px;'>
                <div style='font-size:13px;color:#555;margin-bottom:4px;'>Valor da Ação</div>
                <div style='display:flex;align-items:baseline;gap:12px;'>
                    <span style='font-size:32px;font-weight:900;color:{cor_total};'>R$ {preco_final:.2f}</span>
                    <span style='font-size:18px;color:{cor_total};font-weight:bold;'>{sinal_total} R$ {abs(variacao_total):.2f} ({pct_total:+.1f}%) desde a abertura</span>
                </div>
                <div style='font-size:12px;color:#777;margin-top:4px;'>Preço de abertura: R$ {preco_abertura:.2f}</div>
            </div>""", unsafe_allow_html=True)
            st.markdown(f"""<div style='border:1px solid {brd_r};background:{bg_r};color:{cor_r};
                border-radius:6px;padding:14px 18px;margin-bottom:16px;font-size:13px;'>
                <b style='font-size:15px;'>{nivel_risco}</b><br>{desc_risco}</div>""", unsafe_allow_html=True)
            cores_voto = {"A":("#0d47a1","#e3f2fd","#90caf9"),"B":("#1b5e20","#e8f5e9","#a5d6a7"),"C":("#7f0000","#ffebee","#ef9a9a")}
            st.markdown("**📋 Histórico de Decisões:**")
            cols_votos = st.columns(3)
            for i, r in enumerate([1, 2, 3]):
                v = d.get(f"voto_r{r}") or "—"
                cor_t, bg_v, brd = cores_voto.get(v, ("#333","#f5f5f5","#ccc"))
                with cols_votos[i]:
                    st.markdown(f"""<div style='border:1px solid {brd};background:{bg_v};color:{cor_t};
                        border-radius:6px;padding:10px;text-align:center;font-size:13px;'>
                        <div style='font-size:11px;color:#777;'>Rodada {r}</div>
                        <div style='font-size:22px;font-weight:900;'>{v}</div></div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            exibir_dre({f"r{r}": d.get(f"voto_r{r}") for r in range(1, 4)}, 3)
            plotar_grafico_empresa(estado, nome_interno)

    with aba_jornal_aluno:
        if estado["historico_noticias"]:
            for n_html in estado["historico_noticias"]:
                st.html(n_html)
        else:
            st.info("⏳ Nenhuma notícia publicada neste ciclo.")

    time.sleep(6)
    st.rerun()
