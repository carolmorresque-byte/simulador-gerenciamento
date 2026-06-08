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
# 2. Banco de Dados Global (Memória Central Compartilhada)
# ─────────────────────────────────────────────────────────────────────────────
class BancoDadosMemoria:
    def __init__(self):
        self.rodada_atual = 1
        self.manchete_jornal = None  
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

if not hasattr(db, 'sessoes_ativas'):
    db.sessoes_ativas = set()

if not hasattr(db, 'manchete_jornal'):
    db.manchete_jornal = None

# ─────────────────────────────────────────────────────────────────────────────
# 3. Mapeamentos e Constantes Oficiais
# ─────────────────────────────────────────────────────────────────────────────
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]

EMPRESA_MAP = {
    "α - Empresa Alfa": "Empresa Alfa",
    "β - Empresa Beta": "Empresa Beta",
    "γ - Empresa Gama": "Empresa Gama",
}

IMPACTOS = {
    1: {'A': 0.75, 'B': 0.95, 'C': 1.05},
    2: {'A': 0.40, 'B': 0.82, 'C': 1.143},
    3: {'A': 0.30, 'B': 0.60, 'C': 1.10}
}

LABELS_R1 = {
    'A': '🏦 OPÇÃO A: Lançar em Passivo Financeiro — Encargos no resultado (-R$ 310M). EBITDA: R$ 1.000M | Lucro Líquido cai para R$ 690M.',
    'B': '🏭 OPÇÃO B: Lançar em Ativo Circulante (Estoques) — Juros ativados no estoque. EBITDA: R$ 1.000M | Lucro Líquido estável em R$ 700M.',
    'C': '🏛️ OPÇÃO C: Lançar em Passivo Operacional e Reduzir PDD — Reduz PDD para -R$ 100M. EBITDA sobe para R$ 1.050M | Lucro Líquido vai para R$ 750M.',
}

LABELS_R2 = {
    'A': '📉 OPÇÃO A: Assumir Perda Cambial Imediata — Reconhece o impacto cambial direto na DRE e a desvalorização via provisão de estoque.',
    'B': '⚖️ OPÇÃO B: Dilatar Ativos e Depreciação (CPC 16/23) — Ativa custos extras no estoque e alonga a vida útil dos ativos de 5 para 10 anos.',
    'C': '🎭 OPÇÃO C: Crédito de Incentivo Comercial (Rebate Fake) — Registra descontos verbais futuros de 24 meses como receita imediata.',
}

LABELS_R3 = {
    'A': '✅ OPÇÃO A: Transparência Integral (PECLD) — Registra o calote real de R$ 200M in PDD/PECLD na DRE conforme o CPC 48 (IFRS 9).',
    'B': '🚨 OPÇÃO B: Securitização via FIDC com Deságio — Transfere a carteira para um fundo. Aloca R$ 50M de prejuízo no Financeiro, blindando o EBITDA.',
    'C': '💀 OPÇÃO C: Congelar Provisões e Antecipar Garantias — Omite os R$ 200M em perdas e antecipa R$ 80M de receitas futuras (Brecha CPC 47).',
}

def get_labels(rodada: int) -> dict:
    if rodada == 1: return LABELS_R1
    if rodada == 2: return LABELS_R2
    if rodada == 3: return LABELS_R3
    return LABELS_R1

SENHAS = {
    "🎛️ Painel Apresentador": "mestre123",
    "α - Empresa Alfa":        "alfa",
    "β - Empresa Beta":        "beta",
    "γ - Empresa Gama":        "gama",
}

ACESSO_LIVRE = ["📈 Telão (Bolsa)"]

# ─────────────────────────────────────────────────────────────────────────────
# 3.5. Gerador de Notícias Dinâmicas (GC NEWS)
# ─────────────────────────────────────────────────────────────────────────────
def gerar_manchete_dinamica(rodada: int):
    precos = {nome: db.dados_empresas[nome]["precos"][-1] for nome in EMPRESAS}
    lista_ordenada = sorted(precos.items(), key=lambda x: x[1], reverse=True)
    
    preco_max = lista_ordenada[0][1]
    preco_min = lista_ordenada[-1][1]
    
    líderes = [nome for nome, p in precos.items() if p == preco_max]
    lanternas = [nome for nome, p in precos.items() if p == preco_min]
    
    todos_empatados = (preco_max == preco_min)
    
    txt_lideres = " e ".join(líderes)
    txt_lanternas = " e ".join(lanternas)

    if rodada == 1:
        topo_manchete = f"FENÔMENO FINANCEIRO! {txt_lideres} dribla os juros altos e dispara no topo do mercado!"
        topo_texto = f"SÃO PAULO — Em meio à forte retração do varejo, a estratégia de estruturação de balanço da {txt_lideres} blindou suas ações contra o avanço das taxas de juros."
        baixo_manchete = f"ALERTA VERMELHO! {txt_lanternas} bate de frente com os covenants e amarga a lanterna!"
        baixo_texto = f"SÃO PAULO — A falta de flexibilidade contábil custou caro. A {txt_lanternas} viu seus encargos financeiros explodirem na DRE, afundando a confiança do mercado."
    elif rodada == 2:
        topo_manchete = f"A PROVA DE BALAS! {txt_lideres} neutraliza o dólar a R$ 6,50 e decola de forma genial!"
        topo_texto = f"SÃO PAULO — Enquanto o setor de importados virou uma zona de guerra cambial, a {txt_lideres} mostrou resiliência estratégica absurda, acelerando forte na bolsa de valores."
        baixo_manchete = f"ENGOLINDO ÁGUA! Explosão do câmbio faz as ações da {txt_lanternas} derreterem no porto!"
        baixo_texto = f"SÃO PAULO — Sem colete salva-vidas contra a disparada do dólar, a {txt_lanternas} foi atropelada pelos custos aduaneiros, disparando saídas de acionistas."
    else:
        topo_manchete = f"MINA DE OURO CONTÁBIL! {txt_lideres} ignora calotes e reporta lucros históricos!"
        topo_texto = f"SÃO PAULO — O mercado financeiro está em puro delírio coletivo! Mesmo com a inadimplência do varejo disparando, a {txt_lideres} conseguiu apresentar um EBITDA astronômico."
        baixo_manchete = f"NAUFRÁGIO DO CREDIÁRIO! {txt_lanternas} assume o rombo do calote e afunda sozinha!"
        baixo_texto = f"SÃO PAULO — Realidade nua e crua. Ao registrar integralmente o calote de R$ 200 milhões nas contas a receber, a {txt_lanternas} viu seu valuation derreter."

    if todos_empatados:
        topo_manchete = "MERCADO EM ESTABILIDADE ABSOLUTA: Setor caminha em bloco!"
        topo_texto = "SÃO PAULO — Sem distinção de performance, as empresas do setor adotaram posturas que mantiveram as cotações rigorosamente alinhadas."
        baixo_manchete = "DISPUTA ACIRRADA: Margens idênticas congelam as posições na bolsa."
        baixo_texto = "SÃO PAULO — Analistas apontam que a falta de dispersão nas escolhas das diretorias eliminou qualquer vantagem competitiva nesta rodada."

    html_jornal = f"""
    <div style="background-color: #ffffff; border: 1px solid #ddd; font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
        <div style="background-color: #cc0000; color: #ffffff; display: flex; justify-content: space-between; align-items: center; padding: 12px 20px;">
            <div style="font-size: 22px; font-weight: bold;">☰</div>
            <div style="font-size: 24px; font-weight: 900; letter-spacing: 1px;">GC NEWS</div>
            <div style="font-size: 20px;">🔍</div>
        </div>
        <div style="padding: 20px 15px;">
            <div style="background-color: #639a67; color: #ffffff; padding: 12px 15px; border-radius: 2px; font-size: 16px; font-weight: bold; text-transform: uppercase; line-height: 1.3;">
                {topo_manchete}
            </div>
            <div style="display: flex; align-items: center; margin-top: 8px; margin-bottom: 25px; gap: 10px;">
                <div style="flex: 1; border: 1px solid #cccccc; padding: 12px; border-radius: 2px; min-height: 80px; background-color: #fafafa; display: flex; align-items: center;">
                    <p style="font-size: 12.5px; color: #333333; margin: 0; text-align: justify; line-height: 1.4;">
                        <span style="font-weight: bold; text-transform: uppercase;">{topo_texto.split(' — ')[0]}</span> — {topo_texto.split(' — ')[1] if ' — ' in topo_texto else topo_texto}
                    </p>
                </div>
                <div style="font-size: 35px; text-align: center; width: 65px; line-height: 1;">
                    🌲<br><span style="font-size: 24px; color: #2ecc71; font-weight: bold;">▲</span>
                </div>
            </div>
            <div style="background-color: #ff5c5c; color: #ffffff; padding: 12px 15px; border-radius: 2px; font-size: 16px; font-weight: bold; text-transform: uppercase; line-height: 1.3;">
                {baixo_manchete}
            </div>
            <div style="display: flex; align-items: center; margin-top: 8px; margin-bottom: 15px; gap: 10px;">
                <div style="flex: 1; border: 1px solid #cccccc; padding: 12px; border-radius: 2px; min-height: 80px; background-color: #fafafa; display: flex; align-items: center;">
                    <p style="font-size: 12.5px; color: #333333; margin: 0; text-align: justify; line-height: 1.4;">
                        <span style="font-weight: bold; text-transform: uppercase;">{baixo_texto.split(' — ')[0]}</span> — {baixo_texto.split(' — ')[1] if ' — ' in baixo_texto else baixo_texto}
                    </p>
                </div>
                <div style="font-size: 35px; text-align: center; width: 65px; line-height: 1;">
                    📉<br><span style="font-size: 24px; color: #e74c3c; font-weight: bold;">▼</span>
                </div>
            </div>
            <div style="font-size: 11px; font-weight: bold; color: #222222; border-top: 1px solid #ddd; padding-top: 12px; margin-top: 25px; letter-spacing: 0.5px;">
                ATENÇÃO INVESTIDORES! MERCADO EM TEMPO REAL.
            </div>
        </div>
    </div>
    """
    return html_jornal

# ─────────────────────────────────────────────────────────────────────────────
# 4. Motor de Cálculo Dinâmico e Cumulativo da DRE
# ─────────────────────────────────────────────────────────────────────────────
def calcular_dre_dinamico(votos: dict) -> dict:
    receita      = 20_000_000_000.0
    cmv          = -16_500_000_000.0
    pdd          = -150_000_000.0
    depreciacao  = -150_000_000.0
    outras_desp  = -2_200_000_000.0
    juros        = -300_000_000.0
    
    nota_pdd = "Provisão normal de 3% sobre a carteira ativa."
    nota_dep = "Depreciação linear padrão de instalações e frotas."
    nota_jur = "Serviço de juros sobre dívidas estruturadas."
    
    v1 = votos.get("r1")
    if v1 == 'A':
        juros = -310_000_000.0
        nota_jur = "Despesa financeira de R$ 310M computada integralmente."
    elif v1 == 'B':
        nota_jur = "R$ 10M de juros do Risco Sacado capitalizados no Ativo (Estoques)."
    elif v1 == 'C':
        pdd = -100_000_000.0
        nota_pdd = "⚠️ PDD suprimida artificialmente para R$ 100M para blindar covenants."
        nota_jur = "⚠️ Custos de financiamento ocultados do Resultado Financeiro."
        
    v2 = votos.get("r2")
    if v2 == 'A':
        cmv -= 30_000_000.0
        nota_pdd += " | Provisão realizada para obsolescência de estoques encalhados."
    elif v2 == 'B':
        depreciacao += 20_000_000.0
        nota_dep = "⚠️ Manobra CPC 23: Extensão de vida útil reduziu despesa do trimestre pela metade."
    elif v2 == 'C':
        nota_jur += " | ⚠️ Ativação de R$ 30M fictícios no Ativo sob rubrica de Incentivo Comercial."
        
    v3 = votos.get("r3")
    if v3 == 'A':
        pdd -= 200_000_000.0
        nota_pdd += " | 🚨 Ajuste severo de PECLD (CPC 48) refletindo a inadimplência de 12%."
    elif v3 == 'B':
        juros -= 50_000_000.0
        nota_jur += " | Deságio comercial de R$ 50M lançado integralmente no Resultado Financeiro."
    elif v3 == 'C':
        receita += 80_000_000.0
        nota_pdd += " | 🚨 Omissão dolosa de R$ 200M em perdas reais."
        nota_jur += " | ⚠️ Violação do CPC 47: Receita plurianual de Garantia Estendida trazida a valor presente."

    lucro_bruto = receita + cmv
    ebitda = lucro_bruto + pdd + depreciacao + outras_desp
    lucro_liq = ebitda + juros
    
    return {
        "receita": receita, "cmv": abs(cmv), "lucro_bruto": lucro_bruto,
        "pdd": abs(pdd), "depreciacao": abs(depreciacao), "outras_desp": abs(outras_desp),
        "ebitda": ebitda, "juros": abs(juros), "lucro_liq": lucro_liq,
        "nota_pdd": nota_pdd, "nota_dep": nota_dep, "nota_jur": nota_jur
    }

def exibir_dre(votos_empresa: dict, rodada_exibida: int):
    dre = calcular_dre_dinamico(votos_empresa)
    st.markdown(f"### 📋 DRE Acumulada — Demonstrativo de Resultados (Exercício {rodada_exibida})")

    def fmt(v, negativo=False):
        sinal = "-" if negativo else ""
        return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

    linhas = [
        ("(=) Receita Bruta de Vendas",            fmt(dre["receita"]),           False),
        ("(-) Custo das Mercadorias (CMV)",         fmt(dre["cmv"],   True),        False),
        ("(=) Lucro Bruto Operacional",             fmt(dre["lucro_bruto"]),       True),
        ("(-) Provisão para Calotes (PDD/PECLD)",   fmt(dre["pdd"],   True),        False),
        ("(-) Depreciação de Lojas/Ativos",         fmt(dre["depreciacao"], True), False),
        ("(-) Outras Despesas Operacionais",        fmt(dre["outras_desp"], True), False),
        ("(=) EBITDA APURADO",                     fmt(dre["ebitda"]),            True),
        ("(-) Result. Financeiro (Dívidas/Juros)",  fmt(dre["juros"],  True),      False),
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

    with st.expander("📝 Notas explicativas das escolhas contábeis acumuladas"):
        st.markdown(f"**Créditos de Liquidação Duvidosa:** {dre['nota_pdd']}")
        st.markdown(f"**Imobilizado & Depreciação:** {dre['nota_dep']}")
        st.markdown(f"**Estrutura de Capital & Financiamento:** {dre['nota_jur']}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Auditoria Baseada no Novo Score GR Sem Colisões (A=0, B=2, C=3)
# ─────────────────────────────────────────────────────────────────────────────
def aplicar_auditoria_final():
    PESOS_GR = {'A': 0, 'B': 2, 'C': 3}
    for nome, d in db.dados_empresas.items():
        votos = [d["voto_r1"], d["voto_r2"], d["voto_r3"]]
        score_gr = sum(PESOS_GR.get(v, 0) for v in votos if v is not None)
        d["score_gr"] = score_gr
        
        if score_gr == 0:
            d["status"] = "🏆 EXCELÊNCIA ÉTICA (Integridade Absoluta)"
            d["noticia_r4"] = "Score GR: 0. Transparência total e conformidade estrita com o IFRS. Mercado premia com valuation premium!"
        elif score_gr in [2, 4]:
            d["status"] = "⚖️ PRÁTICA LEGAL CONSERVADORA"
            d["noticia_r4"] = f"Score GR: {score_gr}. Uso pontual de estimativas legais. Governança dentro dos limites de mercado."
        elif score_gr == 6:
            d["status"] = "⚠️ ESTRATEGISTA CONTÁBIL NO LIMITE"
            d["noticia_r4"] = "Score GR: 6. Três escolhas consecutivas de gerenciamento dentro da lei (Opção B). Legal, mas acende alertas na auditoria pela falta de transparência."
        elif score_gr in [3, 5]:
            d["status"] = "🚨 INCONFORMIDADE MATERIAL (1 Fraude)"
            d["noticia_r4"] = f"Score GR: {score_gr}. Uma fraude estrutural grave (Opção C) foi detectada no histórico. CVM instaurou processo sancionador."
        elif score_gr in [7, 8]:
            d["status"] = "❌ MANIPULAÇÃO SISTÊMICA (2 Fraudes)"
            d["noticia_r4"] = f"Score GR: {score_gr}. Duas fraudes contábeis gravíssimas para ocultar perdas operacionais. Confiança do mercado derreteu."
        elif score_gr == 9:
            d["status"] = "🚔 FRAUDE ESTRUTURAL COMPLETA (3 Fraudes)"
            d["noticia_r4"] = "Score GR: 9. O colapso total. Todas as escolhas foram fraudes contábeis dolosas. Destituição do conselho e acionamento da polícia federal."

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
            if st.button("📈 Acessar Telão", use_container_width=True):
                st.session_state["usuario_logado"] = perfil_escolhido_raw
                st.rerun()
        else:
            senha_digitada = st.text_input("Senha:", type="password")
            if st.button("🚪 Autenticar"):
                if senha_digitada == SENHAS[perfil_escolhido_raw]:
                    st.session_state["usuario_logado"] = perfil_escolhido_raw
                    st.session_state["telao_origem"] = perfil_escolhido_raw
                    nome_interno = EMPRESA_MAP.get(perfil_escolhido_raw)
                    if nome_interno:
                        db.sessoes_ativas.add(nome_interno)
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
    st.stop()

perfil = st.session_state["usuario_logado"]
nome_interno = EMPRESA_MAP.get(perfil)
eh_empresa   = nome_interno is not None

with st.sidebar:
    st.markdown(f"**Logado como:** {perfil}")
    st.markdown("---")
    if eh_empresa:
        if st.button("📈 Ver Telão Global", use_container_width=True):
            st.session_state["telao_origem"] = perfil
            st.session_state["usuario_logado"] = "📈 Telão (Bolsa)"
            st.rerun()
    if st.button("← Página de Seleção", use_container_width=True):
        if eh_empresa and nome_interno in db.sessoes_ativas:
            db.sessoes_ativas.remove(nome_interno)
        st.session_state["telao_origem"] = None
        st.session_state["usuario_logado"] = None
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO ALUNO (Com Sistema de Abas Integrado)
# ─────────────────────────────────────────────────────────────────────────────
if eh_empresa:
    d = db.dados_empresas[nome_interno]
    rodada = db.rodada_atual

    st.markdown(f"## 🏢 {perfil} | Exercício {rodada if rodada <= 3 else 'Fim'}")
    
    # Abas para o Aluno navegar sem perder o painel de voto
    aba_voto, aba_jornal_aluno = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mercado (GC NEWS)"])

    NARRATIVAS = {
        1: """### 🏭 1: O DILEMA DO RISCO SACADO 
A empresa encerrou o período sob severas pressões de liquidez em seu fluxo de caixa operacional. Para preservar o ciclo de abastecimento de suas lojas, a companhia realizou a aquisição de **R$ 150 milhões** em eletroeletrônicos junto a indústrias parceiras. 

Sem caixa livre para liquidar esses passivos comerciais nas datas originais de vencimento, a Diretoria Financeira estruturou uma operação de **Risco Sacado** junto ao Banco Épsilon. O banco quitou as faturas dos fornecedores à vista e concedeu prazo adicional à empresa, cobrando **R$ 10 milhões** em juros embutidos na transação.  

A manutenção dessa estrutura de crédito tornou-se essencial para a continuidade do negócio. Contudo, os contratos de financiamento vigentes contêm a seguinte restrição:  

> **Cláusula 7.2 (Covenant Financeiro):** *A Companhia deve manter o índice Dívida Líquida/EBITDA igual ou inferior a 3,0x ao final de cada trimestre, sob pena de vencimento antecipado das dívidas e bloqueio de novos créditos.*

Para piorar o cenário, o Banco Central aumentou fortemente a taxa básica de juros do país neste trimestre. Com o crédito mais caro, os consumidores sumiram das lojas e as vendas gerais de eletrodomésticos despencaram 15%. Esse tombo inesperado esmagou a margem operacional, empurrando o EBITDA real para muito abaixo do esperado pelo mercado.""",
        
        2: """### 📰 RODADA 2: A CRISE DO DÓLAR
A empresa fechou um pedido de 200 mil smartphones de última geração com indústrias parceiras nos EUA e na China. O acordo foi feito em **"moeda aberta"** (sem proteção de hedge), pois o câmbio estava estável em R$ 5,00. O pagamento ocorreria no desembaraço aduaneiro no porto, 60 dias após o embarque.  

No trânsito marítimo, os EUA entram repentinamente em um conflito militar internacional. O mercado entra em pânico e o dólar dispara de **R$ 5,00 para R$ 6,50** em apenas dois meses.  

**Problema: Explosão no Custo de Importação (CMV)**  
O lote orçado por R$ 100 milhões agora custa **R$ 130 milhões** para ser retirado do porto. Um aumento surpresa de R$ 30 milhões por falha na gestão de risco cambial.  

**Greve e Lentidão na Alfândega:** O estoque fica encalhado no porto por 45 dias além do previsto, gerando custos extras de armazenagem (*demurrage*) e atrasando as lojas. Tentando reaver a margem, a diretoria aumentou o preço nas lojas em 30%. O resultado foi imediato: **as vendas travam** e aparelhos acumulam poeira.""",
        
        3: """### 🚨 RODADA 3: O DESAFIO DA INSOLVÊNCIA
Os efeitos prolongados da guerra internacional e a política monetária severa adotada pelo Banco Central resultaram em uma recessão profunda. A elevação do desemprego e a retração da renda deterioraram a capacidade de pagamento das famílias.  

Como reflexo direto, a taxa de inadimplência da carteira de crédito próprio da companhia (Private Label e crediário), historicamente controlada em 3%, **escalou para 12%**.  

**O Desafio Contábil e Patrimonial:** Os saldos em Contas a Receber sofreram severa perda de recuperabilidade. Em conformidade estrita com os critérios de perdas de crédito esperadas determinados pelo **CPC 48 (IFRS 9)**, a companhia é obrigada a reconhecer o aumento do risco de crédito de forma imediata.  

A adequação patrimonial exige o provisionamento de uma despesa de PECLD de **R$ 200 milhões** na DRE. O lançamento integral desse montante anularia o EBITDA do período, evidenciando insolvência técnica e forçando uma severa revisão da auditoria."""
    }

    with aba_voto:
        if rodada <= 3:
            voto_atual = d[f"voto_r{rodada}"]

            if voto_atual is None:
                st.markdown(f"### 📋 Deliberação Estratégica — Exercício {rodada}")

                col_prob, col_dre = st.columns([1.1, 0.9], gap="large")
                with col_prob:
                    if rodada in NARRATIVAS:
                        with st.container(border=True):
                            st.markdown(NARRATIVAS[rodada])
                with col_dre:
                    votos_simulados = {f"r{r}": d[f"voto_r{r}"] for r in range(1, rodada)}
                    votos_simulados[f"r{rodada}"] = 'B'
                    exibir_dre(votos_simulados, rodada)

                st.markdown("---")
                st.markdown("### 🗳️ Sua Decisão Colegiada")
                labels_rodada = get_labels(rodada)
                escolha = st.radio("Selecione o tratamento contábil adotado:", ["A", "B", "C"], format_func=lambda x: labels_rodada[x])
                
                if st.button("✅ Homologar Resolução", use_container_width=True):
                    d[f"voto_r{rodada}"] = escolha
                    d["tempo_voto"] = time.time()  
                    st.success("Resolução registrada com sucesso! Aguarde o encerramento do mercado.")
                    st.rerun()

            else:
                st.success(f"✅ Resolução homologada: {get_labels(rodada)[voto_atual]}")
                st.markdown("---")
                votos_reais = {f"r{r}": d[f"voto_r{r}"] for r in range(1, rodada + 1)}
                exibir_dre(votos_reais, rodada)
                st.markdown("---")
                st.info("⏳ Aguardando o apresentador encerrar a rodada comercial...")
                st.markdown("""<meta http-equiv="refresh" content="5">""", unsafe_allow_html=True)

        else:
            st.markdown("## 🏁 Resultado Final da sua Corporação")
            st.markdown(f"**Veredito da Auditoria:** {d['status']}")
            if d["noticia_r4"]:
                st.warning(d["noticia_r4"])
            st.markdown("---")
            
            votos_finais = {f"r{r}": d[f"voto_r{r}"] for r in range(1, 4)}
            exibir_dre(votos_finais, 3)

    with aba_jornal_aluno:
        if db.manchete_jornal:
            st.markdown("### 📰 Edição Atual do GC NEWS")
            st.html(db.manchete_jornal)
        else:
            st.info("ℹ️ Nenhuma manchete publicada ainda. O jornal impresso sairá ao fim do primeiro trimestre.")

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO APRESENTADOR 
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "🎛️ Painel Apresentador":
    st.title("🎛️ Painel de Comando da Mesa de Operações")
    rodada = db.rodada_atual

    aba_controle, aba_espelho_mercado, aba_espelho_midia = st.tabs([
        "⚙️ Controle de Rodada", 
        "📈 Espelho do Telão", 
        "📰 Espelho da Mídia"
    ])

    with aba_controle:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            texto_botao = f"▶ Fechar Rodada {rodada} e Avançar" if rodada < 3 else "🏁 Fechar Rodada 3 e Aplicar Auditoria Final"
            if rodada <= 3 and st.button(texto_botao, use_container_width=True, type="primary"):
                
                votos_da_rodada = []
                for nome in EMPRESAS:
                    if db.dados_empresas[nome][f"voto_r{rodada}"] is not None:
                        votos_da_rodada.append((nome, db.dados_empresas[nome]["tempo_voto"]))
                
                ranking_velocidade = [item[0] for item in sorted(votos_da_rodada, key=lambda x: x[1] if x[1] else 0)]
                
                for nome in EMPRESAS:
                    voto = db.dados_empresas[nome][f"voto_r{rodada}"]
                    if voto:
                        preco_base = db.dados_empresas[nome]["precos"][-1] * IMPACTOS[rodada][voto]
                        
                        ajuste_tempo = 0.0
                        if len(ranking_velocidade) >= 1 and nome == ranking_velocidade[0]:
                            ajuste_tempo = 0.10  
                        elif len(ranking_velocidade) == 3 and nome == ranking_velocidade[-1]:
                            ajuste_tempo = -0.10 
                            
                        db.dados_empresas[nome]["precos"].append(round(preco_base + ajuste_tempo, 2))
                        db.dados_empresas[nome]["tempo_voto"] = None  

                db.manchete_jornal = gerar_manchete_dinamica(rodada)

                if db.rodada_atual == 3:
                    aplicar_auditoria_final()
                
                db.rodada_atual += 1
                st.rerun()

        with col3:
            if st.button("📈 Ir para o Telão →", use_container_width=True):
                st.session_state["usuario_logado"] = "📈 Telão (Bolsa)"
                st.rerun()

        with col2:
            if st.button("🔄 Reset Total do Jogo", use_container_width=True):
                db.rodada_atual    = 1
                db.sessoes_ativas  = set()
                db.manchete_jornal = None 
                for nome in EMPRESAS:
                    db.dados_empresas[nome] = {
                        "precos": [20.0], "voto_r1": None, "voto_r2": None,
                        "voto_r3": None, "voto_r4": None, "tempo_voto": None,
                        "status": "Operando", "noticia_r4": "", "score_gr": 0,
                    }
                st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Monitoramento e Score de Governança (Mesa de Controle)")
        
        PESOS_TEMPORARIOS = {'A': 0, 'B': 2, 'C': 3}
        for nome in EMPRESAS:
            voto = db.dados_empresas[nome].get(f"voto_r{min(rodada, 3)}")
            status_voto = "📥 CONCLUÍDO" if voto else "⏳ ANALISANDO..."
            
            votos_parciais = [db.dados_empresas[nome]["voto_r1"], db.dados_empresas[nome]["voto_r2"], db.dados_empresas[nome]["voto_r3"]]
            score_parcial = sum(PESOS_TEMPORARIOS.get(v, 0) for v in votos_parciais if v is not None)
            
            if voto:
                st.success(f"**{nome}** — {status_voto} | Cotação Ativa: **R$ {db.dados_empresas[nome]['precos'][-1]:.2f}** | Score GR: `{score_parcial}`")
            else:
                st.error(f"**{nome}** — {status_voto} | Cotação Ativa: **R$ {db.dados_empresas[nome]['precos'][-1]:.2f}** | Score GR: `{score_parcial}`")

    with aba_espelho_mercado:
        st.markdown("### 📊 Cotações Atuais do Mercado")
        c1, c2, c3 = st.columns(3)
        for i, nome in enumerate(EMPRESAS):
            with [c1, c2, c3][i]:
                p_atual = db.dados_empresas[nome]["precos"][-1]
                st.metric(label=nome, value=f"R$ {p_atual:.2f}")
        
        st.markdown("---")
        st.markdown("##### Histórico de Evolução das Ações")
        fig_mestre, ax_mestre = plt.subplots(figsize=(10, 3.5))
        fig_mestre.patch.set_facecolor('#0e1117')
        ax_mestre.set_facecolor('#1e222b')
        ax_mestre.tick_params(colors='white')
        ax_mestre.grid(True, color='#444', linestyle='--', alpha=0.5)
        
        cores = {"Empresa Alfa": "#3498db", "Empresa Beta": "#e67e22", "Empresa Gama": "#2ecc71"}
        for nome in EMPRESAS:
            hist = db.dados_empresas[nome]["precos"]
            ax_mestre.plot(range(len(hist)), hist, marker='o', linewidth=2, color=cores.get(nome, "#fff"), label=nome)
        ax_mestre.legend()
        st.pyplot(fig_mestre)

    with aba_espelho_midia:
        if db.manchete_jornal:
            st.markdown("### 📰 Edição Atual Publicada no GC NEWS")
            st.html(db.manchete_jornal)
        else:
            st.info("ℹ️ O jornal será gerado automaticamente assim que a primeira rodada for encerrada.")

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO TELÃO
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📈 Telão (Bolsa)":
    st.title("📈 Painel Geral do Mercado de Capitais")
    st.markdown("""<meta http-equiv="refresh" content="3">""", unsafe_allow_html=True)

    telao_origem = st.session_state.get("telao_origem")
    if telao_origem:
        if st.button("← Voltar para o meu painel", use_container_width=True):
            st.session_state["usuario_logado"] = telao_origem
            st.rerun()

    st.markdown("---")
    
    aba_mercado, aba_jornal = st.tabs(["📈 Cotações e Gráficos", "📰 GC NEWS - Últimas Notícias"])

    with aba_mercado:
        col1, col2, col3 = st.columns(3)
        
        for i, nome in enumerate(EMPRESAS):
            with [col1, col2, col3][i]:
                preco_atual = db.dados_empresas[nome]["precos"][-1]
                st.metric(label=nome, value=f"R$ {preco_atual:.2f}")
                
                if db.rodada_atual <= 3:
                    if preco_atual > 21.0:
                        st.success("🪙 **Status:** Lucro Exponencial! (Ouro Branco)")
                    elif preco_atual >= 14.0:
                        st.warning("🍬 **Status:** Estabilidade! (Sonho de Valsa)")
                    else:
                        st.error("🍫 **Status:** Risco de Liquidação! (1 Bis)")
                else:
                    status_final = db.dados_empresas[nome]["status"]
                    score_final = db.dados_empresas[nome]["score_gr"]
                    st.markdown(f"**Auditoria:** {status_final}")
                    st.markdown(f"**Score de Risco Contábil:** `{score_final} Pts`")
                    
                    if score_final == 0:
                        st.info("🍯 **Prêmio:** Pão de Mel com Certificado!")
                    elif score_final in [2, 4, 6]:
                        st.warning("🍬 **Prêmio:** 1 Bala azeda.")
                    else:
                        st.error("💀 **Prêmio:** Falência decretada.")

        st.markdown("<br>##### Histórico de Desempenho Contínuo", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(10, 3))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1e222b')
        ax.tick_params(colors='white')
        ax.grid(True, color='#444', linestyle='--', alpha=0.5)
        
        cores = {"Empresa Alfa": "#3498db", "Empresa Beta": "#e67e22", "Empresa Gama": "#2ecc71"}
        for nome in EMPRESAS:
            historico = db.dados_empresas[nome]["precos"]
            ax.plot(range(len(historico)), historico, marker='o', linewidth=2.5, color=cores.get(nome, "#fff"), label=nome)
        
        ax.set_xticks(range(4))
        ax.set_xticklabels(['Abertura', 'Ex. 1', 'Ex. 2', 'Ex. 3'][:len(historico)])
        ax.legend()
        st.pyplot(fig)

    with aba_jornal:
        if db.manchete_jornal:
            st.markdown("### 🚨 PLANTÃO DE NOTÍCIAS COMENTADO")
            st.html(db.manchete_jornal)
        else:
            st.info("⏳ Aguardando o encerramento do primeiro trimestre para publicação dos relatórios de mídia...")
