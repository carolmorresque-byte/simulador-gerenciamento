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
    'C': '💀 OPÇÃO C: Congelar Provisões e Antecipar Garantias — Omite os R$ 200M em perdas e antecipa R$ 80M de receitas futuras.',
}

def get_labels(rodada: int) -> dict:
    if rodada == 1: return LABELS_R1
    if rodada == 2: return LABELS_R2
    if rodada == 3: return LABELS_R3
    return LABELS_R1

NARRATIVAS = {
    1: """### 🏭 RODADA 1: O DILEMA DO RISCO SACADO 
**Cenário:** O comitê de auditoria descobriu que a empresa realiza operações de  Risco Sacado com grandes bancos para antecipar pagamentos de fornecedores. 
Os juros dessas operações vinham sendo incorporados ao custo das mercadorias ou transitando fora do balanço. Uma denúncia anônima ameaça ir à CVM caso a prática continue oculta.

Sua mesa diretora precisa decidir como tratar a reclassificação desses juros antes da divulgação do balanço trimestral.""",
    
    2: """### 📰 RODADA 2: A CRISE DO DÓLAR E OS CONTRATOS DE IMPORTAÇÃO
**Cenário:** O dólar disparou de R$ 5,00 para R$ 6,50 em virtude de tensões geopolíticas. A empresa possui contratos robustos de importação de eletrônicos sem proteção de *hedge* cambial. O impacto bruto estimado nas mercadorias que estão no porto é de uma perda de R$ 300M. Se reconhecido agora, destruirá as metas do ano.

A diretoria se reúne em caráter de urgência para definir a manobra orçamentária.""",
    
    3: """### 🚨 RODADA 3: O DESAFIO DA INSOLVÊNCIA E DA PECLD
**Cenário:** Um grande parceiro comercial e bandeira de cartões parceira do grupo entrou em recuperação judicial. A estimativa real de calote na carteira de crediário da empresa é de R$ 200M. O Diretor de RI avisa que o mercado penalizará agressivamente o papel se essa perda for escancarada.

Escolha a estratégia de provisionamento para mitigar o impacto na percepção dos investidores."""
}

# ─────────────────────────────────────────────────────────────────────────────
# 3.5. Gerador de Notícias Dinâmicas
# ─────────────────────────────────────────────────────────────────────────────
def gerar_manchete_dinamica(rodada_encerrada: int):
    precos_atuais = {nome: db.dados_empresas[nome]["precos"][-1] for nome in EMPRESAS}
    lista_ordenada = sorted(precos_atuais.items(), key=lambda x: x[1], reverse=True)
    preco_max = lista_ordenada[0][1]
    preco_min = lista_ordenada[-1][1]
    
    líderes = [nome for nome, p in precos_atuais.items() if p == preco_max]
    lanternas = [nome for nome, p in precos_atuais.items() if p == preco_min]
    todos_empatados = (preco_max == preco_min)
    
    txt_lideres = " e ".join(líderes)
    txt_lanternas = " e ".join(lanternas)
    votos_r1 = [db.dados_empresas[n]["voto_r1"] for n in EMPRESAS]
    
    topo_manchete, topo_texto = "", ""
    baixo_manchete, baixo_texto = "", ""

    if todos_empatados:
        topo_manchete = "MERCADO EM ESTABILIDADE ABSOLUTA: Setor caminha em bloco!"
        topo_texto = f"SÃO PAULO — Sem distinção de performance, as empresas do setor mantiveram as cotas rigorosamente em R$ {preco_max:.2f}."
        baixo_manchete = "DISPUTA ACIRRADA"
        baixo_texto = "SÃO PAULO — Margens idênticas congelam posições na bolsa corporativa."
    elif rodada_encerrada == 1:
        contagem_A = votos_r1.count('A')
        contagem_B = votos_r1.count('B')
        contagem_C = votos_r1.count('C')

        if contagem_A == 3:
            topo_manchete = "🚢 NAUFRÁGIO EM MASSA! Todo o setor bate de frente com o iceberg dos juros!"
            topo_texto = f"SÃO PAULO — Sem escapatória. A escolha agressiva pelo Passivo Financeiro arrastou as cotações."
        elif contagem_B == 3:
            topo_manchete = "🌊 MAR CALMO? Setor se protege em bloco e evita o naufrágio!"
            topo_texto = f"SÃO PAULO — Ativar juros no estoque garantiu estabilidade e segurança."
        elif contagem_C == 3:
            topo_manchete = "🏝️ EL DORADO DO VAREJO! Super iates decolam com lucros históricos!"
            topo_texto = f"SÃO PAULO — Reduzir PDD foi o motor de popa perfeito para impulsionar os valuations."
        else:
            topo_manchete = f"📈 MOVIMENTAÇÃO NO PREGÃO: {txt_lideres} assume a liderança!"
            topo_texto = f"SÃO PAULO — Estratégias divergentes alteram posições. Papéis líderes cotados a R$ {preco_max:.2f}."
            baixo_manchete = f"📉 PRESSÃO DO MERCADO: {txt_lanternas} recua"
            baixo_texto = f"SÃO PAULO — Investidores punem decisões agressivas, deixando a lanterna em R$ {preco_min:.2f}."
    else:
        topo_manchete = "MERCADO EXPOSTO AOS IMPACTOS ADUANEIROS"
        topo_texto = f"SÃO PAULO — Mudanças macroeconômicas impactam diretamente o valor patrimonial ajustado."
        baixo_manchete = "CENÁRIO VOLÁTIL"
        baixo_texto = f"SÃO PAULO — Balanços revisados geram novas dinâmicas de preços a R$ {preco_min:.2f}."

    html_jornal = f"""
    <div style="background-color: #ffffff; border: 1px solid #ddd; font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 10px rgba(0,0,0,0.15);">
        <div style="background-color: #cc0000; color: #ffffff; display: flex; justify-content: space-between; align-items: center; padding: 12px 20px;">
            <div style="font-size: 22px; font-weight: bold;"></div>
            <div style="font-size: 24px; font-weight: 900; letter-spacing: 1px;">GC NEWS</div>
            <div style="font-size: 20px;"></div>
        </div>
        <div style="padding: 20px 15px;">
            <div style="background-color: #639a67; color: #ffffff; padding: 12px 15px; border-radius: 2px; font-size: 16px; font-weight: bold; text-transform: uppercase; line-height: 1.3;">
                {topo_manchete}
            </div>
            <div style="margin-top: 8px; margin-bottom: 25px; border: 1px solid #cccccc; padding: 12px; background-color: #fafafa;">
                <p style="font-size: 12.5px; color: #333333; margin: 0; text-align: justify; line-height: 1.4;">{topo_texto}</p>
            </div>
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
    
    v1 = votos.get("r1")
    if v1 == 'A': juros = -310_000_000.0
    elif v1 == 'C': pdd = -100_000_000.0
        
    v2 = votos.get("r2")
    if v2 == 'A': cmv -= 30_000_000.0
    elif v2 == 'B': depreciacao += 20_000_000.0
        
    v3 = votos.get("r3")
    if v3 == 'A': pdd -= 200_000_000.0
    elif v3 == 'B': juros -= 50_000_000.0
    elif v3 == 'C': receita += 80_000_000.0

    lucro_bruto = receita + cmv
    ebitda = lucro_bruto + pdd + depreciacao + outras_desp
    lucro_liq = ebitda + juros
    
    return {
        "receita": receita, "cmv": abs(cmv), "lucro_bruto": lucro_bruto,
        "pdd": abs(pdd), "depreciacao": abs(depreciacao), "outras_desp": abs(outras_desp),
        "ebitda": ebitda, "juros": abs(juros), "lucro_liq": lucro_liq
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

# Sincroniza a escolha da barra lateral com o estado global do app
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
# TELA: INÍCIO (Com botões grandes de atalho no corpo da página)
# ─────────────────────────────────────────────────────────────────────────────
if perfil == "🏠 Início":
    st.title("🔒 Simulador de Governança")
    st.markdown("### Selecione o seu ambiente de acesso abaixo:")
    
    # 3 colunas estruturadas para o usuário clicar diretamente
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
# TELA: TELÃO (BOLSA) - GRÁFICO AUTOMÁTICO CORRIGIDO
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📈 Telão (Bolsa)":
    st.title("📈 Painel Geral do Mercado de Capitais")
    if st.button("⬅️ Voltar para a Home"):
        st.session_state["pagina_atual"] = "🏠 Início"
        st.rerun()
        
    aba_mercado, aba_jornal = st.tabs(["📈 Cotações e Gráficos", "📰 GC NEWS"])

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
        if db.manchete_jornal: st.html(db.manchete_jornal)
        else: st.info("⏳ Aguardando os primeiros fechamentos de mercado.")
    
    time.sleep(4)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: MÍDIA (NOTÍCIAS)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📰 Mídia (Notícias)":
    st.title("📰 Portal Informativo - GC NEWS")
    if st.button("⬅️ Voltar para a Home"):
        st.session_state["pagina_atual"] = "🏠 Início"
        st.rerun()
    if db.manchete_jornal: st.html(db.manchete_jornal)
    else: st.info("⏳ Nenhuma notícia extraordinária publicada neste ciclo operacional.")

# ─────────────────────────────────────────────────────────────────────────────
# TELA: PAINEL DO APRESENTADOR (Único com senha)
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
    sub_tela = st.radio("Selecione a Ação do Mestre:", ["📊 Monitorar Respostas & Passar de Rodada", "📈 Visualizar Telão"])
    
    if sub_tela == "📊 Monitorar Respostas & Passar de Rodada":
        col1, col2 = st.columns([2, 1])
        with col1:
            texto_botao = f"▶ Encerrar Exercício {rodada} e Processar Resultados" if rodada < 3 else "🏁 Encerrar Ciclo e Gerar Auditoria Final"
            if rodada <= 3 and st.button(texto_botao, type="primary"):
                votos_da_rodada = [(n, db.dados_empresas[n]["tempo_voto"]) for n in EMPRESAS if db.dados_empresas[n][f"voto_r{rodada}"] is not None]
                ranking_velocidade = [item[0] for item in sorted(votos_da_rodada, key=lambda x: x[1] if x[1] else 0)]
                
                for nome in EMPRESAS:
                    voto = db.dados_empresas[nome][f"voto_r{rodada}"]
                    if voto:
                        preco_base = db.dados_empresas[nome]["precos"][-1] * IMPACTOS[rodada][voto]
                        ajuste_tempo = 0.10 if (ranking_velocidade and nome == ranking_velocidade[0]) else (-0.10 if (len(ranking_velocidade) == 3 and nome == ranking_velocidade[-1]) else 0.0)
                        db.dados_empresas[nome]["precos"].append(round(preco_base + ajuste_tempo, 2))
                        db.dados_empresas[nome]["tempo_voto"] = None  

                db.manchete_jornal = gerar_manchete_dinamica(rodada)
                if db.rodada_atual == 3: aplicar_auditoria_final()
                db.rodada_atual += 1
                st.rerun()

        with col2:
            if st.button("🔄 Reiniciar Jogo Completo"):
                db.rodada_atual = 1
                db.manchete_jornal = None 
                st.session_state["mestre_autenticado"] = False
                for nome in EMPRESAS:
                    db.dados_empresas[nome] = {"precos": [20.0], "voto_r1": None, "voto_r2": None, "voto_r3": None, "voto_r4": None, "tempo_voto": None, "status": "Operando", "noticia_r4": "", "score_gr": 0}
                st.rerun()

        st.markdown("### 📊 Monitoramento de Votos das Bancadas (Tempo Real)")
        for nome in EMPRESAS:
            voto = db.dados_empresas[nome].get(f"voto_r{min(rodada, 3)}")
            if voto: st.success(f"✅ **{nome}** — 📥 SUBMETEU A DECISÃO! | Escolha: `{voto}`")
            else: st.warning(f"⏳ **{nome}** — Em deliberação interna...")
        time.sleep(4)
        st.rerun()
        
    elif sub_tela == "📈 Visualizar Telão":
        for nome in EMPRESAS: st.metric(label=nome, value=f"R$ {db.dados_empresas[nome]['precos'][-1]:.2f}")

# ─────────────────────────────────────────────────────────────────────────────
# TELAS DAS EMPRESAS (ALUNOS)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil in EMPRESA_MAP:
    nome_interno = EMPRESA_MAP[perfil]
    d = db.dados_empresas[nome_interno]
    rodada = db.rodada_atual

    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")
    if st.button("⬅️ Voltar para a Home"):
        st.session_state["pagina_atual"] = "🏠 Início"
        st.rerun()
        
    aba_voto, aba_jornal_aluno = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mercado"])

    with aba_voto:
        if rodada <= 3:
            voto_atual = d[f"voto_r{rodada}"]
            if voto_atual is None:
                st.markdown(f"### 📋 Deliberação Estratégica — Exercício {rodada}")
                col_prob, col_dre = st.columns([1.1, 0.9], gap="large")
                with col_prob:
                    if rodada in NARRATIVAS: st.markdown(NARRATIVAS[rodada])
                with col_dre:
                    votos_simulados = {f"r{r}": d[f"voto_r{r}"] for r in range(1, rodada)}
                    votos_simulados[f"r{rodada}"] = 'B'
                    exibir_dre(votos_simulados, rodada)

                st.markdown("---")
                escolha = st.radio("Selecione o tratamento contábil adotado:", ["A", "B", "C"], format_func=lambda x: get_labels(rodada)[x])
                if st.button("✅ Homologar Resolução", use_container_width=True):
                    d[f"voto_r{rodada}"] = escolha
                    d["tempo_voto"] = time.time()  
                    st.success("Resolução homologada!")
                    st.rerun()
            else:
                st.success(f"📌 **Estratégia Adotada:** {get_labels(rodada)[voto_atual]}")
                votos_reais = {f"r{r}": d[f"voto_r{r}"] for r in range(1, rodada + 1)}
                exibir_dre(votos_reais, rodada)
        else:
            st.markdown(f"**Veredito da Auditoria:** {d['status']}")
            if d["noticia_r4"]: st.warning(d["noticia_r4"])
            votos_finais = {f"r{r}": d[f"voto_r{r}"] for r in range(1, 4)}
            exibir_dre(votos_finais, 3)

    with aba_jornal_aluno:
        if db.manchete_jornal: st.html(db.manchete_jornal)
        else: st.info("ℹ️ Nenhuma manchete publicada para este ciclo.")
