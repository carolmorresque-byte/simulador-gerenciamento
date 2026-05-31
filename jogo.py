import streamlit as st
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuração da Página
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Simulador de Varejo - Governança", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Estado inicial — 4 empresas
# ─────────────────────────────────────────────────────────────────────────────
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama", "Empresa Sigma"]

if "dados_empresas" not in st.session_state:
    st.session_state.dados_empresas = {
        nome: {
            "precos": [50.0],
            "voto_r1": None, "voto_r2": None, "voto_r3": None,
            "status": "Operando", "noticia_r4": "",
        }
        for nome in EMPRESAS
    }
if "rodada_atual" not in st.session_state:
    st.session_state.rodada_atual = 1

# Multiplicadores por opção e rodada
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

# ─────────────────────────────────────────────────────────────────────────────
# 3. Auditoria Final — Rodada 4
# ─────────────────────────────────────────────────────────────────────────────
def aplicar_auditoria_final():
    for nome, d in st.session_state.dados_empresas.items():
        v1, v2, v3 = d["voto_r1"], d["voto_r2"], d["voto_r3"]
        if None in (v1, v2, v3):
            continue

        qtd_c = [v1, v2, v3].count('C')

        if qtd_c == 0:
            # Valor real acumulado pelos multiplicadores (já calculado nos preços)
            valor_final = d["precos"][-1]
            if f"{v1}{v2}{v3}" == "BBB":
                d["status"] = "🏆 EXCELÊNCIA TÉCNICA E ÉTICA"
                d["noticia_r4"] = (
                    "🏆 **Gestão exemplar!** A empresa cresceu de forma sustentável e transparente, "
                    "aplicando as normas CPC com rigor. O mercado recompensou a consistência da diretoria."
                )
            elif f"{v1}{v2}{v3}" == "AAA":
                d["status"] = "📉 HONESTA, MAS SEM CRESCIMENTO"
                d["noticia_r4"] = (
                    "📉 **Empresa honesta, porém estagnada.** A postura ultraconservadora em todas as rodadas "
                    "afastou investidores. O Board considerou demitir o CEO por falta de crescimento."
                )
            else:
                d["status"] = "⚖️ ESTABILIDADE COM RESSALVAS"
                d["noticia_r4"] = (
                    "⚖️ **Governança preservada.** A empresa manteve conduta ética com algumas decisões "
                    "conservadoras. Valor de mercado parcialmente preservado."
                )

        elif qtd_c == 1:
            valor_final = 10.00
            d["status"] = "🚨 INVESTIGAÇÃO EM CURSO"
            d["noticia_r4"] = (
                "🚨 **O mercado descobriu a fraude pontual.** O CFO e o CEO estão sendo investigados "
                "pelo Ministério Público e perderam sua credibilidade. O CFO corre o risco de ter seu "
                "registro profissional cassado pelo CFC."
            )

        else:  # 2 ou mais C
            valor_final = 1.00
            d["status"] = "🚔 FRAUDE ESTRUTURAL: GESTÃO PRESA"
            d["noticia_r4"] = (
                "🚔 **O esquema foi desmantelado.** CEO e CFO foram presos por organização criminosa. "
                "A empresa não existe mais para o mercado. Ação virou pó: R$ 1,00."
            )

        d["precos"].append(round(valor_final, 2))

# ─────────────────────────────────────────────────────────────────────────────
# 4. Sidebar — Seleção de perfil
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🔐 Controle de Acesso")
perfil = st.sidebar.selectbox(
    "Selecione quem está acessando:",
    ["📈 Telão (Bolsa)", *EMPRESAS, "👑 Painel Apresentador"],
)

# ═════════════════════════════════════════════════════════════════════════════
# TELÃO
# ═════════════════════════════════════════════════════════════════════════════
if perfil == "📈 Telão (Bolsa)":
    st.title("📊 BOLSA DE VALORES — HOME BROKER REAL TIME")
    st.subheader(f"Ano atual da simulação: {st.session_state.rodada_atual}")

    # Métricas no topo
    cols = st.columns(4)
    for i, (nome, d) in enumerate(st.session_state.dados_empresas.items()):
        delta = round(d["precos"][-1] - d["precos"][-2], 2) if len(d["precos"]) > 1 else 0
        cols[i].metric(nome, f"R$ {d['precos'][-1]:.2f}", delta=f"R$ {delta:+.2f}")

    st.markdown("---")

    # Gráfico comparativo sempre visível
    fig, ax = plt.subplots(figsize=(11, 5))
    rotulos_eixo = ["Início", "Ano 1", "Ano 2", "Ano 3", "Veredito"]
    cores = ["#1976D2", "#388E3C", "#F57C00", "#7B1FA2"]
    for i, (nome, d) in enumerate(st.session_state.dados_empresas.items()):
        x = rotulos_eixo[: len(d["precos"])]
        ax.plot(x, d["precos"], marker="o", linewidth=2.5, label=nome, color=cores[i])
        ax.text(len(d["precos"]) - 1, d["precos"][-1] + 1.5,
                f"R${d['precos'][-1]:.2f}", fontsize=9, color=cores[i], fontweight="bold")
    ax.set_ylabel("Preço da Ação (R$)")
    ax.set_ylim(-5, 130)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper left")
    st.pyplot(fig)

    # Veredito final
    if st.session_state.rodada_atual == 4:
        st.markdown("## 🏁 VEREDITO FINAL")
        for nome, d in st.session_state.dados_empresas.items():
            if "PRESA" in d["status"] or "FRAUDE" in d["status"]:
                st.error(f"**{nome}** — {d['status']} | R$ {d['precos'][-1]:.2f}")
            elif "EXCELÊNCIA" in d["status"]:
                st.success(f"**{nome}** — {d['status']} | R$ {d['precos'][-1]:.2f}")
            else:
                st.info(f"**{nome}** — {d['status']} | R$ {d['precos'][-1]:.2f}")

# ═════════════════════════════════════════════════════════════════════════════
# PAINEL DO APRESENTADOR
# ═════════════════════════════════════════════════════════════════════════════
elif perfil == "👑 Painel Apresentador":
    st.title("👑 PAINEL DE CONTROLE")
    st.subheader(f"Ano atual: {st.session_state.rodada_atual}")

    col1, col2 = st.columns(2)
    with col1:
        label_btn = {
            1: "🚀 Liberar Ano 2",
            2: "🚀 Liberar Ano 3",
            3: "⚖️ Disparar Auditoria (Ano 4)",
        }.get(st.session_state.rodada_atual, "✅ Simulação Encerrada")

        if st.session_state.rodada_atual <= 3:
            if st.button(label_btn):
                st.session_state.rodada_atual += 1
                if st.session_state.rodada_atual == 4:
                    aplicar_auditoria_final()
                st.rerun()
    with col2:
        if st.button("🔄 Reiniciar Jogo"):
            st.session_state.dados_empresas = {
                nome: {
                    "precos": [50.0],
                    "voto_r1": None, "voto_r2": None, "voto_r3": None,
                    "status": "Operando", "noticia_r4": "",
                }
                for nome in EMPRESAS
            }
            st.session_state.rodada_atual = 1
            st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Decisões Registradas")
    cols = st.columns(4)
    for i, (nome, d) in enumerate(st.session_state.dados_empresas.items()):
        with cols[i]:
            st.markdown(f"**{nome}**")
            st.write(f"Ano 1: `{d['voto_r1'] or '—'}`")
            st.write(f"Ano 2: `{d['voto_r2'] or '—'}`")
            st.write(f"Ano 3: `{d['voto_r3'] or '—'}`")
            st.write(f"Preços: {d['precos']}")

# ═════════════════════════════════════════════════════════════════════════════
# PORTAL DAS EMPRESAS
# ═════════════════════════════════════════════════════════════════════════════
else:
    empresa_atual = perfil
    d = st.session_state.dados_empresas[empresa_atual]
    rodada = st.session_state.rodada_atual

    st.title(f"🏢 {empresa_atual}")
    col1, col2 = st.columns(2)
    col1.metric("Preço Atual da Ação", f"R$ {d['precos'][-1]:.2f}")
    col2.metric("Rodada", f"Ano {rodada}")

    st.markdown("---")

    # ── Resumos de rodadas passadas ──────────────────────────────────────────
    if rodada > 1 and d["voto_r1"] is not None:
        with st.expander("📅 Ano 1 — Decisão registrada", expanded=False):
            st.info(f"**Decisão:** {LABELS[d['voto_r1']]}  \n**Preço após o ano:** R$ {d['precos'][1]:.2f}")

    if rodada > 2 and d["voto_r2"] is not None:
        with st.expander("📅 Ano 2 — Decisão registrada", expanded=False):
            st.info(f"**Decisão:** {LABELS[d['voto_r2']]}  \n**Preço após o ano:** R$ {d['precos'][2]:.2f}")

    if rodada > 3 and d["voto_r3"] is not None:
        with st.expander("📅 Ano 3 — Decisão registrada", expanded=False):
            st.info(f"**Decisão:** {LABELS[d['voto_r3']]}  \n**Preço após o ano:** R$ {d['precos'][3]:.2f}")

    # ── ANO 1 ────────────────────────────────────────────────────────────────
    if rodada == 1:
        st.markdown("## 📅 ANO 1 — Risco Sacado (*Confirming*)")
        st.warning(
            "**🏬 CENÁRIO:**  \n"
            "Sua rede varejista enfrenta forte aperto de liquidez. O CFO firmou contratos de "
            "**confirming (risco sacado)** com bancos: os fornecedores recebem antecipado pelo banco, "
            "e a empresa paga depois — com juros embutidos.  \n\n"
            "O board pressiona por resultados positivos. O saldo de risco sacado acumulado é de "
            "**R$ 1,2 bilhão**.  \n\n"
            "**Como classificar essa operação no balanço?**"
        )
        st.markdown("""
| Opção | Classificação | O que a diretoria faz |
|:---:|:---|:---|
| **A** | **Sem Gerenciamento** | Registrar corretamente como **dívida financeira** (Passivo Financeiro) + divulgar nas notas explicativas |
| **B** | **Gerenciamento Técnico (CPC)** | Registrar em **Fornecedores a Pagar** (Passivo Operacional) com nota explicativa discreta — interpretação técnica ambígua |
| **C** | **Gerenciamento Fraudulento** | **Omitir completamente** o risco sacado — não aparece nem no passivo, nem nas notas explicativas |
""")
        st.markdown("> 💡 *Opção A: ação cai 30% | Opção B: ação sobe 10% | Opção C: ação sobe 40% — mas é uma bomba-relógio.*")

        if d["voto_r1"] is None:
            escolha = st.radio("Decisão da diretoria:", ["A", "B", "C"],
                               format_func=lambda x: LABELS[x], key=f"r1_{empresa_atual}")
            if st.button("✅ Confirmar Decisão — Ano 1", key=f"btn_r1_{empresa_atual}"):
                d["voto_r1"] = escolha
                d["precos"].append(round(d["precos"][-1] * IMPACTOS[1][escolha], 2))
                st.rerun()
        else:
            st.success(f"✅ Decisão já registrada: **{LABELS[d['voto_r1']]}** | Preço: R$ {d['precos'][1]:.2f}")

    # ── ANO 2 ────────────────────────────────────────────────────────────────
    elif rodada == 2:
        st.markdown("## 📅 ANO 2 — Expansão e Geração de Caixa")
        st.warning(
            "**🏬 CENÁRIO:**  \n"
            "A empresa precisa mostrar crescimento para o mercado. O caixa está apertado após o ano anterior "
            "e o conselho exige resultados no balanço.  \n\n"
            "**Como a diretoria decide gerar (ou aparentar gerar) caixa e crescimento?**"
        )
        st.markdown("""
| Opção | Classificação | O que a diretoria faz |
|:---:|:---|:---|
| **A** | **Sem Gerenciamento** | **Vender ativos** operacionais para gerar caixa real — transparência total, mas encolhe a operação |
| **B** | **Gerenciamento Técnico (CPC)** | **Reconhecer receita de longo prazo antecipadamente** com base no CPC 47 (*revenue recognition*) — dentro da norma, mas agressivo |
| **C** | **Gerenciamento Fraudulento** | Criar **contratos de consultoria fantasma** para inflar o caixa e a receita sem operação real |
""")
        st.markdown("> 💡 *Opção A: ação cai 20% | Opção B: ação sobe 10% | Opção C: ação sobe 20% — mas registra mais uma fraude.*")

        if d["voto_r2"] is None:
            escolha = st.radio("Decisão da diretoria:", ["A", "B", "C"],
                               format_func=lambda x: LABELS[x], key=f"r2_{empresa_atual}")
            if st.button("✅ Confirmar Decisão — Ano 2", key=f"btn_r2_{empresa_atual}"):
                d["voto_r2"] = escolha
                d["precos"].append(round(d["precos"][-1] * IMPACTOS[2][escolha], 2))
                st.rerun()
        else:
            st.success(f"✅ Decisão já registrada: **{LABELS[d['voto_r2']]}** | Preço: R$ {d['precos'][2]:.2f}")

    # ── ANO 3 ────────────────────────────────────────────────────────────────
    elif rodada == 3:
        st.markdown("## 📅 ANO 3 — DRE sob Pressão e Gestão do Lucro")
        st.warning(
            "**🏬 CENÁRIO:**  \n"
            "O fechamento do exercício se aproxima. O resultado operacional está abaixo do guidance "
            "prometido ao mercado. Analistas e fundos de investimento monitoram de perto.  \n\n"
            "**Como a diretoria decide fechar o DRE deste ano?**"
        )
        st.markdown("""
| Opção | Classificação | O que a diretoria faz |
|:---:|:---|:---|
| **A** | **Sem Gerenciamento** | **Venda de ativos** para cobrir o prejuízo operacional — reconhece a realidade, mas descapitaliza a empresa |
| **B** | **Gerenciamento Técnico (CPC)** | **Capitalizar gastos de marketing** como ativo intangível (CPC 04) — dentro da norma, eleva lucro legalmente |
| **C** | **Gerenciamento Fraudulento** | **Reverter PDD sem base** técnica para inflar o lucro — manipulação das provisões para calote |
""")
        st.markdown("> 💡 *Opção A: ação cai 15% | Opção B: ação sobe 10% | Opção C: ação cai 20% — o mercado começa a desconfiar.*")

        if d["voto_r3"] is None:
            escolha = st.radio("Decisão da diretoria:", ["A", "B", "C"],
                               format_func=lambda x: LABELS[x], key=f"r3_{empresa_atual}")
            if st.button("✅ Confirmar Decisão — Ano 3", key=f"btn_r3_{empresa_atual}"):
                d["voto_r3"] = escolha
                d["precos"].append(round(d["precos"][-1] * IMPACTOS[3][escolha], 2))
                st.rerun()
        else:
            st.success(f"✅ Decisão já registrada: **{LABELS[d['voto_r3']]}** | Preço: R$ {d['precos'][3]:.2f}")

    # ── ANO 4 — VEREDITO + GRÁFICO ───────────────────────────────────────────
    elif rodada == 4:
        st.markdown("## ⚖️ ANO 4 — AUDITORIA DA CVM & VEREDITO FINAL")

        status = d.get("status", "")
        noticia = d.get("noticia_r4", "")

        if "PRESA" in status or "ESTRUTURAL" in status:
            st.error(f"**{status}**\n\n{noticia}")
        elif "INVESTIGAÇÃO" in status:
            st.warning(f"**{status}**\n\n{noticia}")
        elif "EXCELÊNCIA" in status:
            st.success(f"**{status}**\n\n{noticia}")
        else:
            st.info(f"**{status}**\n\n{noticia}")

        st.markdown("---")
        st.markdown("### 📊 Histórico Completo da Ação")

        rotulos = ["Início", "Ano 1", "Ano 2", "Ano 3", "Veredito"][: len(d["precos"])]
        fig2, ax2 = plt.subplots(figsize=(9, 4))
        cor = "#e63946" if ("PRESA" in status or "INVESTIGAÇÃO" in status) else "#2e7d32"
        ax2.plot(rotulos, d["precos"], marker="o", linewidth=3, color=cor)
        for i, (r, p) in enumerate(zip(rotulos, d["precos"])):
            ax2.annotate(f"R$ {p:.2f}", (i, p), textcoords="offset points",
                         xytext=(0, 10), ha="center", fontsize=10, fontweight="bold")
        ax2.set_ylabel("Preço da Ação (R$)")
        ax2.set_title(f"Evolução — {empresa_atual}", fontweight="bold")
        ax2.grid(True, linestyle="--", alpha=0.4)
        ax2.set_ylim(-5, max(d["precos"]) * 1.4 + 10)
        st.pyplot(fig2)

        st.markdown("### 📋 Caminho de Decisões")
        c1, c2, c3 = st.columns(3)
        c1.info(f"**Ano 1:** {LABELS.get(d['voto_r1'], '—')}")
        c2.info(f"**Ano 2:** {LABELS.get(d['voto_r2'], '—')}")
        c3.info(f"**Ano 3:** {LABELS.get(d['voto_r3'], '—')}")

        qtd_c = [d["voto_r1"], d["voto_r2"], d["voto_r3"]].count('C')
        if qtd_c == 0:
            st.success(f"✅ Nenhuma fraude registrada. Preço final calculado pelos multiplicadores.")
        elif qtd_c == 1:
            st.warning(f"⚠️ 1 decisão fraudulenta → Valor colapsa para R$ 10,00.")
        else:
            st.error(f"🚔 {qtd_c} decisões fraudulentas → Valor colapsa para R$ 1,00.")
