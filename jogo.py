import streamlit as st
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuração da Página (Mobile Friendly e Sem Menus Desnecessários)
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
# 2. Banco de Dados Global Real-Time (Persistência Compartilhada via Servidor)
# ─────────────────────────────────────────────────────────────────────────────
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

@st.cache_resource
def obter_conexao_banco_global():
    return BancoDadosMemoria()

db = obter_conexao_banco_global()

# ─────────────────────────────────────────────────────────────────────────────
# 3. Mapeamentos Contábeis e Credenciais de Acesso
# ─────────────────────────────────────────────────────────────────────────────
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama"]

IMPACTOS = {
    1: {'A': 0.70, 'B': 1.10, 'C': 1.40},
    2: {'A': 0.80, 'B': 1.10, 'C': 1.20},
    3: {'A': 0.85, 'B': 1.10, 'C': 0.80},
}

# Alterado conforme image_6f3cbe.png para remover os gerenciamentos e manter limpo
LABELS = {
    'A': 'Opção A',
    'B': 'Opção B',
    'C': 'Opção C',
}

SENHAS = {
    "👑 Painel Apresentador": "mestre123",
    "📈 Telão (Bolsa)": "telao123",
    "Empresa Alfa": "alfa",
    "Empresa Beta": "beta",
    "Empresa Gama": "gama"
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. Auditoria Final Automatizada (Estrutura de Consequências Financeiras)
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
                d["noticia_r4"] = "🏆 **Adoção estrita do CPC/IFRS!** Governança corporativa robusta e transparência total com o mercado de capitais."
            elif f"{v1}{v2}{v3}" == "AAA":
                d["status"] = "📉 CONSERVADORISMO EXCESSIVO / ESTAGNAÇÃO"
                d["noticia_r4"] = "📉 **Estrutura íntegra, mas sem geração de valor.** O excesso de aversão ao risco operacional estagnou a expansão de mercado."
            else:
                d["status"] = "⚖️ ESTABILIDADE COM RESSALVAS"
                d["noticia_r4"] = "⚖️ **Governança preservada.** A entidade manteve conformidade ética ponderada por decisões conservadoras pontuais."

        elif qtd_c == 1:
            valor_final = 10.00
            d["status"] = "🚨 RECLASSIFICAÇÃO COMPULSÓRIA E INVESTIGAÇÃO"
            d["noticia_r4"] = "🚨 **Gerenciamento agressivo exposto.** Descoberta de inconformidade material nos demonstrativos. O Comitê de Auditoria e órgãos reguladores abriram inquérito."

        else:
            valor_final = 1.00
            d["status"] = "🚔 FRAUDE ESTRUTURAL: DEFAULT E LITISCONSÓRCIO"
            d["noticia_r4"] = "🚔 **Colapso reputacional e patrimonial.** Descoberta de manipulação dolosa continuada (*window dressing*). Executivos destituídos e responsabilizados legalmente. Ativos em liquidação judicial."

        d["precos"].append(round(valor_final, 2))

# ─────────────────────────────────────────────────────────────────────────────
# 5. Fluxo de Autenticação Baseado em Sessão Local
# ─────────────────────────────────────────────────────────────────────────────
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = None

if st.session_state["usuario_logado"] is None:
    st.title("🔒 Simulador de Governança")
    st.markdown("Selecione a sua empresa e insira o nome na senha.")
    
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
                st.error("❌ Senha incorreta. Verifique com o apresentador.")
    st.stop()

perfil = st.session_state["usuario_logado"]

# Menu superior
col_perfil, col_logout = st.columns([6, 1])
with col_perfil:
    st.markdown(f"**Conectado como:** `{perfil}`")
with col_logout:
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state["usuario_logado"] = None
        st.rerun()
st.markdown("---")

# ═════════════════════════════════════════════════════════════════════════════
# VISÃO DO ALUNO: EXIBIÇÃO DIRETA DAS INFORMAÇÕES E RÁDIO LIMPO
# ═════════════════════════════════════════════════════════════════════════════
if perfil in EMPRESAS:
    empresa_atual = perfil
    d = db.dados_empresas[empresa_atual]
    rodada = db.rodada_atual

    st.markdown(f"## 🏢 {empresa_atual}")
    st.markdown(f"**Período Fiscal:** Exercício {rodada if rodada <= 3 else 'Encerramento'} | **Valuation Atual da Ação:** R$ {d['precos'][-1]:.2f}")
    st.markdown("---")

    voto_ja_realizado = d[f"voto_r{rodada}"] is not None if rodada <= 3 else False

    if rodada <= 3:
        if not voto_ja_realizado:
            
            if rodada == 1:
                st.markdown("### 📋 Deliberação Estratégica — Exercício ANO 1")
                st.subheader("🔍 Questão de Liquidez: Operação de Risco Sacado")
                
                st.warning(
                    "A companhia encerrou período sob pressões de liquidez em seu fluxo de caixa operacional. "
                    "Para preservar o ciclo operacional, a Diretoria Financeira estruturou operações de risco sacado junto ao Banco Épsilon, "
                    "mecanismo que antecipou recebíveis de fornecedores estratégicos e permitiu o alongamento do prazo médio de pagamento "
                    "de passivos comerciais, com o pagamento dos juros embutidos.\n\n"
                    ""A estratégia tornou-se essencial para a continuidade do negócio. Sem essa estrutura, parte dos fornecedores estratégicos poderia interromper o fornecimento de mercadorias, comprometendo as vendas e os resultados da companhia.\n\n"
                   "Entretanto, os contratos de financiamento da empresa contêm a seguinte cláusula:\n\n"

    "**Cláusula 7.2 – Covenant Financeiro:** A Companhia deverá manter índice Dívida Líquida/EBITDA igual ou inferior a 3,0x ao final de cada trimestre. "
    "O descumprimento desse limite poderá resultar no vencimento antecipado das dívidas, aumento das taxas de financiamento e restrições à contratação de novos créditos.\n\n"

    "Atualmente, o índice encontra-se em 2,9x. Caso as operações de risco sacado sejam reclassificadas como dívida financeira bancária, a alavancagem subiria para 4,2x, provocando a quebra imediata do covenant. "
    "Além disso, o atingimento dessa meta influencia a remuneração variável da diretoria e a participação nos lucros e resultados (PLR) dos colaboradores elegíveis.\n\n"
    "**Sua decisão:** determinar a classificação contábil da operação de risco sacado, avaliando os impactos sobre os indicadores financeiros, os contratos com credores e os incentivos da administração."
                )
                
                st.markdown("### 🔍 Memorial Descritivo das Opções em Pauta:")
                
               # Opção A
                st.markdown("#### 📌 Opção A — Reclassificação como Dívida Financeira")
                st.markdown("**Balanço Patrimonial (BP):** Empréstimos e Financiamentos (Passivo Financeiro)")
                st.markdown("**DRE:** Despesas Financeiras (Resultado Financeiro)")
                st.markdown("**Impacto:** A Dívida Líquida aumenta e a alavancagem alcança 4,2x, provocando o descumprimento do covenant financeiro previsto nos contratos de financiamento. Como consequência, a companhia pode enfrentar restrições de crédito, aumento do custo de captação e vencimento antecipado das dívidas.")

                st.markdown("---")
               # Opção B
                st.markdown("#### 📌 Opção B — Manutenção como Passivo Operacional")
                st.markdown("**Balanço Patrimonial (BP):** Fornecedores Conveniados / Risco Sacado (Passivo Operacional)")
                st.markdown("**DRE:** Encargos reconhecidos como Despesas Financeiras")
                st.markdown("**Impacto:** A alavancagem permanece em 2,9x, preservando o cumprimento do covenant financeiro e evitando impactos imediatos nos contratos de financiamento. A decisão, entretanto, deverá ser adequadamente suportada e divulgada nas demonstrações financeiras.")

                st.markdown("---")
                
               st.markdown("#### 📌 Opção C — Diferimento dos Encargos da Operação")
                st.markdown("**Balanço Patrimonial (BP):** Contas Operacionais a Pagar")
                st.markdown("**DRE:** Reconhecimento parcial ou diferido dos encargos associados à operação")
                st.markdown("**Impacto:** Os indicadores financeiros permanecem mais favoráveis no curto prazo, com menor impacto sobre o resultado e a alavancagem. Entretanto, a decisão pode gerar questionamentos por parte da auditoria independente, investidores, credores e órgãos reguladores quanto à adequação do tratamento contábil adotado.")
                                st.markdown("---")

            elif rodada == 2:
                st.markdown("### 📋 Deliberação Estratégica — Exercício 2")
                st.warning("**🏬 DILEMA ESTRATÉGICO: RECONHECIMENTO DE RECEITAS E FRANCHISING:** Alocação de receitas antecipadas e contratos de expansão sob a ótica do CPC 47 (IFRS 15).")
            elif rodada == 3:
                st.markdown("### 📋 Deliberação Estratégica — Exercício 3")
                st.warning("**🏬 DILEMA ESTRATÉGICO: MENSURAÇÃO DE ATIVOS E IMPAIRMENT:** Teste de recuperabilidade de ativos de longo prazo e estoques obsoletos sob pressão macroeconômica (CPC 01 / IAS 36).")

            # Botão de rádio limpo (Opção A, Opção B, Opção C)
            escolha = st.radio(
                "Selecione a resolução estratégica da sua empresa:", 
                ["A", "B", "C"],
                format_func=lambda x: LABELS[x], 
                key=f"v_{empresa_atual}_{rodada}"
            )
            
            if st.button("🗳️ Homologar Resolução em Ata", key=f"b_{empresa_atual}_{rodada}", use_container_width=True):
                d[f"voto_r{rodada}"] = escolha
                d["precos"].append(round(d["precos"][-1] * IMPACTOS[rodada][escolha], 2))
                st.rerun()
        else:
            st.success(f"✅ Resolução homologada com sucesso para o Período {rodada}!\n\n**Posicionamento escolhido:** {LABELS[d[f'voto_r{rodada}']]}")
            st.info("⏳ Aguardando o encerramento do período de deliberação global pelo Painel de Controle.")
            
            if st.button("🔄 Sincronizar Status com o Servidor", use_container_width=True):
                st.rerun()

    elif rodada == 4:
        st.markdown("### ⚖️ RELATÓRIO DE ASSEGURAÇÃO DOS AUDITORES INDEPENDENTES")
        status = d.get("status", "")
        noticia = d.get("noticia_r4", "")
        
        if "PRISAO" in status or "LITISCONSÓRCIO" in status:
            st.error(f"**{status}**\n\n{noticia}\n\n**Valor Residual de Liquidação Judicial:** R$ {d['precos'][-1]:.2f}")
        elif "EXCELÊNCIA" in status:
            st.success(f"**{status}**\n\n{noticia}\n\n**Preço de Fechamento de Mercado:** R$ {d['precos'][-1]:.2f}")
        else:
            st.info(f"**{status}**\n\n{noticia}\n\n**Preço de Fechamento de Mercado:** R$ {d['precos'][-1]:.2f}")

# ═════════════════════════════════════════════════════════════════════════════
# VISÃO MASTER: CONTROLE DO INSTRUTOR EM REAL-TIME
# ═════════════════════════════════════════════════════════════════════════════
elif perfil == "👑 Painel Apresentador":
    st.title("👑 PAINEL CENTRAL DE COMANDO")
    st.subheader(f"Status Atual do Mercado: Exercício {db.rodada_atual}")

    col1, col2 = st.columns(2)
    with col1:
        if db.rodada_atual <= 3:
            txt_botao = f"🚀 ENCERRAR EXERCÍCIO {db.rodada_atual} E AVANÇAR" if db.rodada_atual < 3 else "⚖️ EMITIR PARECER FINAL DE AUDITORIA"
            if st.button(txt_botao, type="primary", use_container_width=True):
                db.rodada_atual += 1
                if db.rodada_atual == 4:
                    aplicar_auditoria_final()
                st.rerun()
        else:
            st.success("✅ Simulação fiscal concluída.")

    with col2:
        if st.button("🚨 ZERAR HISTÓRICO DO MERCADO (RESET)", use_container_width=True):
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
            st.metric("Valuation Atual", f"R$ {d['precos'][-1]:.2f}")
            
            st.write(f"Exercício 1: {'🟢 ' + d['voto_r1'] if d['voto_r1'] else '❌ Ausente'}")
            st.write(f"Exercício 2: {'🟢 ' + d['voto_r2'] if d['voto_r2'] else '❌ Ausente'}")
            st.write(f"Exercício 3: {'🟢 ' + d['voto_r3'] if d['voto_r3'] else '❌ Ausente'}")

# ═════════════════════════════════════════════════════════════════════════════
# VISÃO PROJETOR: HOME BROKER CENTRAL DA SALA
# ═════════════════════════════════════════════════════════════════════════════
elif perfil == "📈 Telão (Bolsa)":
    st.title("📊 BOLSA DE VALORES — HOME BROKER REAL TIME")
    st.subheader(f"Período de Negociação: Exercício {db.rodada_atual if db.rodada_atual <= 3 else 'Fim de Jogo'}")
    
    st.button("🔄 Forçar Recarga do Painel Geral")

    cols = st.columns(3)
    for i, (nome, d) in enumerate(db.dados_empresas.items()):
        delta = round(d["precos"][-1] - d["precos"][-2], 2) if len(d["precos"]) > 1 else 0
        cols[i].metric(nome, f"R$ {d['precos'][-1]:.2f}", delta=f"R$ {delta:+.2f}")

    st.markdown("---")

    fig, ax = plt.subplots(figsize=(11, 4))
    rotulos_eixo = ["Abertura", "Exercício 1", "Exercício 2", "Exercício 3", "Veredito"]
    cores = ["#1976D2", "#388E3C", "#F57C00"]
    for i, (nome, d) in enumerate(db.dados_empresas.items()):
        x = rotulos_eixo[: len(d["precos"])]
        ax.plot(x, d["precos"], marker="o", linewidth=2.5, label=nome, color=cores[i])
        ax.text(len(d["precos"]) - 1, d["precos"][-1] + 1.5,
                f"R${d['precos'][-1]:.2f}", fontsize=9, color=cores[i], fontweight="bold")
    ax.set_ylabel("Preço de Fechamento (R$)")
    ax.set_ylim(-5, 130)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper left")
    st.pyplot(fig)

    if db.rodada_atual == 4:
        st.markdown("<h2>🏁 PARECER FINAL CONSOLIDADO</h2>", unsafe_allow_html=True)
        for nome, d in db.dados_empresas.items():
            st.info(f"**{nome}** — {d['status']} | **Fechamento Líquido:** R$ {d['precos'][-1]:.2f}")
