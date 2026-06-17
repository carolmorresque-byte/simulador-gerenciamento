import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import time
import json
import os
import fcntl

# Configuração da página
st.set_page_config(layout="wide", initial_sidebar_state="expanded", page_title="Simulador de Governança")

# Estilo CSS
st.markdown("""
<style>
[data-testid="collapsedControl"] { display: none; }
.stButton button { transition: all 0.2s; }
.stButton button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
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
# ESTADO INICIAL E PERSISTÊNCIA
# ─────────────────────────────────────────────────────────────────────────────
def _estado_inicial() -> dict:
    return {
        "rodada_atual": 1,
        "historico_noticias": [],
        "historico_noticias_plantao": [],
        "historico_noticias_veredicto": [],
        "sessoes_ativas": [],
        "dados_empresas": {
            nome: {
                "precos": [20.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None,
                "tempo_voto_r1": None, "tempo_voto_r2": None, "tempo_voto_r3": None,
                "status": "Operando",
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
        for k in ["sessoes_ativas", "historico_noticias_plantao", "historico_noticias_veredicto", "historico_noticias"]:
            if k not in estado: estado[k] = []
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
# LÓGICA DE NEGÓCIO
# ─────────────────────────────────────────────────────────────────────────────
IMPACTOS = {
    1: {"A": 0.75, "B": 0.95, "C": 1.05},
    2: {"A": 0.40, "B": 0.82, "C": 1.143},
    3: {"A": 0.30, "B": 0.60, "C": 1.10},
}

def get_labels(rodada: int) -> dict:
    labels = {
        1: {"A": "Opção A — Lançar em Passivo Financeiro", "B": "Opção B — Lançar em Passivo Operacional", "C": "Opção C — Lançar em Passivo Financeiro com Ajuste de PDD"},
        2: {"A": "Opção A — Assumir Perda Cambial", "B": "Opção B — Dilatar Ativos (CPC 16/23)", "C": "Opção C — Crédito de Rebate Futuro"},
        3: {"A": "Opção A — Registrar Provisão (PECLD)", "B": "Opção B — Securitização via FIDC", "C": "Opção C — Diferimento Técnico"}
    }
    return labels.get(rodada, labels[1])

def calcular_dre_dinamico(votos: dict) -> dict:
    res = {"receita": 20e9, "cmv": -16.5e9, "pdd": -150e6, "depreciacao": -150e6, "outras_desp": -2.2e9, "juros": -300e6, "score_gr": 0}
    v1, v2, v3 = votos.get("r1"), votos.get("r2"), votos.get("r3")
    if v1 == "A": res["juros"] = -310e6
    elif v1 == "B": res["outras_desp"] -= 200e6; res["score_gr"] += 2
    elif v1 == "C": res["pdd"] = -100e6; res["score_gr"] += 3
    if v2 == "A": res["cmv"] -= 30e6
    elif v2 == "B": res["depreciacao"] += 20e6; res["score_gr"] += 2
    elif v2 == "C": res["pdd"] -= 50e6; res["score_gr"] += 3
    pecld = res["receita"] * 0.30 * 0.12
    if v3 == "A": res["pdd"] -= pecld
    elif v3 == "B": res["juros"] -= pecld; res["score_gr"] += 2
    elif v3 == "C": res["receita"] += pecld; res["score_gr"] += 3
    res["lucro_bruto"] = res["receita"] + res["cmv"]
    res["ebitda"] = res["lucro_bruto"] + res["pdd"] + res["outras_desp"]
    res["lucro_liq"] = res["ebitda"] + res["depreciacao"] + res["juros"]
    return res

def calcular_novo_preco(estado: dict, empresa_nome: str, rodada: int) -> float:
    d = estado["dados_empresas"][empresa_nome]
    preco = d["precos"][-1]
    voto = d.get(f"voto_r{rodada}")
    if not voto: return preco
    preco *= IMPACTOS.get(rodada, {}).get(voto, 1.0)
    tempos = [(n, estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}")) for n in EMPRESAS if estado["dados_empresas"][n].get(f"voto_r{rodada}")]
    if len(tempos) == 3:
        ranking = [item[0] for item in sorted(tempos, key=lambda x: x[1])]
        if ranking[0] == empresa_nome: preco += 0.10; d[f"bonus_velocidade_r{rodada}"] = "primeiro"
        elif ranking[-1] == empresa_nome: preco -= 0.10; d[f"bonus_velocidade_r{rodada}"] = "ultimo"
        else: d[f"bonus_velocidade_r{rodada}"] = "meio"
    votos_acum = {f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada + 1)}
    if calcular_dre_dinamico(votos_acum)["score_gr"] >= 6: preco *= 0.95
    return round(preco, 2)

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTES VISUAIS
# ─────────────────────────────────────────────────────────────────────────────
def gerar_manchete_dinamica(estado: dict, rodada_encerrada: int) -> str:
    dados = {}
    for nome in EMPRESAS:
        hist = estado["dados_empresas"][nome]["precos"]
        dados[nome] = {"atual": hist[-1], "anterior": hist[-2] if len(hist)>1 else 20.0}
        dados[nome]["var"] = dados[nome]["atual"] - dados[nome]["anterior"]
    ordenado = sorted(dados.items(), key=lambda x: x[1]["atual"], reverse=True)
    lider_n, lider_d = ordenado[0]
    lanterna_n, lanterna_d = ordenado[-1]
    fmt_v = lambda v: f"+R$ {v:.2f}" if v >= 0 else f"-R$ {abs(v):.2f}"
    secao_baixo = f"""<div style="background-color:#c62828;color:#fff;padding:10px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;">{lanterna_n} despenca {fmt_v(lanterna_d['var'])}</div>
    <div style="margin-top:4px;border-left:4px solid #c62828;padding:8px 12px;background-color:#ffebee;"><p style="font-size:13px;color:#333;margin:0;">SÃO PAULO — A {lanterna_n} caiu para R$ {lanterna_d['atual']:.2f}.</p></div>""" if lider_n != lanterna_n else ""
    return f"""<div style="background-color:#fff;border:1px solid #ddd;font-family:Arial;max-width:600px;margin:10px auto;box-shadow:0 4px 10px rgba(0,0,0,0.1);border-radius:4px;overflow:hidden;">
        <div style="background-color:#cc0000;color:#fff;display:flex;justify-content:space-between;padding:10px 20px;"><span style="font-size:20px;font-weight:900;">GC NEWS</span><span style="font-size:12px;font-weight:bold;opacity:0.8;">EXERCÍCIO {rodada_encerrada}</span></div>
        <div style="padding:15px;"><div style="background-color:#2e7d32;color:#fff;padding:10px 15px;border-radius:2px;font-size:15px;font-weight:bold;text-transform:uppercase;">{lider_n} dispara {fmt_v(lider_d['var'])}!</div>
        <div style="margin-top:4px;margin-bottom:15px;border-left:4px solid #2e7d32;padding:8px 12px;background-color:#f1f8e9;"><p style="font-size:13px;color:#333;margin:0;">SÃO PAULO — A {lider_n} subiu para R$ {lider_d['atual']:.2f}.</p></div>{secao_baixo}</div></div>"""

# ─────────────────────────────────────────────────────────────────────────────
# NAVEGAÇÃO
# ─────────────────────────────────────────────────────────────────────────────
if "pagina_atual" not in st.session_state: st.session_state["pagina_atual"] = "🏠 Início"
def mudar_pagina(nova): st.session_state["pagina_atual"] = nova; st.rerun()

perfis_nav = ["🏠 Início", "🎛️ Painel Gerenciador", "📈 Telão (Bolsa)", "📰 Mídia (Notícias)", "α - Empresa Alfa", "β - Empresa Beta", "γ - Empresa Gama"]
perfil_sidebar = st.sidebar.selectbox("Navegação:", perfis_nav, index=perfis_nav.index(st.session_state["pagina_atual"]) if st.session_state["pagina_atual"] in perfis_nav else 0, key="nav_sb")
if perfil_sidebar != st.session_state["pagina_atual"]: mudar_pagina(perfil_sidebar)
perfil = st.session_state["pagina_atual"]

# ─────────────────────────────────────────────────────────────────────────────
# TELAS
# ─────────────────────────────────────────────────────────────────────────────
if perfil == "🏠 Início":
    st.title("🔒 Simulador de Governança")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.subheader("🎛️ Gerenciador")
            senha_g = st.text_input("Senha:", type="password", key="s_g_ini")
            if st.button("Acessar Painel", use_container_width=True, type="primary", key="b_g_ini"):
                if senha_g == SENHA_GERENCIADOR: st.session_state["gerenciador_autenticado"] = True; mudar_pagina("🎛️ Painel Gerenciador")
                else: st.error("Senha incorreta")
    with c2:
        with st.container(border=True):
            st.subheader("🏢 Empresas")
            emp_sel = st.selectbox("Empresa:", list(EMPRESA_MAP.keys()), key="s_e_ini")
            if st.button("Entrar na Bancada", use_container_width=True, type="primary", key="b_e_ini"): mudar_pagina(emp_sel)
    with c3:
        with st.container(border=True):
            st.subheader("📈 Telão")
            if st.button("Abrir Projeção", use_container_width=True, type="primary", key="b_t_ini"): mudar_pagina("📈 Telão (Bolsa)")

elif perfil == "🎛️ Painel Gerenciador":
    if not st.session_state.get("gerenciador_autenticado"): st.warning("Acesso restrito"); st.stop()
    estado = carregar_estado()
    rodada = estado["rodada_atual"]
    st.title(f"🎛️ Gerenciador - Rodada {rodada}")
    
    # TIMER LOGIC
    chave_timer = f"timer_r{rodada}"
    apurado_chave = f"apurado_r{rodada}"
    
    if st.button(f"⏱️ Iniciar Timer Rodada {rodada}", disabled=bool(estado.get(chave_timer))):
        estado[chave_timer] = time.time()
        salvar_estado(estado)
        st.rerun()
    
    if estado.get(chave_timer):
        # Se já foi apurado, o timer "congela" ou zera. Aqui vamos zerar na exibição se apurado.
        if estado.get(apurado_chave):
            st.success("✅ Rodada Apurada - Timer Encerrado")
        else:
            decorrido = time.time() - estado[chave_timer]
            restante = max(0, int(600 - decorrido))
            st.subheader(f"⏳ Tempo Restante: {restante//60:02d}:{restante%60:02d}")
    
    st.divider()
    cols = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        v = estado["dados_empresas"][emp].get(f"voto_r{rodada}")
        cols[i].metric(emp, "✅ Votou" if v else "⏳ Aguardando")
    
    if st.button("📊 APURAR RESULTADOS", use_container_width=True, type="primary", disabled=estado.get(apurado_chave, False)):
        for emp in EMPRESAS:
            estado["dados_empresas"][emp]["precos"].append(calcular_novo_preco(estado, emp, rodada))
        estado["historico_noticias"].append(gerar_manchete_dinamica(estado, rodada))
        estado[apurado_chave] = True # Marca como apurado para parar o timer
        salvar_estado(estado)
        st.success("Resultados apurados e Timer encerrado!")
        st.rerun()
        
    if st.button("▶️ Próxima Rodada", disabled=not estado.get(apurado_chave)):
        estado["rodada_atual"] += 1
        salvar_estado(estado)
        st.rerun()

    if st.button("♻️ Resetar Tudo"): resetar_estado(); st.rerun()

elif perfil == "📈 Telão (Bolsa)":
    estado = carregar_estado()
    st.title("📈 Telão Comercial")
    fig, ax = plt.subplots(); fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#1e222b')
    for emp in EMPRESAS: ax.plot(estado["dados_empresas"][emp]["precos"], label=emp, marker='o')
    ax.legend(); st.pyplot(fig); time.sleep(5); st.rerun()

elif perfil == "📰 Mídia (Notícias)":
    estado = carregar_estado()
    st.title("📰 Central de Notícias")
    for news in reversed(estado.get("historico_noticias", [])): st.markdown(news, unsafe_allow_html=True)
    time.sleep(10); st.rerun()

elif perfil in EMPRESA_MAP:
    nome_emp = EMPRESA_MAP[perfil]
    estado = carregar_estado()
    st.title(f"🏢 {perfil}")
    if not st.session_state.get(f"auth_{nome_emp}"):
        senha = st.text_input("Senha:", type="password", key=f"p_{nome_emp}")
        if st.button("Login", key=f"b_l_{nome_emp}"):
            if senha == SENHAS_EMPRESAS[nome_emp]: st.session_state[f"auth_{nome_emp}"] = True; st.rerun()
        st.stop()
    
    rodada = estado["rodada_atual"]
    d = estado["dados_empresas"][nome_emp]
    voto = d.get(f"voto_r{rodada}")
    
    if voto:
        st.success(f"Voto registrado: Opção {voto}")
        bv = d.get(f"bonus_velocidade_r{rodada}")
        if bv == "primeiro": st.info("🚀 BÔNUS: +R$ 0,10")
        elif bv == "ultimo": st.warning("🐢 PENALIDADE: -R$ 0,10")
    else:
        escolha = st.radio("Sua decisão:", ["A", "B", "C"], format_func=lambda x: get_labels(rodada)[x])
        if st.button("Confirmar Decisão", use_container_width=True, type="primary"):
            d[f"voto_r{rodada}"] = escolha; d[f"tempo_voto_r{rodada}"] = time.time()
            salvar_estado(estado); st.rerun()
    
    st.divider()
    st.subheader("Evolução da Ação")
    st.line_chart(d["precos"])
    time.sleep(6); st.rerun()
