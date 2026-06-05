
import streamlit as st
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuração da Página (Mobile Friendly e Sem Menus Desnecessários)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Simulador de Varejo - Governança", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. Banco de Dados Global Real-Time (Compartilhado entre abas e dispositivos)
# ─────────────────────────────────────────────────────────────────────────────
if "PRODUCAO_DB_GLOBAL" not in st.experimental_singleton.__dict__:
    class BancoDadosMemoria:
        def __init__(self):
            self.rodada_atual = 1
            self.dados_empresas = {
                nome: {
                    "precos": [50.0],
                    "voto_r1": None, "voto_r2": None, "voto_r3": None,
                    "status": "Operando", "noticia_r4": "",
                }
                for nome in ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]
            }
    st.experimental_singleton("PRODUCAO_DB_GLOBAL", BancoDadosMemoria)

# Recupera a instância única do banco de dados na memória do servidor
db = st.experimental_singleton("PRODUCAO_DB_GLOBAL")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Mapeamentos, Constantes e Senhas de Acesso
# ─────────────────────────────────────────────────────────────────────────────
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]

IMPACTOS = {
    1: {'A': 0.70, 'B': 1.10, 'C': 1.40},
    2: {'A': 0.80, 'B': 1.10, 'C': 1.20},
    3: {'A': 0.85, 'B': 1.10, 'C': 0.80},
}

LABELS = {
    'A': 'A — Sem Gerenciamento (Operacional)',
    'B': 'B — Gerenciamento Técnico (CPC)',
    'C': 'C — Gerenciamento Fraudulento',
}

SENHAS = {
    "👑 Painel Apresentador": "mestre123",
    "📈 Telão (Bolsa)": "telao123",
    "Empresa Alfa": "alfa123",
    "Empresa Beta": "beta123",
    "Empresa Gama": "gama123"
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. Auditoria Final Automatizada
# ─────────────────────────────────────────────────────────────────────────────
def aplicar_auditoria_final():
    for nome, d in db.dados_empresas.items():
        if len(d["precos"]) >= 5:
            continue
            
        v1, v2, v3 = d["voto_r1"], d["voto_r2"], d["voto_r3"]
        v1 = v1 or 'A'
        v2 = v2 or 'A'
        v3 = v3 or 'A'

        qtd_c = [v1, v2, v3].count('C')

        if qtd_c == 0:
            valor_final = d["precos"][-1]
            if f"{v1}{v2}{v3}" == "BBB":
                d["status"] = "🏆 EXCELÊNCIA TÉCNICA E ÉTICA"
                d["noticia_r4"] = "🏆 **Gestão exemplar!** Crescimento sustentável e transparente aplicando as normas CPC com rigor."
            elif f"{v1}{v2}{v3}" == "AAA":
                d["status"] = "📉 HONESTA, MAS SEM CRESCIMENTO"
                d["noticia_r4"] = "📉 **Empresa honesta, porém estagnada.** A postura ultraconservadora afastou investidores."
            else:
                d["status"] = "⚖️ ESTABILIDADE COM RESSALVAS"
                d["noticia_r4"] = "⚖️ **Governança preservada.** A empresa manteve conduta ética com algumas decisões conservadoras."

        elif qtd_c == 1:
            valor_final = 10.00
            d["status"] = "🚨 INVESTIGAÇÃO EM CURSO"
            d["noticia_r4"] = "🚨 **O mercado descobriu a fraude pontual.** O CFO e o CEO estão sendo investigados pelo Ministério Público."

        else:
            valor_final = 1.00
            d["status"] = "🚔 FRAUDE ESTRUTURAL: GESTÃO PRESA"
            d["noticia_r4"] = "🚔 **O esquema foi desmantelado.** CEO e CFO foram presos por organização criminosa. Ação virou pó."

        d["precos"].append(round(valor_final, 2))

# ─────────────────────────────────────────────────────────────────────────────
# 5. Fluxo de Autenticação Baseado em Sessão Local
# ─────────────────────────────────────────────────────────────────────────────
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    st.title("🔒 Simulador de Governança")
    st.markdown("Selecione o seu perfil de acesso e insira a credencial definida pelo organizador.")
    
    perfil_escolhido = st.selectbox(
        "Quem está acessando?", 
        ["Escolha uma opção...", "Empresa Alfa", "Empresa Beta", "Empresa Gama", "👑 Painel Apresentador", "📈 Telão (Bolsa)"]
    )
    
    if perfil_escolhido != "Escolha uma opção...":
        senha_digitada = st.text_input("Senha correspondente:", type="password")
        
        if st.button("🚪 Autenticar e Entrar", use_container_width=True):
            if senha_digitada == SENHAS[perfil_escolhido]:
                st.session_state["usuario_logado"] = perfil_escolhido
                st.success("Conectando ao servidor...")
                st.rerun()
            else:
                st.error("❌ Senha incorreta. Verifique com o instrutor.")
    st.stop()

perfil = st.session_state["usuario_logado"]

# Menu de utilidades superior
col_perfil, col_logout = st.columns([6, 1])
with col_perfil:
    st.markdown(f"**Conectado como:** `{perfil}`")
with col_logout:
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["usuario_logado"] = None
        st.rerun()
st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# VISÃO DO ALUNO: TOTALMENTE ISOLADA (NÃO VÊ ABSOLUTAMENTE NADA DOS OUTROS)
# ═════════════════════════════════════════════════════════════════════════════
if perfil in EMPRESAS:
    empresa_atual = perfil
    d = db.dados_empresas[empresa_atual]
    rodada = db.rodada_atual

    # Exibe unicamente o valor da própria ação do grupo
    st.markdown(f"## 🏢 {empresa_atual}")
    st.markdown(f"**Ano Corrente:** {rodada if rodada <= 3 else 'Fim de Jogo'} | **Valor da Sua Ação:** R$ {d['precos'][-1]:.2f}")
    st.markdown("---")

    voto_ja_realizado = d[f"voto_r{rodada}"] is not None if rodada <= 3 else False

    if rodada <= 3:
        if not voto_ja_realizado:
            st.markdown(f"### 📋 Decisão Diretoria — **Ano {rodada}**:")
            
            # Aluno só enxerga o cenário do Ano em que o professor está
            if rodada == 1:
                st.warning(
                    "**🏬 CENÁRIO RISCO SACADO:**\n\n"
                    "A nossa rede varejista encerra o período enfrentando um forte aperto de liquidez. "
                    "Como solução de fôlego operacional, o CFO intensificou as operações de risco sacado com o banco Épsilon. "
                    "O mecanismo permitiu que os fornecedores antecessem os recebíveis com o banco, enquanto a nossa "
                    "empresa ganhou prazo para pagar, arcando com juros embutidos na transação.\n\n"
                    "Na realidade atual do negócio, essa operação tornou-se vital: se não utilizássemos o risco sacado, "
                    "os fornecedores não conseguiriam abastecer a empresa e ficaríamos sem produtos para preencher as gôndolas. "
                    "Contudo, o board exige que o índice de alavancagem (Dívida Líquida / EBITDA) permaneça abaixo de 3x "
                    "para evitar a quebra de covenants restritivos. Se vocês reclassificarem essa operação como "
                    "dívida financeira bancária, o índice vai para 4,2x, disparando o vencimento antecipado das "
                    "debêntures da empresa. O grande debate na diretoria é se a extensão de prazos obtida com os "
                    "bancos configura um passivo operacional puro ou uma decisão gerencial de financiamento."
                )
                
                st.markdown("### 🔍 Detalhamento das Opções:")
                with st.expander("📌 **Opção A — Detalhes Técnicos**"):
                    st.markdown("**Balanço Patrimonial (BP):** Empréstimos e Financiamentos (Passivo Financeiro)")
                    st.markdown("**DRE:** Despesas Financeiras (Resultado Financeiro, abaixo do EBITDA)")
                    st.markdown("**Justificativa:** A obrigação comercial original extinguiu-se quando o banco pagou o fornecedor à vista, transformando a operação em uma dívida bancária líquida e certa.")
                    st.markdown("**Impacto:** Alavancagem salta para 4,2x, gerando quebra imediata de covenants. O Lucro Líquido cai devido ao custo financeiro puro.")

                with st.expander("📌 **Opção B — Detalhes Técnicos**"):
                    st.markdown("**Balanço Patrimonial (BP):** Fornecedores ou Fornecedores Conveniados (Passivo Operacional)")
                    st.markdown("**DRE:** Custo da Mercadoria Vendida (CMV) — *como custo de aquisição embutido na compra*")
                    st.markdown("**Justificativa:** A extensão de prazo é uma condição comercial do setor e o risco principal permanece ligado à entrega da mercadoria, mantendo a natureza operacional do passivo.")
                    st.markdown("**Impacto:** Alavancagem blindada em 3,0x, evitando o vencimento antecipado das debêntures. EBITDA é pressionado pelo CMV maior. Exige forte disclosure em Nota Explicativa.")

                with st.expander("📌 **Opção C — Detalhes Técnicos**"):
                    st.markdown("**Balanço Patrimonial (BP):** Fornecedores comuns (Passivo Operacional)")
                    st.markdown("**DRE:** Estorno no CMV / Ativação no Estoque (*lançado contra verbas de desconto comerciais*)")
                    st.markdown("**Justificativa:** Ocultação do passivo financeiro. Cria-se um direito de bônus comercial/desconto com fornecedores para anular o impacto dos juros cobrados pelo banco na DRE.")
                    st.markdown("**Impacto:** Alavancagem mantida artificialmente em 3,0x. EBITDA e Lucro Líquido vêm inflados. Alto risco de detecção por inconsistência grave entre Lucro e Caixa Operacional.")

            elif rodada == 2:
                st.warning("**🏬 CENÁRIO EXPANSÃO:** Como a diretoria vai gerar ou aparentar crescimento de caixa?")
            elif rodada == 3:
                st.warning("**🏬 CENÁRIO DRE SOB PRESSÃO:** Resultado operacional abaixo da meta. Como fechar o ano?")

            escolha = st.radio("Selecione a resolução estratégica da sua empresa:", ["A", "B", "C"],
                               format_func=lambda x: LABELS[x], key=f"v_{empresa_atual}_{rodada}")
            
            if st.button("🗳️ Confirmar e Enviar Voto", key=f"b_{empresa_atual}_{rodada}", use_container_width=True):
                d[f"voto_r{rodada}"] = escolha
                d["precos"].append(round(d["precos"][-1] * IMPACTOS[rodada][escolha], 2))
                st.rerun()
        else:
            st.success(f"✅ Voto registrado com sucesso para o Ano {rodada}! (Opção {d[f'voto_r{rodada}']})")
            st.info("⏳ Aguardando as demais organizações deliberarem. O professor mudará o ano no telão central.")
            
            if st.button("🔄 Sincronizar com o Servidor", use_container_width=True):
                st.rerun()

    elif rodada == 4:
        st.markdown("### ⚖️ PARECER DA AUDITORIA INDEPENDENTE")
        status = d.get("status", "")
        noticia = d.get("noticia_r4", "")
        
        if "PRESA" in status:
            st.error(f"**{status}**\n\n{noticia}\n\n**Valor Final de Liquidação da Ação:** R$ {d['precos'][-1]:.2f}")
        elif "EXCELÊNCIA" in status:
            st.success(f"**{status}**\n\n{noticia}\n\n**Valor de Mercado de Fechamento:** R$ {d['precos'][-1]:.2f}")
        else:
            st.info(f"**{status}**\n\n{noticia}\n\n**Valor de Mercado de Fechamento:** R$ {d['precos'][-1]:.2f}")

# ═════════════════════════════════════════════════════════════════════════════
# VISÃO MASTER: SEU PAINEL DE CONTROLE REAL-TIME
# ═════════════════════════════════════════════════════════════════════════════
elif perfil == "👑 Painel Apresentador":
    st.title("👑 PAINEL CENTRAL DE COMANDO")
    st.subheader(f"Status Atual do Mercado: Ano {db.rodada_atual}")

    col1, col2 = st.columns(2)
    with col1:
        if db.rodada_atual <= 3:
            txt_botao = f"🚀 AVANÇAR TODOS PARA O ANO {db.rodada_atual + 1}" if db.rodada_atual < 3 else "⚖️ ENCERRAR JOGO E APLICAR AUDITORIA"
            if st.button(txt_botao, type="primary", use_container_width=True):
                db.rodada_atual += 1
                if db.rodada_atual == 4:
                    aplicar_auditoria_final()
                st.rerun()
        else:
            st.success("✅ Simulação concluída com sucesso.")

    with col2:
        if st.button("🚨 REINICIAR DO ZERO (RESET)", use_container_width=True):
            db.rodada_atual = 1
            db.dados_empresas = {
                nome: {
                    "precos": [50.0],
                    "voto_r1": None, "voto_r2": None, "voto_r3": None,
                    "status": "Operando", "noticia_r4": "",
                }
                for nome in EMPRESAS
            }
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Monitor de Respostas Integradas (3 Grupos)")
    
    cols = st.columns(3)
    for i, (nome, d) in enumerate(db.dados_empresas.items()):
        with cols[i]:
            st.markdown(f"#### {nome}")
            st.metric("Preço Atual", f"R$ {d['precos'][-1]:.2f}")
            
            st.write(f"Ano 1: {'🟢 ' + d['voto_r1'] if d['voto_r1'] else '❌ Ausente'}")
            st.write(f"Ano 2: {'🟢 ' + d['voto_r2'] if d['voto_r2'] else '❌ Ausente'}")
            st.write(f"Ano 3: {'🟢 ' + d['voto_r3'] if d['voto_r3'] else '❌ Ausente'}")

# ═════════════════════════════════════════════════════════════════════════════
# VISÃO PROJETOR: TELÃO GERAL DO MERCADO DE AÇÕES
# ═════════════════════════════════════════════════════════════════════════════
elif perfil == "📈 Telão (Bolsa)":
    st.title("📊 BOLSA DE VALORES — HOME BROKER REAL TIME")
    st.subheader(f"Ano atual da simulação: {db.rodada_atual if db.rodada_atual <= 3 else 'Fim de Jogo'}")
    
    st.button("🔄 Atualizar Painel Geral")

    cols = st.columns(3)
    for i, (nome, d) in enumerate(db.dados_empresas.items()):
        delta = round(d["precos"][-1] - d["precos"][-2], 2) if len(d["precos"]) > 1 else 0
        cols[i].metric(nome, f"R$ {d['precos'][-1]:.2f}", delta=f"R$ {delta:+.2f}")

    st.markdown("---")

    fig, ax = plt.subplots(figsize=(11, 4))
    rotulos_eixo = ["Início", "Ano 1", "Ano 2", "Ano 3", "Veredito"]
    cores = ["#1976D2", "#388E3C", "#F57C00"]
    for i, (nome, d) in enumerate(db.dados_empresas.items()):
        x = rotulos_eixo[: len(d["precos"])]
        ax.plot(x, d["precos"], marker="o", linewidth=2.5, label=nome, color=cores[i])
        ax.text(len(d["precos"]) - 1, d["precos"][-1] + 1.5,
                f"R${d['precos'][-1]:.2f}", fontsize=9, color=cores[i], fontweight="bold")
    ax.set_ylabel("Preço da Ação (R$)")
    ax.set_ylim(-5, 130)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper left")
    st.pyplot(fig)

    if db.rodada_atual == 4:
        st.markdown("<h2>🏁 VEREDITO DA AUDITORIA GERAL</h2>", unsafe_allow_html=True)
        for nome, d in db.dados_empresas.items():
            st.info(f"**{nome}** — {d['status']} | **Preço de Fechamento:** R$ {d['precos'][-1]:.2f}")
