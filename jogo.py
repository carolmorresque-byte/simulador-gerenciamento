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

# Inicialização segura de estados globais
if not hasattr(db, 'sessoes_ativas'):
    db.sessoes_ativas = set()
if not hasattr(db, 'manchete_jornal'):
    db.manchete_jornal = None

# Inicialização segura do Session State (Estados locais do navegador)
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None
if "telao_origem" not in st.session_state:
    st.session_state["telao_origem"] = None

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

# NARRATIVAS COMPLETAS DO JOGO
NARRATIVAS = {
    1: """### 🏭 1: O DILEMA DO RISCO SACADO e ANTECIPAÇÃO DE FORNECEDORES
**Cenário:** O comitê de auditoria descobriu que a empresa realiza operações de *Forfait* (Risco Sacado) com grandes bancos para antecipar pagamentos de fornecedores. Os juros dessas operações vinham sendo incorporados ao custo das mercadorias ou transitando fora do balanço. Uma denúncia anônima ameaça ir à CVM caso a prática continue oculta.

Sua mesa diretora precisa decidir como tratar a reclassificação desses juros antes da divulgação do balanço trimestral.""",
    
    2: """### 📰 RODADA 2: A CRISE DO DÓLAR E OS CONTRATOS DE IMPORTAÇÃO
**Cenário:** O dólar disparou de R$ 5,00 para R$ 6,50 em virtude de tensões geopolíticas. A empresa possui contratos robustos de importação de eletrônicos sem proteção de *hedge* cambial. O impacto bruto estimado nas mercadorias que estão no porto é de uma perda de R$ 300M. Se reconhecido agora, destruirá as metas do ano.

A diretoria se reúne em caráter de urgência para definir a manobra orçamentária.""",
    
    3: """### 🚨 RODADA 3: O DESAFIO DA INSOLVÊNCIA E DA PECLD
**Cenário:** Um grande parceiro comercial e bandeira de cartões parceira do grupo entrou em recuperação judicial. A estimativa real de calote na carteira de crediário da empresa é de R$ 200M. O Diretor de RI avisa que o mercado penalizará agressivamente o papel se essa perda for escancarada.

Escolha a estratégia de provisionamento para mitigar o impacto na percepção dos investidores."""
}

# ─────────────────────────────────────────────────────────────────────────────
# 3.5. Gerador de Notícias Dinâmicas com Métricas Financeiras
# ─────────────────────────────────────────────────────────────────────────────
def gerar_manchete_dinamica(rodada_encerrada: int):
    precos_atuais = {nome: db.dados_empresas[nome]["precos"][-1] for nome in EMPRESAS}
    precos_anteriores = {nome: db.dados_empresas[nome]["precos"][-2] for nome in EMPRESAS}
    
    lista_ordenada = sorted(precos_atuais.items(), key=lambda x: x[1], reverse=True)
    
    preco_max = lista_ordenada[0][1]
    preco_min = lista_ordenada[-1][1]
    
    líderes = [nome for nome, p in precos_atuais.items() if p == preco_max]
    lanternas = [nome for nome, p in precos_atuais.items() if p == preco_min]
    
    todos_empatados = (preco_max == preco_min)
    
    nome_lider_rep = líderes[0]
    nome_lanterna_rep = lanternas[0]
    
    var_lider_pct = ((preco_max - precos_anteriores[nome_lider_rep]) / precos_anteriores[nome_lider_rep]) * 100 if precos_anteriores[nome_lider_rep] > 0 else 0
    var_lanterna_pct = ((preco_min - precos_anteriores[nome_lanterna_rep]) / precos_anteriores[nome_lanterna_rep]) * 100 if precos_anteriores[nome_lanterna_rep] > 0 else 0
    
    distancia_pct = ((preco_max - preco_min) / preco_min) * 100 if preco_min > 0 else 0

    txt_lideres = " e ".join(líderes)
    txt_lanternas = " e ".join(lanternas)

    votos_r1 = [db.dados_empresas[n]["voto_r1"] for n in EMPRESAS]
    votos_r2 = [db.dados_empresas[n]["voto_r2"] for n in EMPRESAS]
    votos_r3 = [db.dados_empresas[n]["voto_r3"] for n in EMPRESAS]
    
    topo_manchete, topo_texto = "", ""
    baixo_manchete, baixo_texto = "", ""

    if todos_empatados:
        topo_manchete = "MERCADO EM ESTABILIDADE ABSOLUTA: Setor caminha em bloco!"
        topo_texto = f"SÃO PAULO — Sem distinção de performance, as empresas do setor mantiveram as cotas rigorosamente em R$ {preco_max:.2f}."
        baixo_manchete = "DISPUTA ACIRRADA: Margens idênticas congelam posições na bolsa."
        baixo_texto = "SÃO PAULO — Analistas apontam que a falta de expressão eliminou vantagens competitivas nesta rodada."
    
    elif rodada_encerrada == 1:
        contagem_A = votos_r1.count('A')
        contagem_B = votos_r1.count('B')
        contagem_C = votos_r1.count('C')

        nome_a = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r1"] == 'A'])
        nome_b = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r1"] == 'B'])
        nome_c = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r1"] == 'C'])

        if contagem_A == 3:
            topo_manchete = "🚢 NAUFRÁGIO EM MASSA! Todo o setor bate de frente com o iceberg dos juros!"
            topo_texto = f"SÃO PAULO — Sem escapatória. A escolha agressiva pelo Passivo Financeiro arrastou todas as empresas para o fundo do pregão, congelando os papéis em R$ {preco_min:.2f}."
            baixo_manchete = "SEM SOBREVIVENTES"
            baixo_texto = "Nenhuma mesa conseguiu mitigar os encargos financeiros desta rodada."
        elif contagem_B == 3:
            topo_manchete = "🌊 MAR CALMO? Setor se protege em bloco e evita o naufrágio!"
            topo_texto = f"SÃO PAULO — Ativar juros no estoque garantiu uma navegação segura. Todas as empresas mantiveram as ações estáveis na casa de R$ {preco_max:.2f}."
            baixo_manchete = "NAVEGAÇÃO COORDENADA"
            baixo_texto = "Estratégia idêntica neutralizou a volatilidade inicial do mercado."
        elif contagem_C == 3:
            topo_manchete = "🏝️ EL DORADO DO VAREJO! Super iates decolam com lucros históricos!"
            topo_texto = f"SÃO PAULO — Reduzir PDD foi o motor de popa perfeito! O mercado comprou a narrativa de otimismo e inflou as ações para R$ {preco_max:.2f}."
            baixo_manchete = "CÉU AZUL EM ALTO MAR"
            baixo_texto = "Balanços highly agressivos impulsionaram o valuation de todas as bancadas."
        elif contagem_A == 2 and contagem_B == 1:
            topo_manchete = f"🚢 O SETOR TITANIC! Mercado afunda {abs(var_lanterna_pct):.1f}%, mas a {nome_b} veste colete salva-vidas e cai só {abs(var_lider_pct):.1f}%!"
            topo_texto = f"SÃO PAULO — O setor bateu no iceberg da crisis e afundou. A {nome_b} reagiu rápido, vestiu seu colete a R$ {preco_max:.2f} e garantiu {distancia_pct:.1f}% de vantagem sobre as outras."
            baixo_manchete = f"NAUFRÁGIO CONFIRMADO: {nome_a} bate no fundo do mar a R$ {preco_min:.2f}!"
            baixo_texto = f"SÃO PAULO — O mercado puniu a falta de manobra das lanternas, cujas ações derreteram {abs(var_lanterna_pct):.1f}% no trimestre."
        elif contagem_A == 2 and contagem_C == 1:
            topo_manchete = f"🌊 CONTRA A MARÉ: Concorrentes afundam {abs(var_lanterna_pct):.1f}%, mas a gigante {nome_c} tinha seu bote reserva e dispara para R$ {preco_max:.2f}!"
            topo_texto = f"SÃO PAULO — Enquanto uns naufragam com queda expressiva nas ações, a {nome_c} comemora seus lucros, abrindo uma cratera insana de {distancia_pct:.1f}% de distância da lanterna!"
            baixo_manchete = f"SOB A ÁGUA: {nome_a} registra prejuízo estético e derrete na Bolsa!"
            baixo_texto = f"SÃO PAULO — Pressionadas pelo passivo, as concorrentes amargaram uma desvalorização violenta, restando cotadas a R$ {preco_min:.2f}."
        elif contagem_B == 2 and contagem_A == 1:
            topo_manchete = f"⚓ NAVIO AFUNDANDO, QUEM TEM COLETE BOIA! Setor recua, mas a {nome_a} sem proteção é a que afunda primeiro!"
            topo_texto = f"SÃO PAULO — Enquanto as concorrentes vestiram o colete e amorteceram a queda em {abs(var_lider_pct):.1f}% (R$ {preco_max:.2f}), a {nome_a} foi direto para o fundo do mar, virando a âncora do pregão ao despencar {abs(var_lanterna_pct):.1f}%."
            baixo_manchete = f"ÂNCORA DO PREGÃO: {nome_a} desce ao nível abissal de R$ {preco_min:.2f}!"
            baixo_texto = f"SÃO PAULO — Sem colchão contábil contra as taxas de juros, a empresa viu seu valor de mercado sumir na água."
        elif contagem_B == 2 and contagem_C == 1:
            topo_manchete = f"🌊 ENGOLINDO ÁGUA NO MAR! A {nome_c} acelera seu iate de luxo e deixa rivais boiando para trás!"
            topo_texto = f"SÃO PAULO — Enquanto as concorrentes afundam e tentam respirar na superfície com queda de {abs(var_lanterna_pct):.1f}% (R$ {preco_min:.2f}), a {nome_c} mostra resiliência absoluta a R$ {preco_max:.2f} e abre {distancia_pct:.1f}% de distância."
            baixo_manchete = f"REBOCADAS PELA CRISE: Ritmo lento prende {nome_b} nas marés baixas!"
            baixo_texto = f"SÃO PAULO — A postura defensiva evitou a quebra, mas impediu o papel de acompanhar os motores de alta da líder."
        elif contagem_C == 2 and contagem_A == 1:
            topo_manchete = f"🏝️ ESQUECIDA EM ALTO MAR? Concorrentes em alta enquanto a {nome_a} afunda sozinha no mar!"
            topo_texto = f"SÃO PAULO — As concorrentes pegaram o iate de luxo e viram as ações decolarem {var_lider_pct:+.1f}% (R$ {preco_max:.2f}), enquanto a {nome_a} foi abandonada no naufrágio caindo {abs(var_lanterna_pct):.1f}%."
            baixo_manchete = f"🛟 FORA DO RESGATE: {nome_a} colide com iceberg de despesas e opera a R$ {preco_min:.2f}!"
            baixo_texto = f"SÃO PAULO — Isolada na lanterna corporativa, a empresa ficou com uma incômoda desvantagem de {distancia_pct:.1f}% em relação ao topo."
        elif contagem_C == 2 and contagem_B == 1:
            topo_manchete = f"🌊 ESQUECIDA EM ALTO MAR? Concorrentes em alta enquanto a {nome_b} fica boiando!"
            topo_texto = f"SÃO PAULO — As concorrentes pegaram o iate e viram as ações subirem {var_lider_pct:+.1f}% (R$ {preco_max:.2f}), enquanto a {nome_b} está em alto mar engolindo água, amargando {abs(var_lanterna_pct):.1f}% de prejuízo."
            baixo_manchete = f"MANTENDO A CABEÇA FORA D'ÁGUA: {nome_b} amarga R$ {preco_min:.2f} mas evita o colapso total!"
            baixo_texto = f"SÃO PAULO — Ainda bem que tinha salva-vidas (ficou {distancia_pct:.1f}% atrás da líder), impedindo que o papel virasse fumaça contábil."

    elif rodada_encerrada == 2:
        # Lógica resumida para simplificação do retorno das mensagens das rodadas 2 e 3
        topo_manchete = "MERCADO EXPOSTO AOS IMPACTOS ADUANEIROS"
        topo_texto = f"SÃO PAULO — Movimentações corporativas alteram o grid na segunda rodada. Cotação topo em R$ {preco_max:.2f}."
        baixo_manchete = "PRESSÃO CAMBIAL AFETA BALANÇOS"
        baixo_texto = f"SÃO PAULO — Fragilidades operacionais deixam lanternas cotadas em R$ {preco_min:.2f}."

    elif rodada_encerrada == 3:
        topo_manchete = "AUDITORIA FINALIZADA NO SETOR VAREJISTA"
        topo_texto = f"SÃO PAULO — Encerramento das rodadas operacionais consolida valuations. Cotação máxima fixada em R$ {preco_max:.2f}."
        baixo_manchete = "BUSHING CONTÁBIL EXPOSTO"
        baixo_texto = f"SÃO PAULO — Riscos de provisões impactam diretamente os papéis de menor valor a R$ {preco_min:.2f}."

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
                <div style="font-size: 28px; text-align: center; width: 75px; line-height: 1.1; font-weight: bold; padding: 5px;">
                    🪅🤑<br><span style="font-size: 20px; color: #2ecc71;">💸📈</span>
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
                <div style="font-size: 28px; text-align: center; width: 75px; line-height: 1.1; font-weight: bold; padding: 5px;">
                    💸💸<br><span style="font-size: 22px; color: #e74c3c;">🤬📉</span>
                </div>
            </div>
            <div style="font-size: 11px; font-weight: bold; color: #222222; border-top: 1px solid #ddd; padding-top: 12px; margin-top: 25px; letter-spacing: 0.5px;">
                EDIÇÃO ATUALIZADA COMPARTILHADA COM O MERCADO.
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
    
    v1 = votos.get("r1")
    if v1 == 'A':
        juros = -310_000_000.0
    elif v1 == 'B':
        pass
    elif v1 == 'C':
        pdd = -100_000_000.0
        
    v2 = votos.get("r2")
    if v2 == 'A':
        cmv -= 30_000_000.0
    elif v2 == 'B':
        depreciacao += 20_000_000.0
    elif v2 == 'C':
        pass
        
    v3 = votos.get("r3")
    if v3 == 'A':
        pdd -= 200_000_000.0
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
        "ebitda": ebitda, "juros": abs(juros), "lucro_liq": lucro_liq
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

# ─────────────────────────────────────────────────────────────────────────────
# 5. Auditoria Baseada no Novo Score GR
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
            d["noticia_r4"] = "Score GR: 6. Três escolhas consecutivas de gerenciamento dentro da lei (Opção B). Legal, mas acende alertas."
        elif score_gr in [3, 5]:
            d["status"] = "🚨 INCONFORMIDADE MATERIAL (1 Fraude)"
            d["noticia_r4"] = f"Score GR: {score_gr}. Uma fraude estrutural grave (Opção C) foi detectada no histórico."
        elif score_gr in [7, 8]:
            d["status"] = "❌ MANIPULAÇÃO SISTÊMICA (2 Fraudes)"
            d["noticia_r4"] = f"Score GR: {score_gr}. Duas fraudes contábeis gravíssimas para ocultar perdas operacionais."
        elif score_gr == 9:
            d["status"] = "🚔 FRAUDE ESTRUTURAL COMPLETA (3 Fraudes)"
            d["noticia_r4"] = "Score GR: 9. O colapso total. Todas as escolhas foram fraudes contábeis dolosas."

# ─────────────────────────────────────────────────────────────────────────────
# 6. Fluxo de Autenticação Aberto e Seletivo (MODIFICADO)
# ─────────────────────────────────────────────────────────────────────────────
# Criando a lista de perfis disponíveis na sidebar para navegação transparente
perfis_navegacao = [
    "Escolha uma opção...",
    "🎛️ Painel Apresentador",
    "📈 Telão (Bolsa)",
    "📰 Mídia (Notícias)",
    "α - Empresa Alfa",
    "β - Empresa Beta",
    "γ - Empresa Gama"
]

perfil_selecionado = st.sidebar.selectbox("Quem está acessando?", perfis_navegacao, index=perfis_navegacao.index(st.session_state["usuario_logado"]) if st.session_state["usuario_logado"] in perfis_navegacao else 0)

# Trata a mudança de estado baseada no seletor
if perfil_selecionado != "Escolha uma opção...":
    # Se for Telão ou Mídia, dá livre acesso sem pedir senhas
    if perfil_selecionado in ["📈 Telão (Bolsa)", "📰 Mídia (Notícias)"]:
        st.session_state["usuario_logado"] = perfil_selecionado
    else:
        # Só pede senha se o usuário mudar ativamente para um perfil restrito que ainda não está autenticado
        if st.session_state["usuario_logado"] != perfil_selecionado:
            st.title("🔒 Autenticação Exigida")
            senha_digitada = st.text_input("Insira a chave de acesso corporativa:", type="password", key="senha_field")
            if st.button("Confirmar Identidade"):
                if senha_digitada == SENHAS[perfil_selecionado]:
                    st.session_state["usuario_logado"] = perfil_selecionado
                    st.rerun()
                else:
                    st.error("Chave incorreta para este perfil de segurança.")
            st.stop()
else:
    st.session_state["usuario_logado"] = None
    st.title("🔒 Simulador de Governança")
    st.info("Utilize o menu seletor na barra lateral esquerda para ingressar em sua respectiva estação de simulação.")
    st.stop()

# Recuperação de segurança das variáveis de perfil local
perfil = st.session_state["usuario_logado"]
nome_interno = EMPRESA_MAP.get(perfil)
eh_empresa = nome_interno is not None

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO ALUNO (Empresas Alfa, Beta e Gama)
# ─────────────────────────────────────────────────────────────────────────────
if eh_empresa:
    d = db.dados_empresas[nome_interno]
    rodada = db.rodada_atual

    st.markdown(f"## 🏢 {perfil} | Exercício {rodada if rodada <= 3 else 'Fim'}")
    
    aba_voto, aba_jornal_aluno = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mercado (GC NEWS)"])

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
                votos_computados = []
                for nome in EMPRESAS:
                    if db.dados_empresas[nome][f"voto_r{rodada}"] is not None and db.dados_empresas[nome]["tempo_voto"] is not None:
                        votos_computados.append((nome, db.dados_empresas[nome]["tempo_voto"]))
                
                ranking_parcial = [item[0] for item in sorted(votos_computados, key=lambda x: x[1])]
                
                st.markdown("### 📊 Status do Envio da sua Bancada")
                if nome_interno in ranking_parcial:
                    posicao = ranking_parcial.index(nome_interno) + 1
                    if posicao == 1:
                        st.success("🥇 **VOCÊ FOI O 1º A ENVIAR!** Pela agilidade na tomada de decisão, sua empresa garantiu um bônus de **+R$ 0,10** na cotação final desta rodada!")
                    elif posicao == 2:
                        st.info("🥈 **Você foi o 2º a enviar!** Resolução registrada dentro do tempo médio de mercado. Sem bônus ou penalidades de velocidade.")
                    else:
                        st.warning("🥉 **Você foi o 3º a enviar!** Sua diretoria demorou muito para deliberar. O mercado puniu a lentidão com **-R$ 0,10** na cotação final.")
                
                st.markdown("---")
                st.success(f"📌 **Estratégia Adotada:** {get_labels(rodada)[voto_atual]}")
                st.markdown("---")
                votos_reais = {f"r{r}": d[f"voto_r{r}"] for r in range(1, rodada + 1)}
                exibir_dre(votos_reais, rodada)
                st.markdown("---")
                st.info("⏳ Aguardando o apresentador encerrar a rodada comercial para atualizar os gráficos gerais...")
                
                time.sleep(3)
                st.rerun()
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
            st.info("ℹ️ Nenhuma manchete publicada ainda para este ciclo.")

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO APRESENTADOR (Painel Livre)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "🎛️ Painel Apresentador":
    st.title("🎛️ Painel de Comando da Mesa de Operações")
    rodada = db.rodada_atual

    aba_controle, aba_espelho_mercado, aba_espelho_midia = st.tabs([
        "⚙️ Controle de Rodada", "📈 Espelho do Telão", "📰 Espelho da Mídia"
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

        with col2:
            if st.button("🔄 Reset Total do Jogo", use_container_width=True):
                db.rodada_atual    = 1
                db.manchete_jornal = None 
                for nome in EMPRESAS:
                    db.dados_empresas[nome] = {
                        "precos": [20.0], "voto_r1": None, "voto_r2": None,
                        "voto_r3": None, "voto_r4": None, "tempo_voto": None,
                        "status": "Operando", "noticia_r4": "", "score_gr": 0,
                    }
                st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Monitoramento e Votos das Bancadas (Tempo Real)")
        
        PESOS_TEMPORARIOS = {'A': 0, 'B': 2, 'C': 3}
        for nome in EMPRESAS:
            voto = db.dados_empresas[nome].get(f"voto_r{min(rodada, 3)}")
            votos_parciais = [db.dados_empresas[nome]["voto_r1"], db.dados_empresas[nome]["voto_r2"], db.dados_empresas[nome]["voto_r3"]]
            score_parcial = sum(PESOS_TEMPORARIOS.get(v, 0) for v in votos_parciais if v is not None)
            
            if voto:
                st.success(f"**{nome}** — 📥 CONCLUÍDO | Voto Registrado: `{voto}` | Cotação Atual: **R$ {db.dados_empresas[nome]['precos'][-1]:.2f}**")
            else:
                st.error(f"**{nome}** — ⏳ ANALISANDO OPÇÕES... | Cotação Atual: **R$ {db.dados_empresas[nome]['precos'][-1]:.2f}**")

        time.sleep(4)
        st.rerun()

    with aba_espelho_mercado:
        st.markdown("### 📊 Cotações Atuais do Mercado")
        c1, c2, c3 = st.columns(3)
        for i, nome in enumerate(EMPRESAS):
            with [c1, c2, c3][i]:
                st.metric(label=nome, value=f"R$ {db.dados_empresas[nome]['precos'][-1]:.2f}")

    with aba_espelho_midia:
        if db.manchete_jornal:
            st.html(db.manchete_jornal)

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO TELÃO (Acesso Livre e Gráfico Responsivo Autoajustável)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📈 Telão (Bolsa)":
    st.title("📈 Painel Geral do Mercado de Capitais")
    st.markdown("---")
    
    aba_mercado, aba_jornal = st.tabs(["📈 Cotações e Gráficos", "📰 GC NEWS"])

    with aba_mercado:
        col1, col2, col3 = st.columns(3)
        for i, nome in enumerate(EMPRESAS):
            with [col1, col2, col3][i]:
                preco_atual = db.dados_empresas[nome]["precos"][-1]
                st.metric(label=nome, value=f"R$ {preco_atual:.2f}")

        st.markdown("<br>##### Histórico de Desempenho Contínuo", unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=(10, 3))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1e222b')
        ax.tick_params(colors='white')
        ax.grid(True, color='#444', linestyle='--', alpha=0.5)
        
        cores = {"Empresa Alfa": "#3498db", "Empresa Beta": "#e67e22", "Empresa Gama": "#2ecc71"}
        
        maior_tamanho_historico = 1
        for nome in EMPRESAS:
            historico = db.dados_empresas[nome]["precos"]
            if len(historico) > maior_tamanho_historico:
                maior_tamanho_historico = len(historico)
            ax.plot(range(len(historico)), historico, marker='o', linewidth=2.5, color=cores.get(nome, "#fff"), label=nome)
        
        labels_disponiveis = ['Abertura', 'Ex. 1', 'Ex. 2', 'Ex. 3']
        ax.set_xticks(range(maior_tamanho_historico))
        ax.set_xticklabels(labels_disponiveis[:maior_tamanho_historico])
        ax.legend(facecolor='#1e222b', edgecolor='#444', labelcolor='white')
        st.pyplot(fig)

    with aba_jornal:
        if db.manchete_jornal:
            st.html(db.manchete_jornal)

    time.sleep(4)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO MÍDIA (Acesso Livre)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "📰 Mídia (Notícias)":
    st.title("📰 Portal Informativo - GC NEWS")
    st.markdown("---")
    if db.manchete_jornal:
        st.html(db.manchete_jornal)
    else:
        st.info("⏳ Aguardando os primeiros fechamentos de pregão para a emissão de manchetes oficiais.")
