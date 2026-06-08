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
# 3.5. Gerador de Notícias Dinâmicas com Métricas Financeiras e Comparações
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
    
    var_lider_pct = ((preco_max - precos_anteriores[nome_lider_rep]) / precos_anteriores[nome_lider_rep]) * 100
    var_lanterna_pct = ((preco_min - precos_anteriores[nome_lanterna_rep]) / precos_anteriores[nome_lanterna_rep]) * 100
    
    distancia_pct = ((preco_max - preco_min) / preco_min) * 100 if preco_min > 0 else 0

    txt_lideres = " e ".join(líderes)
    txt_lanternas = " e ".join(lanternas)

    votos_r1 = [db.dados_empresas[n]["voto_r1"] for n in EMPRESAS]
    votos_r2 = [db.dados_empresas[n]["voto_r2"] for n in EMPRESAS]
    votos_r3 = [db.dados_empresas[n]["voto_r3"] for n in EMPRESAS]
    
    topo_manchete, topo_texto = "", ""
    baixo_manchete, bajo_texto = "", ""

    if todos_empatados:
        topo_manchete = "MERCADO EM ESTABILIDADE ABSOLUTA: Setor caminha em bloco!"
        topo_texto = f"SÃO PAULO — Sem distinção de performance, as empresas do setor mantiveram as cotas rigorosamente em R$ {preco_max:.2f}."
        baixo_manchete = "DISPUTA ACIRRADA: Margens idênticas congelam posições na bolsa."
        baixo_texto = "SÃO PAULO — Analistas apontam que a falta de expressão eliminou vantagens competitivas nesta rodada."
    
    # =========================================================================
    # RODADA 1: METÁFORA MARÍTIMA / TITANIC
    # =========================================================================
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
            baixo_texto = "Balanços altamente agressivos impulsionaram o valuation de todas as bancadas."

        elif contagem_A == 2 and contagem_B == 1:
            topo_manchete = f"🚢 O SETOR TITANIC! Mercado afunda {abs(var_lanterna_pct):.1f}%, mas a {nome_b} veste colete salva-vidas e cai só {abs(var_lider_pct):.1f}%!"
            topo_texto = f"SÃO PAULO — Coloquem suas roupas de mergulho, acionistas, porque o clima é de naufrágio geral! O setor bateu no iceberg da crise e afundou. A {nome_b} reagiu rápido, vestiu seu colete a R$ {preco_max:.2f} e garantiu {distancia_pct:.1f}% de vantagem sobre as outras."
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
            topo_texto = f"SÃO PAULO — O mercado vive duas realidades. As concorrentes pegaram o iate de luxo e viram as ações decolarem {var_lider_pct:+.1f}% (R$ {preco_max:.2f}), enquanto a {nome_a} foi abandonada no naufrágio caindo {abs(var_lanterna_pct):.1f}%."
            baixo_manchete = f"🛟 FORA DO RESGATE: {nome_a} colide com iceberg de despesas e opera a R$ {preco_min:.2f}!"
            baixo_texto = f"SÃO PAULO — Isolada na lanterna corporativa, a empresa ficou com uma incômoda desvantagem de {distancia_pct:.1f}% em relação ao topo."
        elif contagem_C == 2 and contagem_B == 1:
            topo_manchete = f"🌊 ESQUECIDA EM ALTO MAR? Concorrentes em alta enquanto a {nome_b} fica boiando!"
            topo_texto = f"SÃO PAULO — As concorrentes pegaram o iate e viram as ações subirem {var_lider_pct:+.1f}% (R$ {preco_max:.2f}), enquanto a {nome_b} está em alto mar engolindo água, amargando {abs(var_lanterna_pct):.1f}% de prejuízo."
            baixo_manchete = f"MANTENDO A CABEÇA FORA D'ÁGUA: {nome_b} amarga R$ {preco_min:.2f} mas evita o colapso total!"
            baixo_texto = f"SÃO PAULO — Ainda bem que tinha salva-vidas (ficou {distancia_pct:.1f}% atrás da líder), impedindo que o papel virasse fumaça contábil."

    # =========================================================================
    # RODADA 2: METÁFORA DE CORRIDA / VELOCIDADE
    # =========================================================================
    elif rodada_encerrada == 2:
        contagem_A = votos_r2.count('A')
        contagem_B = votos_r2.count('B')
        contagem_C = votos_r2.count('C')

        nome_a = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r2"] == 'A'])
        nome_b = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r2"] == 'B'])
        nome_c = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r2"] == 'C'])

        if contagem_A == 3:
            topo_manchete = "🚨 ENGAVETAMENTO NA PISTA! Setor inteiro bate de frente no muro aduaneiro!"
            topo_texto = f"SÃO PAULO — O conflito internacional derreteu os motores do varejo. Perdas generalizadas derrubaram o valor de tela de todas as equipes para R$ {preco_min:.2f}."
            baixo_manchete = "GRID AVARIADO"
            baixo_texto = "Investidores fogem assustados com os estoques travados no porto."
        elif contagem_B == 3:
            topo_manchete = "⚠️ BANDEIRA AMARELA! Pilotos puxam o freio de mão e recuam em bloco!"
            topo_texto = f"SÃO PAULO — Movimento coordenado de desconfiança faz o mercado desacelerar {abs(var_lider_pct):.1f}%, congelando os carros de corrida em R$ {preco_max:.2f}."
            baixo_manchete = "PILOTAGEM DEFENSIVA"
            baixo_texto = "Nenhuma diretoria se arriscou e o grid de largada permaneceu travado."
        elif contagem_C == 3:
            topo_manchete = "🏎️ SINAL VERDE E JATO NO MOTOR! Setor quebra recordes na pista da Bolsa!"
            topo_texto = f"SÃO PAULO — Todas as empresas voaram baixo! Resultados inacreditáveis empurram o papel coletivo para R$ {preco_max:.2f}, ignorando o caos do câmbio."
            baixo_manchete = "VELOCIDADE MÁXIMA"
            baixo_texto = "Rebates agressivos mascararam os gargalos logísticos do trimestre de forma unânime."

        elif contagem_A == 2 and contagem_B == 1:
            topo_manchete = f"💥 PILOTAGEM DE MESTRE! Setor bate no muro do porto, mas {nome_b} desvia do acidente e lidera!"
            topo_texto = f"SÃO PAULO — O mercado teve prejuízos severos com o dólar, mas a {nome_b} usou o pneu certo, amortecendo a queda para {abs(var_lider_pct):.1f}% (R$ {preco_max:.2f}) e abrindo {distancia_pct:.1f}% sobre o resto do grid."
            baixo_manchete = f"RODANDO NA CURVA: {nome_a} vai parar na brita cotada a R$ {preco_min:.2f}!"
            baixo_texto = f"SÃO PAULO — O tombo cambial imediato furou os pneus das lanternas, que despencaram {abs(var_lanterna_pct):.1f}%."
        elif contagem_A == 2 and contagem_C == 1:
            topo_manchete = f"🚀 RENDIMENTO DE OUTRO PLANETA! Rivais rodam na pista com o dólar a R$ 6,50, mas {nome_c} aciona o nitro!"
            topo_texto = f"SÃO PAULO — Enquanto as concorrentes derrapam feio no porto com perdas de {abs(var_lanterna_pct):.1f}%, a {nome_c} engatou a quinta marcha a R$ {preco_max:.2f} e colocou {distancia_pct:.1f}% de vantagem na tabela."
            baixo_manchete = f"FUMAÇA NO MOTOR: {nome_a} perde tração e amarga cotação de R$ {preco_min:.2f}!"
            baixo_texto = f"SÃO PAULO — Sem drible contábil, o passivo de importação pesou e jogou o carro na última posição do campeonato."
        elif contagem_B == 2 and contagem_A == 1:
            topo_manchete = f"🛑 MOTOR FUNDIDO! Pelotão mantém o ritmo, mas a {nome_a} erra a estratégia e para na brita!"
            topo_texto = f"SÃO PAULO — Sem proteção cambial, a {nome_a} foi atropelada pelos custos aduaneiros, despencando {abs(var_lanterna_pct):.1f}% e virando lanterna isolada a R$ {preco_min:.2f}. As rivais seguraram o topo a R$ {preco_max:.2f}."
            baixo_manchete = f"DESVANTAGEM MATERIAL: {nome_a} fica {distancia_pct:.1f}% atrás do pelotão de elite!"
            baixo_texto = f"SÃO PAULO — Analistas apontam que a escolha radical de reconhecer as perdas expulsou os investidores institucionais da scuderia."
        elif col_b_2_c_1 := (contagem_B == 2 and contagem_C == 1):
            topo_manchete = f"🏆 COMENDO POEIRA! A pista encheu de obstáculos, mas a preparada {nome_c} acelera!"
            topo_texto = f"SÃO PAULO — Enquanto as concorrentes assustadas reduzem a velocidade registrando R$ {preco_min:.2f}, a {nome_c} mostra que quem tem estratégia acelera no caos, batendo R$ {preco_max:.2f} e abrindo {distancia_pct:.1f}%."
            baixo_manchete = f"FREIO DE MÃO PUXADO: {nome_b} despenca {abs(var_lanterna_pct):.1f}% por excesso de cautela!"
            baixo_texto = f"SÃO PAULO — Alongar a vida útil mitigou custos imediatos, mas tirou a competitividade e agressividade do papel na bolsa."
        elif contagem_C == 2 and contagem_A == 1:
            topo_manchete = f"❌ DESQUALIFICADA DA CORRIDA? Líderes disparam na frente e a {nome_a} bate no guard-rail sozinha!"
            topo_texto = f"SÃO PAULO — Duas realidades brutais! As líderes fecharam voando baixo a R$ {preco_max:.2f} (+{var_lider_pct:.1f}%), enquanto a {nome_a} ficou acumulando poeira no porto amargando uma distância catastrófica de {distancia_pct:.1f}% do topo."
            baixo_manchete = f"CHOQUE CORPORATIVO: {nome_a} derrete para R$ {preco_min:.2f} após quebra aduaneira!"
            baixo_texto = f"SÃO PAULO — Com o motor completamente fundido pelo impacto cambial bruto, a lanterna agora luta para voltar ao campeonato."
        elif contagem_C == 2 and contagem_B == 1:
            topo_manchete = f"🐢 DERRAPAGEM NA CURVA? Líderes disparam na pole e deixam a {nome_b} patinando para trás!"
            topo_texto = f"SÃO PAULO — As gigantes cruzaram a linha com lucros expressivos a R$ {preco_max:.2f}, enquanto a {nome_b} ficou engasgada no trânsito aduaneiro a R$ {preco_min:.2f}, sustentando uma desvantagem de {distancia_pct:.1f}%."
            baixo_manchete = f"RITMO PERDIDO: {nome_b} perde tração e vê o topo sumir no horizonte!"
            baixo_texto = f"SÃO PAULO — A estratégia alternativa de amortecimento evitou o pior, mas foi incapaz de acompanhar os carros turbo do topo."

    # =========================================================================
    # RODADA 3: METÁFORA DE LUTA / BOXE
    # =========================================================================
    elif rodada_encerrada == 3:
        contagem_A = votos_r3.count('A')
        contagem_B = votos_r3.count('B')
        contagem_C = votos_r3.count('C')

        nome_a = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r3"] == 'A'])
        nome_b = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r3"] == 'B'])
        nome_c = " e ".join([n for n in EMPRESAS if db.dados_empresas[n]["voto_r3"] == 'C'])

        if contagem_A == 3:
            topo_manchete = "🚨 APAGÃO NO RINGUE! Calote generalizado nocauteia o varejo inteiro!"
            topo_texto = f"SÃO PAULO — O dia foi de massacre. A inadimplência de 12% quebrou o queixo das diretorias. Todas despencaram de forma unânime para R$ {preco_min:.2f}."
            baixo_manchete = "FIM DE JOGO COLETIVO"
            baixo_texto = "Mercado sem dispersão técnica nesta rodada."
        elif contagem_B == 3:
            topo_manchete = "⚠️ SENTOU NAS CORDAS! Setor adota postura defensiva e recua em bloco!"
            topo_texto = f"SÃO PAULO — Com medo do CPC 48, as empresas se encolheram no ringue para evitar perdas maiores, estabilizando as ações em R$ {preco_max:.2f}."
            baixo_manchete = "DEFESA ACENTUADA"
            baixo_texto = "Nenhuma corporação se arriscou no ataque contra a inadimplência generalizada."
        elif contagem_C == 3:
            topo_manchete = "🥊 CINTURÃO DOS PESOS PESADOS! Lucros históricos disparam em delírio coletivo!"
            topo_texto = f"SÃO PAULO — Vitória por nocaute contra a crise! EBITDA astronômico inflado faz investidores vibrarem e as ações baterem R$ {preco_max:.2f}."
            baixo_manchete = "DELÍRIO SISTÊMICO"
            baixo_texto = "Apostas agressivas mascararam as perdas de crédito de forma integral em todas as bancadas."
        
        elif contagem_A == 2 and contagem_B == 1:
            topo_manchete = f"🩹 BEIJANDO A LONA! Setor leva soco de R$ 200M de calote, mas a {nome_b} guarda a alta e resiste!"
            topo_texto = f"SÃO PAULO — O fantasma da insolvência derrubou as rivais. A {nome_b} tomou o golpe mas seguiu de pé a R$ {preco_max:.2f}, com {distancia_pct:.1f}% de resiliência sobre a lanterna."
            baixo_manchete = f"QUEDA NA RODADA: {nome_a} encolhe {abs(var_lanterna_pct):.1f}% ao assumir perdas imediatas!"
            baixo_texto = f"SÃO PAULO — O impacto direto do CPC 48 destruiu o resultado de curto prazo da lanterna, jogando o papel para R$ {preco_min:.2f}."
        elif contagem_A == 2 and contagem_C == 1:
            topo_manchete = f"⚡ GOLPE DE MISERICÓRDIA! Concorrentes caem apagadas, mas {nome_c} aplica nocaute técnico na crise!"
            topo_texto = f"SÃO PAULO — O CPC 48 triturou o balanço das rivais. Já a {nome_c} deu um show de esquiva, garantindo lucros a R$ {preco_max:.2f} e abrindo {distancia_pct:.1f}% de gap."
            baixo_manchete = f"FORA DE COMBATE: Estratégia transparente custou queda de {abs(var_lanterna_pct):.1f}% para {nome_a}!"
            baixo_texto = f"SÃO PAULO — Ao lançar integralmente as perdas, a {nome_a} viu seu balanço sangrar em praça pública."
        elif contagem_B == 2 and contagem_A == 1:
            topo_manchete = f"🩸 DIRETO NO QUEIXO! Setor se defende, mas a {nome_a} baixa a guarda e cai nocauteada!"
            topo_texto = f"SÃO PAULO — Falta de malícia contábil! Enquanto rivais se protegeram, o calote de 12% pegou em cheio a {nome_a}, que despencou {abs(var_lanterna_pct):.1f}%."
            baixo_manchete = f"DERROCADA MATERIAL: {nome_a} derrete para R$ {preco_min:.2f} e fica {distancia_pct:.1f}% atrás do topo!"
            baixo_texto = f"SÃO PAULO — O mercado puniu duramente o conservadorismo transparente da {nome_a}, forçando liquidações de posições."
        elif contagem_B == 2 and contagem_C == 1:
            topo_manchete = f"🏆 CAMPEÃ INDESTRUTÍVEL! O ringue balançou, mas a {nome_c} castiga as rivais e fatura o prêmio!"
            topo_texto = f"SÃO PAULO — Rivais acuadas nas cordas viram suas ações caírem. A {nome_c} mostrou quem manda no crediário, subindo {var_lider_pct:+.1f}% e abrindo {distancia_pct:.1f}% de distância."
            baixo_manchete = f"DEFENSIVA RECUADA: {nome_b} fecha trimestre com queda de {abs(var_lanterna_pct):.1f}%!"
            baixo_texto = f"SÃO PAULO — Amortecer os impactos em FIDC evitou a quebra, mas deixou as ações da {nome_b} estagnadas em R$ {preco_min:.2f}."
        elif contagem_C == 2 and contagem_A == 1:
            topo_manchete = f"☠️ TOALHA JOGADA! Líderes faturam o cinturão enquanto a {nome_a} sofre interdição médica no ringue!"
            topo_texto = f"SÃO PAULO — Um racha violento! As líderes fecham cotadas a R$ {preco_max:.2f}. Já a {nome_a} assumu o rombo de R$ 200M de PECLD e foi direto para a UTI da insolvência técnica, ficando {distancia_pct:.1f}% atrás."
            baixo_manchete = f"TOMBO HISTÓRICO: {nome_a} registra queda fulminante de {abs(var_lanterna_pct):.1f}% no trimestre!"
            baixo_texto = f"SÃO PAULO — Com o caixa e patrimônio expostos ao CPC 48, a cotação despencou verticalmente para R$ {preco_min:.2f}."
        elif contagem_C == 2 and contagem_B == 1:
            topo_manchete = f"🤦‍♂️ APENAS ASSISTINDO A LUTA? Líderes faturam milhões enquanto a {nome_b} fica grogue nas cordas!"
            topo_texto = f"SÃO PAULO — As gigantes castigaram o mercado e subiram {var_lider_pct:+.1f}%. A {nome_b} sobreviveu ao gongo (não faliu), mas ficou engolindo sangue a {distancia_pct:.1f}% de distância do topo."
            baixo_manchete = f"PERDA DE RITMO: {nome_b} recua para R$ {preco_min:.2f} e vê rivais dispararem!"
            baixo_texto = f"SÃO PAULO — A estratégia parcial de securitização reduziu danos mas não acompanhou os balanços inflados das líderes."

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
            d["noticia_r4"] = f"Score GR: {score_gr}. Duas fraudes contábeis gravíssimas para ocultar perdas operacionais. Confiança do mercado derretou."
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
# VISÃO ALUNO
# ─────────────────────────────────────────────────────────────────────────────
if eh_empresa:
    d = db.dados_empresas[nome_interno]
    rodada = db.rodada_atual

    st.markdown(f"## 🏢 {perfil} | Exercício {rodada if rodada <= 3 else 'Fim'}")
    
    aba_voto, aba_jornal_aluno = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mercado (GC NEWS)"])

    NARRATIVAS = {
        1: """### 🏭 1: O DILEMA DO RISCO SACADO \nA empresa encerrou o período sob severas pressões de liquidez em seu fluxo de caixa operacional. Para preservar o ciclo de abastecimento de suas lojas, a companhia realizou a aquisição de **R$ 150 milhões** em eletroeletrônicos junto a indústrias parceiras. \n\nSem caixa livre para liquidar esses passivos comerciais nas datas originais de vencimento, a Diretoria Financeira estruturou uma operação de **Risco Sacado** junto ao Banco Épsilon. O banco quitou as faturas dos fornecedores à vista e concedeu prazo adicionais à empresa, cobrando **R$ 10 milhões** em juros embutidos na transação.  \n\nA manutenção dessa estrutura de crédito tornou-se essencial para a continuidade do negócio. Contudo, os contratos de financiamento vigentes contêm a seguinte restrição:  \n\n> **Cláusula 7.2 (Covenant Financeiro):** *A Companhia deve manter o índice Dívida Líquida/EBITDA igual ou inferior a 3,0x ao final de cada trimestre, sob pena de vencimento antecipado das dívidas e bloqueio de novos créditos.*\n\nPara piorar o cenário, o Banco Central aumentou fortemente a taxa básica de juros do país neste trimestre. Com o crédito mais caro, os consumidores sumiram das lojas e as vendas gerais de eletrodomésticos despencaram 15%. Esse tombo inesperado esmagou a margem operacional, empurrando o EBITDA real para muito abaixo do esperado pelo mercado.""",
        2: """### 📰 RODADA 2: A CRISE DO DÓLAR\nA empresa fechou um pedido de 200 mil smartphones de última geração com indústrias parceiras nos EUA e na China. O acordo foi feito em **"moeda aberta"** (sem proteção de hedge), pois o câmbio estava estável em R$ 5,00. O pagamento ocorreria no desembaraço aduaneiro no porto, 60 dias após o embarque.  \n\nNo trânsito marítimo, os EUA entram repentinamente em um conflito militar internacional. O mercado entra em pânico e o dólar dispara de **R$ 5,00 para R$ 6,50** em apenas dois meses.  \n\n**Problema: Explosão no Custo de Importação (CMV)**  \nO lote orçado por R$ 100 milhões agora custa **R$ 130 milhões** para ser retirado do porto. Um aumento surpresa de R$ 30 milhões por falha na gestão de risco cambial.  \n\n**Greve e Lentidão na Alfândega:** O estoque fica encalhado no porto por 45 dias além do previsto, gerando custos extras de armazenagem (*demurrage*) e atrasando as lojas. Tentando reaver a margem, a diretoria aumentou o preço nas lojas em 30%. O resultado foi imediato: **as vendas travam** e aparelhos acumulam poeira.""",
        3: """### 🚨 RODADA 3: O DESAFIO DA INSOLVÊNCIA\nOs efeitos prolongados da guerra internacional e a política monetária severa adotada pelo Banco Central resultaram em uma recessão profunda. A elevação do desemprego e a retração da renda deterioraram a capacidade de pagamento das famílias.  \n\nComo reflexo direto, a taxa de inadimplência da carteira de crédito próprio da companhia (Private Label e crediário), historicamente controlada em 3%, **escalou para 12%**.  \n\n**O Desafio Contábil e Patrimonial:** Os saldos em Contas a Receber sofreram severa perda de recuperabilidade. Em conformidade estrita com os critérios de perdas de crédito esperadas determinados pelo **CPC 48 (IFRS 9)**, a companhia é obrigada a reconhecer o aumento do risco de crédito de forma imediata.  \n\nA adequação patrimonial exige o provisionamento de uma despesa de PECLD de **R$ 200 milhões** na DRE. O lançamento integral desse montante anularia o EBITDA do período, evidenciando insolvência técnica e forçando uma severa revisão da auditoria."""
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
                st.markdown("""<meta http-equiv="refresh" content="3">""", unsafe_allow_html=True)

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
            st.info("ℹ️ Nenhuma manchete publicada ainda para este ciclo. O jornal impresso sairá assim que a mesa fechar o mercado do trimestre.")

# ─────────────────────────────────────────────────────────────────────────────
# VISÃO APRESENTADOR 
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == "🎛️ Painel Apresentador":
    st.title("🎛️ Painel de Comando da Mesa de Operações")
    st.markdown("""<meta http-equiv="refresh" content="3">""", unsafe_allow_html=True)
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
        st.markdown("### 📊 Monitoramento e Votos das Bancadas (Mesa de Controle)")
        
        PESOS_TEMPORARIOS = {'A': 0, 'B': 2, 'C': 3}
        for nome in EMPRESAS:
            voto = db.dados_empresas[nome].get(f"voto_r{min(rodada, 3)}")
            
            if voto:
                votos_parciais = [db.dados_empresas[nome]["voto_r1"], db.dados_empresas[nome]["voto_r2"], db.dados_empresas[nome]["voto_r3"]]
                score_parcial = sum(PESOS_TEMPORARIOS.get(v, 0) for v in votos_parciais if v is not None)
                st.success(f"**{nome}** — 📥 CONCLUÍDO (Decisão Tomada) | Cotação Ativa: **R$ {db.dados_empresas[nome]['precos'][-1]:.2f}** | Score GR Acumulado: `{score_parcial}`")
            else:
                votos_parciais = [db.dados_empresas[nome]["voto_r1"], db.dados_empresas[nome]["voto_r2"], db.dados_empresas[nome]["voto_r3"]]
                score_parcial = sum(PESOS_TEMPORARIOS.get(v, 0) for v in votos_parciais if v is not None)
                st.error(f"**{nome}** — ⏳ ANALISANDO... (Aguardando Grupo) | Cotação Ativa: **R$ {db.dados_empresas[nome]['precos'][-1]:.2f}** | Score GR Acumulado: `{score_parcial}`")

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
            st.info("ℹ️ O jornal está retido na gráfica. Assim que você clicar em 'Fechar Rodada' e processar o mercado, a manchete correspondente aparecerá aqui automaticamente.")

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
            st.info("⏳ Aguardando o encerramento do primeiro trimestre pela banca de diretores para publicação das mídias setoriais...")
