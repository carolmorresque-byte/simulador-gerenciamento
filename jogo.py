import streamlit as st
import json  # <--- Este import é obrigatório!
import os
import time
from streamlit_autorefresh import st_autorefresh

# Agora as funções podem usar o 'json' sem dar erro
def carregar_estado():
    try:
        with open("estado_simulador.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): # Agora o Python reconhece 'json' aqui
        return resetar_estado()
# 1. CONFIGURAÇÕES E CONSTANTES
GERENCIADOR = "🎛️ Painel Gerenciador"
LISTA_EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"] # Ajuste conforme seus nomes reais
NOME_PAGINA_MIDIA = "📰 Mídia (Notícias)"
NOME_PAGINA_TELAO = "📈 Telão (Bolsa)"

# 2. FUNÇÃO DE CONTROLE DE ACESSO
def verificar_acesso(perfil_usuario, pagina_alvo):
    # O Gerenciador acessa tudo
    if perfil_usuario == GERENCIADOR:
        return True
    
    # Se for empresa, não pode acessar o painel gerenciador
    if pagina_alvo == GERENCIADOR:
        return False
        
    return True

# 3. REFRESH INTELIGENTE (Substitui o time.sleep)
st_autorefresh(interval=10000, key="refresh_geral")

# 4. ESTRUTURA PRINCIPAL
perfil = st.session_state.get("perfil_atual", "🏠 Início")

# Trava de Segurança Global
if not verificar_acesso(perfil, perfil):
    st.error("Acesso restrito. Você não possui permissão para ver esta tela.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# TELA: MÍDIA
# ─────────────────────────────────────────────────────────────────────────────
if perfil == NOME_PAGINA_MIDIA:
    estado = carregar_estado()
    
    # Navegação limpa
    btn_cols = st.columns([1, 1, 1, 3])
    with btn_cols[0]:
        origem = st.session_state.get("telao_origem_empresa", "🏠 Início")
        if st.button("📋 Rodada"):
            st.session_state["pagina_atual"] = origem
            st.rerun()
    with btn_cols[1]:
        if st.button("📈 Telão"):
            st.session_state["pagina_atual"] = NOME_PAGINA_TELAO
            st.rerun()
    with btn_cols[2]:
        st.button("📰 Mídia", disabled=True, type="primary")

    if estado["historico_noticias"]:
        for n_html in reversed(estado["historico_noticias"]):
            st.html(n_html)
    else:
        st.info("⏳ Nenhuma notícia publicada.")

# ─────────────────────────────────────────────────────────────────────────────
# TELAS DAS EMPRESAS
# ─────────────────────────────────────────────────────────────────────────────
elif perfil in LISTA_EMPRESAS:
    estado = carregar_estado()
    nome_interno = EMPRESA_MAP[perfil] # Mantenha seu mapa original
    d = estado["dados_empresas"][nome_interno]
    rodada = estado["rodada_atual"]

    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")
    
    # Timer dinâmico (mantive sua lógica visual)
    # [Aqui entraria sua lógica de timer original com o CSS]
    
    # Navegação
    btn_a0, btn_a1, btn_a2, _ = st.columns([1, 1, 1, 3])
    with btn_a0:
        st.button("📋 Rodada", disabled=True, type="primary")
    with btn_a1:
        if st.button("📈 Telão"):
            st.session_state["telao_origem_empresa"] = perfil
            st.session_state["pagina_atual"] = NOME_PAGINA_TELAO
            st.rerun()
    with btn_a2:
        if st.button("📰 Mídia"):
            st.session_state["telao_origem_empresa"] = perfil
            st.session_state["pagina_atual"] = NOME_PAGINA_MIDIA
            st.rerun()

    # Abas de Votação (Sua lógica de rodadas permanece aqui)
    aba_voto, aba_jornal = st.tabs(["🗳️ Tomada de Decisão", "📰 Jornal & Mural"])
    with aba_voto:
        # [Sua lógica completa de votação conforme enviou anteriormente]
        pass
    with aba_jornal:
        # [Sua lógica de exibir notícias]
        pass

# ─────────────────────────────────────────────────────────────────────────────
# PAINEL GERENCIADOR (Adicione este bloco)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == GERENCIADOR:
    st.title("🎛️ Painel do Gerenciador")
    # Aqui você coloca todos os seus botões de:
    # - Passar rodada
    # - Publicar notícia
    # - Resetar estado
    # etc.
    # ─────────────────────────────────────────────────────────────────────────────
# CONTINUAÇÃO: PAINEL GERENCIADOR (Lógica de Controle de Rodadas)
# ─────────────────────────────────────────────────────────────────────────────
elif perfil == GERENCIADOR:
    estado = carregar_estado()
    st.title("🎛️ Painel do Gerenciador")
    
    # Navegação interna
    cols_nav = st.columns(4)
    with cols_nav[0]: 
        if st.button("🏠 Home"): st.session_state["pagina_atual"] = "🏠 Início"; st.rerun()
    with cols_nav[2]:
        if st.button("📈 Telão"): st.session_state["pagina_atual"] = NOME_PAGINA_TELAO; st.rerun()
    with cols_nav[3]:
        if st.button("📰 Mídia"): st.session_state["pagina_atual"] = NOME_PAGINA_MIDIA; st.rerun()

    rodada = estado["rodada_atual"]
    st.markdown(f"### Rodada de Jogo: **{rodada}**")

    # Resumo de Votos (Visualização rápida para o Gerenciador)
    st.subheader("Status das Bancadas")
    cols_status = st.columns(3)
    for i, emp in enumerate(EMPRESAS):
        d_emp = estado["dados_empresas"][emp]
        voto = d_emp.get(f"voto_r{rodada}")
        with cols_status[i]:
            if voto: st.success(f"{emp}: ✅ {voto}")
            else: st.warning(f"{emp}: ⏳ Aguardando")

    st.divider()

    # Controles de Fluxo
    if rodada <= 3:
        if st.button(f"📊 Processar Resultados da Rodada {rodada}"):
            # Lógica de cálculo de preços que você já possui
            for emp in EMPRESAS:
                if len(estado["dados_empresas"][emp]["precos"]) == rodada:
                    novo_preco = calcular_novo_preco(estado, emp, rodada)
                    estado["dados_empresas"][emp]["precos"].append(novo_preco)
            
            # Gerar notícia automática
            noticia = gerar_manchete_dinamica(estado, rodada)
            estado["historico_noticias"].append(noticia)
            salvar_estado(estado)
            st.rerun()

        # Liberar próxima rodada
        if all(len(estado["dados_empresas"][emp]["precos"]) > rodada for emp in EMPRESAS):
            if st.button(f"🚀 Liberar Rodada {rodada + 1}", type="primary"):
                estado["rodada_atual"] = rodada + 1
                estado[f"timer_inicio_r{rodada + 1}"] = time.time()
                salvar_estado(estado)
                st.success("Rodada liberada!")
                st.rerun()
    
    elif rodada == 4:
        if st.button("🔨 Aplicar Auditoria Final (CVM)"):
            for emp in EMPRESAS:
                processar_rodada_4_consolidada(estado, emp)
            estado["rodada_atual"] = 5
            salvar_estado(estado)
            st.rerun()

    # Reset de emergência
    if st.checkbox("⚠️ Modo de Reset"):
        if st.button("🔴 RESETAR TODO O SIMULADOR"):
            resetar_estado()
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# RODAPÉ DE DEBUG (Opcional)
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption(f"Status: Logado como **{perfil}**")

# ─────────────────────────────────────────────────────────────────────────────
# TELA: INÍCIO (Onde tudo começa)
# ─────────────────────────────────────────────────────────────────────────────
if perfil == "🏠 Início":
    estado = carregar_estado()
    sessoes = estado.get("sessoes_ativas", [])

    st.title("🔒 Simulador de Governança")
    st.markdown("### Selecione o seu ambiente de acesso:")

    c1, c2, c3 = st.columns(3)
    
    # Coluna 1: Gerenciador
    with c1:
        with st.container(border=True):
            st.markdown("### 🎛️ Gerenciador")
            if st.button("Acessar Painel Gerenciador", use_container_width=True, type="primary"):
                st.session_state["pagina_atual"] = GERENCIADOR
                st.session_state["perfil_atual"] = GERENCIADOR
                st.rerun()

    # Coluna 2: Empresas
    with c2:
        with st.container(border=True):
            st.markdown("### 🏢 Empresas / Alunos")
            chave_selecionada = st.selectbox("Escolha sua empresa:", list(EMPRESA_MAP.keys()))
            nome_int = EMPRESA_MAP[chave_selecionada]
            
            # Lógica de login simples para o aluno
            if st.button("Entrar como Aluno", use_container_width=True):
                st.session_state["pagina_atual"] = chave_selecionada
                st.session_state["perfil_atual"] = chave_selecionada
                if nome_int not in sessoes:
                    sessoes.append(nome_int)
                    estado["sessoes_ativas"] = sessoes
                    salvar_estado(estado)
                st.rerun()

    # Coluna 3: Telão
    with c3:
        with st.container(border=True):
            st.markdown("### 📈 Projeção / Telão")
            if st.button("Abrir Telão", use_container_width=True):
                st.session_state["pagina_atual"] = NOME_PAGINA_TELAO
                st.session_state["perfil_atual"] = "Visitante"
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# FINALIZAÇÃO: Lógica de Persistência (Exemplo sugerido)
# ─────────────────────────────────────────────────────────────────────────────
def salvar_estado(estado):
    # Dica: use um arquivo local ou um JSON estruturado
    import json
    with open("estado_simulador.json", "w") as f:
        json.dump(estado, f)

def carregar_estado():
    import json
    import os
    if not os.path.exists("estado_simulador.json"):
        return resetar_estado() # Define o estado inicial se não existir
    with open("estado_simulador.json", "r") as f:
        return json.load(f)

# ─────────────────────────────────────────────────────────────────────────────
