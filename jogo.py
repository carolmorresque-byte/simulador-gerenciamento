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

if not hasattr(db, 'sessoes_ativas'):
    db.sessoes_ativas = set()
if not hasattr(db, 'historico_noticias'):
    db.historico_noticias = []

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
            'A': f'OPÇÃO A: Transparência Integral (PECLD) — Registra o calote real de R$ {pecld_m:,.0f}M na DRE conforme o CPC 48 (IFRS 9).'.replace(",", "."),
            'B': 'OPÇÃO B: Securitização via FIDC com Deságio — Transfere a carteira para um fundo. Aloca R$ 50M de prejuízo no Financeiro, blindando o EBITDA.',
            'C': 'OPÇÃO C: Congelar Provisões e Antecipar Garantias — Omite as perdas e antecipa R$ 80M de receitas futuras (Brecha CPC 47).',
        }
    return LABELS_R1

NARRATIVAS = {
    1: """### 🏭 RODADA 1: RISCO SACADO E COVENANTS FINANCEIROS
**Cenário:** A empresa enfrenta pressões de liquidez e, para manter suas operações, utilizou uma estrutura de risco sacado com o Banco Épsilon. Essa operation antecipa o recebimento para fornecedores estratégicos e estende o prazo de pagamento da companhia (com juros de R$ 10MM), evitando o desabastecimento.

O principal problema é o impacto nos covenants financeiros:
*   **Situação Atual:** O índice Dívida Líquida/EBITDA está em 2,9x (o limite contratual é 3,0x).
*   **O Risco:** Se o risco sacado for reclassificado de passivo comercial para dívida financeira, o índice salta para 4,2x. Isso causará o vencimento antecipado das dívidas e travará novos créditos.

**Sua missão:** Definir a classificação contábil dessa operação, ponderando a realidade técnica contra o risco de quebra de contrato e o conflito de interesses na remuneração.""",
    
    2: """### 📰 RODADA 2: A CRISE DO DÓLAR E OS CONTRATOS DE IMPORTAÇÃO
**Cenário:** A empresa enfrenta uma crise severa devido à falta de proteção cambial (*hedge*) e ao repasse excessivo de custos ao consumidor.

*   **Estouro no Orçamento:** A alta do dólar (de R$ 5,00 para R$ 6,50) causada por um conflito militar elevou o custo de importação de 200 mil smartphones de R$ 100 milhões para R$ 130 milhões.
*   **Gargalo Logístico:** Uma lentidão na alfândega reteve os produtos por 45 dias extras, gerando multas de armazenagem (*demurrage*) e atrasando as vendas.
*   **Vendas Travadas:** A tentativa de repassar o prejuízo aumentando os preços em 30% paralisou as vendas, encalhou os aparelhos e gerou custos de obsolescência.

A diretoria se reúne em caráter de urgência para definir a manobra orçamentária."""
}

# ─────────────────────────────────────────────────────────────────────────────
# 3.5. Gerador de Notícias Dinâmicas (Foco Exclusivo em Cotações e Oscilações)
# ─────────────────────────────────────────────────────────────────────────────
def gerar_manchete_dinamica(rodada_encerrada: int):
    # Pega o preço atual (pós-rodada) e o do mês anterior (antes do impacto)
    dados_fechamento = {}
    for nome in EMPRESAS:
        historico = db.dados_empresas[nome]["precos"]
        atual = historico[-1]
        anterior = historico[-2] if len(historico) > 1 else 20.0
        variacao = atual - anterior
        dados_fechamento[nome] = {"atual": atual, "anterior": anterior, "var": variacao}

    lista_ordenada = sorted(dados_fechamento.items(), key=lambda x: x[1]["atual"], reverse=True)
    
    lider_nome, lider_dados = lista_ordered[0]
    lanterna_nome, lanterna_dados = lista_ordered[-1]
    
    todos_empatados = (lider_dados["atual"] == lanterna_dados["atual"])
    
    topo_manchete, topo_texto = "", ""
    baixo_manchete, baixo_texto = "", ""

    # Helper para formatar a variação de preço
    def fmt_var(valor):
        return f"+R$ {valor:.2f}" if valor >= 0 else f"-R$ {abs(valor):.2f}"

    # --- RODADA 1: MAR / NAVEGAÇÃO ---
    if rodada_encerrada == 1:
        if todos_empatados:
            topo_manchete = "MAR CALMO: EMPRESAS REGISTRAM EQUILÍBRIO ABSOLUTO NO SETOR"
            topo_texto = f"SÃO PAULO — Em um mês de águas tranquilas, todas as companhias fecharam pareadas em R$ {lider_dados['atual']:.2f}. Analistas apontam que a ausência de volatilidade refletiu estratégias idênticas de tesouraria."
        else:
            topo_manchete = f"MAR EM FÚRIA: {lider_nome} SURFA ONDA DE VALORIZAÇÃO E SOBE {fmt_var(lider_dados['var'])}!"
            topo_texto = f"SÃO PAULO — Enquanto o setor enfrentava forte maremoto regulatório, a agilidade e a estratégia de mercado da {lider_nome} impulsionaram o papel, saindo de R$ {lider_dados['anterior']:.2f} para R$ {lider_dados['atual']:.2f} neste mês."
            
            baixo_manchete = f"NAUFRÁGIO: {lanterna_nome} ENTRA EM REDEMOINHO E PERDE {fmt_var(lanterna_dados['var'])}"
            baixo_texto = f"SÃO PAULO — Investidores puniram a lentidão institucional e a engenharia patrimonial da {lanterna_nome}. O papel colapsou perante o mês anterior, derretendo para o valor de tela de R$ {lanterna_dados['atual']:.2f}."

    # --- RODADA 2: CORRIDA / FÓRMULA 1 ---
    elif rodada_encerrada == 2:
        if todos_empatados:
            topo_manchete = "SAFETY CAR NA PISTA: GRID REPETE FECHAMENTO DO MÊS ANTERIOR"
            topo_texto = f"SÃO PAULO — Sem ultrapassagens no pregão, o mercado de varejo operou sob bandeira amarela. Os ativos congelaram em R$ {lider_dados['atual']:.2f} com variação nula entre as concorrentes."
        else:
            topo_manchete = f"GP DA TESOURARIA: {lider_nome} METE O PÉ NO ACELERADOR E SALTA PARA R$ {lider_dados['atual']:.2f}!"
            topo_texto = f"SÃO PAULO — Com uma arrancada agressiva nos boxes da governança, a {lider_nome} registrou uma espetacular alta de {fmt_var(lider_dados['var'])} em relação ao mês anterior, assumindo isolada a liderança do grid."
            
            baixo_manchete = f"RODOU NA CURVA: {lanterna_nome} PERDE TRAÇÃO NO MERCADO FINANCEIRO"
            baixo_texto = f"SÃO PAULO — Após manobras arriscadas na precificação interna, a {lanterna_nome} viu seus papéis perderem {fmt_var(lanterna_dados['var'])} comparado ao fechamento passado, cruzando a linha de chegada a R$ {lanterna_dados['atual']:.2f}."

    # --- RODADA 3: BOXE / COMBATE ---
    else:
        if todos_empatados:
            topo_manchete = "GONGADO: ÚLTIMO ROUND TERMINA EM EMPATE OPERACIONAL"
            topo_texto = f"SÃO PAULO — O combate contra a crise macroeconômica terminou sem um vencedor claro na bolsa. Todas as bancadas resistiram nas cordas e fecharam cotadas em R$ {lider_dados['atual']:.2f}."
        else:
            topo_manchete = f"NOCAUTE NA BOLSA: {lider_nome} SEGURA O CINTURÃO COM DISPARADA DE {fmt_var(lider_dados['var'])}!"
            topo_texto = f"SÃO PAULO — Em um fechamento histórico, a {lider_nome} esquivou-se dos riscos de mercado e viu suas ações saltarem do patamar anterior de R$ {lider_dados['anterior']:.2f} para incríveis R$ {lider_dados['atual']:.2f}."
            
            baixo_manchete = f"DIRETO NO QUEIXO: {lanterna_nome} CAI À LONA E REGISTRA QUEDA DE {fmt_var(lanterna_dados['var'])}"
            baixo_texto = f"SÃO PAULO — Sem forças para rebater o impacto dos números consolidados na DRE, a {lanterna_nome} sofreu uma severa fuga de capitais. Os papéis despencaram para R$ {lanterna_dados['atual']:.2f} no encerramento do ciclo."

    html_jornal = f"""
    <div style="background-color: #ffffff; border: 1px solid #ddd; font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto 20px auto; box-shadow: 0 4px 10px rgba(0,0,0,0.15); border-radius: 4px; overflow: hidden;">
        <div style="background-color: #cc0000; color: #ffffff; display: flex; justify-content: space-between; align-items: center; padding: 12px 20px;">
            <div style="font-size: 24px; font-weight: 900; letter-spacing: 1px;">GC NEWS</div>
            <div style="font-size: 12px; font-weight: bold; background: rgba(0,0,0,0.2); padding: 4px 8px; border-radius: 4px;">EXERCÍCIO {rodada_encerrada}</div>
        </div>
        <div style="padding: 20px 15px;">
            <!-- LÍDER / SUBIU -->
            <div style="background-color: #2e7d32; color: #ffffff; padding: 12px 15px; border-radius: 2px; font-size: 15px; font-weight: bold; text-transform: uppercase; line-height: 1.3;">
                {topo_manchete}
            </div>
            <div style="margin-top: 6px; margin-bottom: 20px; border-left: 4px solid #2e7d32; padding: 8px 12px; background-color: #f1f8e9;">
                <p style="font-size: 13px; color: #333333; margin: 0; text-align: justify; line-height: 1.4;">{topo_texto}</p>
            </div>
            
            <!-- LANTERNA / CAIU -->
            {" " if todos_empatados else f'''
            <div style="background-color: #c62828; color: #ffffff; padding: 12px 15px; border-radius: 2px; font-size: 15px; font-weight: bold; text-transform: uppercase; line-height: 1.3;">
                {baixo_manchete}
            </div>
            <div style="margin-top: 6px; border-left: 4px solid #c62828; padding: 8px 12px; background-color: #ffebee;">
                <p style="font-size: 13px; color: #333333; margin: 0; text-align: justify; line-height: 1.4;">{baixo_texto}</p>
            </div>
            '''}
        </div>
    </div>
    """
    return html_jornal
# ─────────────────────────────────────────────────────────────────────────────
# 4. Motor de Cálculo Dinâmico da DRE
# ─────────────────────────────────────────────────────────────────────────────
def calcular_dre_dinamico(votos: dict) -> dict:
    receita      = 20_000_000_000.0
    cmv          = -16_500_000_000.0
    pdd          = -150_000_000.0
    depreciacao  = -150_000_000.0
    outras_desp  = -2_200_000_000.0
    juros        = -300_000_000.0
    
    # Rodada 1
    v1 = votos.get("r1")
    if v1 == 'A': juros = -310_000_000.0
    elif v1 == 'C': pdd = -100_000_000.0
        
    # Rodada 2
    v2 = votos.get("r2")
    if v2 == 'A': cmv -= 30_000_000.0
    elif v2 == 'B': depreciacao += 20_000_000.0
        
    lucro_bruto_v2 = receita + cmv
    ebitda_v2 = lucro_bruto_v2 + pdd + depreciacao + outras_desp
    pecld_dinamica = ebitda_v2 

    # Rodada 3
    v3 = votos.get("r3")
    if v3 == 'A': 
        pdd -= pecld_dinamica  
    elif v3 == 'B': 
        juros -= 50_000_000.0
    elif v3 == 'C': 
        receita += 80_000_000.0

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
    rows = ""
    for i, (conta, valor, destaque) in enumerate(linhas):
        borda = "border-top:2px solid #555;" if i in {2, 6, 7, 8} else ""
        bg    = "background:#1e3a5f;color:#fff;font-weight:bold;" if destaque else "color:#e0e0e0;"
        rows += f"<tr style='{bg}{borda}'><td style='padding:6px 10px;font-family:monospace;'>{conta}</td><td style='padding:6px 10px;font-family:monospace;text-align:right;'>{valor}</td></tr>"
    st.markdown(f"<table style='width:100%;border-collapse:collapse;'>{rows}</table><br>", unsafe_allow_html=True)

def aplicar_auditoria_final():
    PESOS_GR = {'A': 0, 'B': 2, 'C': 3}
    for nome, d in db.dados_empresas.items():
        votos = [d["voto_r1"], d["voto_r2"], d["voto_r3"]]
        score_gr = sum(PESOS_GR.get(v, 0) for v in votos if v is not None)
        d["score_gr"] = score_gr
        if score_gr == 0:
            d["status"] = "🏆 EXCELÊNCIA ÉTICA (Integridade Absoluta)"
            d["noticia_r4"] = "Score GR: 0. Transparência total e em conformidade estrita com as normas."
        elif score_gr in [2, 4, 6]:
            d["status"] = "⚖️ PRÁTICA LEGAL CONSERVADORA"
            d["noticia_r4"] = f"Score GR: {score_gr}. Uso de estimativas dentro dos limites legais."
        else:
            d["status"] = "🚨 INCONFORMIDADE MATERIAL DETECTADA"
            d["noticia_r4"] = f"Score GR: {score_gr}. Práticas agressivas ou manipulações identificadas pela auditoria."

# ─────────────────────────────────────────────────────────────────────────────
# 5. Inicialização de Estados de Navegação
# ─────────────────────────────────────────────────────────────────────────────
if "mestre_autenticado" not in st.session_state:
    st.session_state["mestre_autenticado"] = False
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "🏠 Início"

perfis_navegacao = [
    "🏠 Início",
    "🎛️ Painel Apresentador",
    "📈 Telão (Bolsa)",
    "📰 Mídia (Notícias)",
    "α - Empresa Alfa",
    "β - Empresa Beta",
    "γ - Empresa Gama"
]

perfil_sidebar = st.sidebar.selectbox("Navegação Lateral:", perfis_navegacao, index=perfis_navegacao.index(st.session_state["pagina_atual"]))
if perfil_sidebar != st.session_state["pagina_atual"]:
    st.session_state["pagina_atual"] = perfil_sidebar
    st.rerun()

perfil = st.session_state["pagina_atual"]

# ─────────────────────────────────────────────────────────────────────────────
# TELA: INÍCIO
# ─────────────────────────────────────────────────────────────────────────────
if perfil == "🏠 Início":
    st.title("🔒 Simulador de Governança")
    st.markdown("### Selecione o seu ambiente de acesso abaixo:")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("### 🎛️ Mestre")
            st.write("Acesso restrito para o Apresentador controlar as rodadas.")
            if st.button("Acessar Painel", use_container_width=True, type="primary"):
                st.session_state["pagina_atual"] = "🎛️ Painel Apresentador"
                st.rerun()
                
    with c2:
        with st.container(border=True):
            st.markdown("### 🏢 Empresas / Alunos")
            st.write("Selecione a estação de trabalho da sua bancada corporativa.")
            empresa_escolhida = st.selectbox("Escolha sua empresa:", ["α - Empresa Alfa", "β - Empresa Beta", "γ - Empresa Gama"])
            if st.button("Entrar como Aluno", use_container_width=True):
                st.session_state["pagina_atual"] = empresa_escolhida
                st.rerun()
                
    with c3:
        with st.container(border=True):
            st.markdown("### 📈 Projeção / Telão")
            st.write("Acesso livre para abrir o gráfico dinâmico e cotações na TV/Projetor.")
            if st.button("Abrir Telão Comercial", use_container_width=True):
                st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: TELÃO (BOLSA)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📈 Telão (Bolsa)":
    st.title("📈 Painel Geral do Mercado de Capitais")
    if st.button("⬅️ Voltar para a Home"):
        st.session_state["pagina_atual"] = "🏠 Início"
        st.rerun()
        
    aba_mercado, aba_jornal = st.tabs(["📈 Cotações e Gráficos", "📰 FEED DE NOTÍCIAS (Mural)"])

    with aba_mercado:
        col1, col2, col3 = st.columns(3)
        for i, nome in enumerate(EMPRESAS):
            with [col1, col2, col3][i]:
                st.metric(label=nome, value=f"R$ {db.dados_empresas[nome]['precos'][-1]:.2f}")

        fig, ax = plt.subplots(figsize=(10, 3))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1e222b')
        ax.tick_params(colors='white')
        ax.grid(True, color='#444', linestyle='--', alpha=0.5)
        
        cores = {"Empresa Alfa": "#3498db", "Empresa Beta": "#e67e22", "Empresa Gama": "#2ecc71"}
        maior_tamanho = 1
        for nome in EMPRESAS:
            historico = db.dados_empresas[nome]["precos"]
            if len(historico) > maior_tamanho: maior_tamanho = len(historico)
            ax.plot(range(len(historico)), historico, marker='o', linewidth=2.5, color=cores.get(nome, "#fff"), label=nome)
        
        labels_disponiveis = ['Abertura', 'Ex. 1', 'Ex. 2', 'Ex. 3']
        ax.set_xticks(range(maior_tamanho))
        ax.set_xticklabels(labels_disponiveis[:maior_tamanho])
        ax.legend(facecolor='#1e222b', edgecolor='#444', labelcolor='white')
        st.pyplot(fig)

    with aba_jornal:
        if db.historico_noticias:
            for n_html in db.historico_noticias:
                st.html(n_html)
        else: 
            st.info("⏳ Aguardando os primeiros fechamentos de mercado.")
    
    time.sleep(4)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: MÍDIA (NOTÍCIAS HISTÓRICAS)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📰 Mídia (Notícias)":
    st.title("📰 Portal Informativo - FEED COMPLETO GC NEWS")
    if st.button("⬅️ Voltar para a Home"):
        st.session_state["pagina_atual"] = "🏠 Início"
        st.rerun()
        
    if db.historico_noticias:
        for n_html in db.historico_noticias:
            st.html(n_html)
    else: 
        st.info("⏳ Nenhuma notícia extraordinária publicada neste ciclo operacional.")

# ─────────────────────────────────────────────────────────────────────────────
# TELA: PAINEL DO APRESENTADOR (Mestre)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "🎛️ Painel Apresentador":
    if st.button("⬅️ Voltar para a Home"):
        st.session_state["pagina_atual"] = "🏠 Início"
        st.rerun()
        
    if not st.session_state["mestre_autenticado"]:
        st.subheader("🔒 Acesso Reservado ao Apresentador")
        senha_dig = st.text_input("Insira a senha do Mestre:", type="password")
        if st.button("Autenticar"):
            if senha_dig == "mestre123":
                st.session_state["mestre_autenticado"] = True
                st.rerun()
            else: st.error("Chave incorreta.")
        st.stop()

    st.title("🎛️ Painel de Comando da Mesa de Operações")
    rodada = db.rodada_atual
    
    col1, col2 = st.columns([2, 1])
    with col1:
        texto_botao = f"▶ Encerrar Exercício {rodada} e Processar Resultados" if rodada < 3 else "🏁 Encerrar Ciclo e Gerar Auditoria Final"
        if rodada <= 3 and st.button(texto_botao, type="primary"):
            votos_da_rodada = [(n, db.dados_empresas[n]["tempo_voto"]) for n in EMPRESAS if db.dados_empresas[n][f"voto_r{rodada}"] is not None]
            ranking_velocidade = [item[0] for item in sorted(votos_da_rodada, key=lambda x: x[1] if x[1] else 0)]
            
            primeiro_a_responder = ranking_velocidade[0] if ranking_velocidade else None
            
            for nome in EMPRESAS:
                voto = db.dados_empresas[nome][f"voto_r{rodada}"]
                if voto:
                    preco_base = db.dados_empresas[nome]["precos"][-1] * IMPACTOS[rodada][voto]
                    ajuste_tempo = 0.10 if (nome == primeiro_a_responder) else (-0.10 if (len(ranking_velocidade) == 3 and nome == ranking_velocidade[-1]) else 0.0)
                    db.dados_empresas[nome]["precos"].append(round(preco_base + ajuste_tempo, 2))
                    # Mantemos o "tempo_voto" preservado para a tela do aluno consultar depois

            nova_manchete = gerar_manchete_dinamica(rodada, primeiro_a_responder)
            db.historico_noticias.insert(0, nova_manchete)
            
            if db.rodada_atual == 3: aplicar_auditoria_final()
            db.rodada_atual += 1
            st.rerun()

    with col2:
        if st.button("🔄 Reiniciar Jogo Completo"):
            db.rodada_atual = 1
            db.historico_noticias = [] 
            st.session_state["mestre_autenticado"] = False
            for nome in EMPRESAS:
                db.dados_empresas[nome] = {"precos": [20.0], "voto_r1": None, "voto_r2": None, "voto_r3": None, "voto_r4": None, "tempo_voto": None, "status": "Operando", "noticia_r4": "", "score_gr": 0}
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Monitoramento de Votos das Bancadas (Tempo Real)")
    for nome in EMPRESAS:
        voto = db.dados_empresas[nome].get(f"voto_r{min(rodada, 3)}")
        if voto: st.success(f"✅ **{nome}** — 📥 SUBMETEU A DECISÃO!")
        else: st.warning(f"⏳ **{nome}** — Em deliberação interna...")
    
    time.sleep(4)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELAS DAS EMPRESAS (ALUNOS)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil in EMPRESA_MAP:
    nome_interno = EMPRESA_MAP[perfil]
    d = db.dados_empresas[nome_interno]
    rodada = db.rodada_atual

    votos_anteriores = {"r1": d["voto_r1"], "r2": d["voto_r2"]}
    dre_atual = calcular_dre_dinamico(votos_anteriores)
    pecld_m = dre_atual["pecld_dinamica"] / 1_000_000.0  

    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")
    if st.button("⬅️ Voltar para a Home"):
        st.session_state["pagina_atual"] = "🏠 Início"
        st.rerun()
        
    aba_voto, aba_jornal_aluno = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mural Coletivo"])

    with aba_voto:
        if rodada <= 3:
            voto_atual = d[f"voto_r{rodada}"]
            if voto_atual is None:
                st.markdown(f"### 📋 Deliberação Estratégica — Exercício {rodada}")
                col_prob, col_dre = st.columns([1.1, 0.9], gap="large")
                
                with col_prob:
                    if rodada == 3:
                        texto_r3 = f"""### 🚨 RODADA 3: O DESAFIO DA INSOLVÊNCIA E DA PECLD
A recessão econômica e o desemprego corroeram a renda das famílias, fazendo a inadimplência no crediário próprio saltar de 3% para 12%. Pelas regras do CPC 48 (IFRS 9), a perda de recebíveis obriga a empresa a registrar uma provisão (PECLD) de **R$ {pecld_m:,.0f} milhões** na DRE. O impacto desse lançamento anula o EBITDA do período, escancara uma situação de insolvência técnica e aciona a revisão dos auditores independentes."""
                        st.markdown(texto_r3)
                    else:
                        if rodada in NARRATIVAS: st.markdown(NARRATIVAS[rodada])
                        
                with col_dre:
                    votos_simulados = {f"r{r}": d[f"voto_r{r}"] for r in range(1, rodada)}
                    votos_simulados[f"r{rodada}"] = 'B'
                    exibir_dre(votos_simulados, rodada)

                st.markdown("---")
                escolha = st.radio("Selecione o tratamento contábil adotado:", ["A", "B", "C"], format_func=lambda x: get_labels(rodada, pecld_m)[x])
                if st.button("✅ Homologar Resolução", use_container_width=True):
                    d[f"voto_r{rodada}"] = escolha
                    d["tempo_voto"] = time.time()  
                    st.success("Resolução homologada!")
                    st.rerun()
            else:
                st.success(f"📌 Estratégia Adotada: {get_labels(rodada, pecld_m)[voto_atual]}")
                
                # --- CALCULA FEEDBACK INDIVIDUAL DE TEMPO (Apenas visível na tela da própria empresa) ---
                votos_com_tempo = [(n, db.dados_empresas[n]["tempo_voto"]) for n in EMPRESAS if db.dados_empresas[n][f"voto_r{rodada}"] is not None]
                ranking_temp = [item[0] for item in sorted(votos_com_tempo, key=lambda x: x[1] if x[1] else 0)]
                
                if ranking_temp and ranking_temp[0] == nome_interno:
                    st.markdown("""<div style='background-color: #c8e6c9; border: 1px solid #81c784; color: #1b5e20; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 13px;'>
                    ⏱️ <b>Bônus de Agilidade:</b> Sua bancada foi a primeira a homologar a decisão! O mercado valorizou a rapidez de governança com +R$ 0,10 na ação.
                    </div>""", unsafe_allow_html=True)
                elif len(ranking_temp) == 3 and ranking_temp[-1] == nome_interno:
                    st.markdown("""<div style='background-color: #ffcdd2; border: 1px solid #ef5350; color: #b71c1c; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 13px;'>
                    ⏱️ <b>Penalidade por Atraso:</b> Sua bancada foi a última a responder. A lentidão perante a crise gerou incerteza e custou -R$ 0,10 de desconto operacional.
                    </div>""", unsafe_allow_html=True)
                
                votos_reais = {f"r{r}": d[f"voto_r{r}"] for r in range(1, rodada + 1)}
                exibir_dre(votos_reais, rodada)
        else:
            st.markdown(f"**Veredito da Auditoria:** {d['status']}")
            if d["noticia_r4"]: st.warning(d["noticia_r4"])
            votos_finais = {f"r{r}": d[f"voto_r{r}"] for r in range(1, 4)}
            exibir_dre(votos_finais, 3)

    with aba_jornal_aluno:
        if db.historico_noticias:
            for n_html in db.historico_noticias:
                st.html(n_html)
        else: 
            st.info("ℹ️ Nenhuma manchete publicada para este ciclo.")
