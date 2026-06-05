import streamlit as st
import matplotlib.pyplot as plt

# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuração da Página (Mobile Friendly)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Simulador de Varejo - Governança", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Estado Compartilhado Globalmente (Banco de Dados em Memória)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def obter_banco_dados_global():
    return {
        "dados_empresas": {
            nome: {
                "precos": [50.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None,
                "status": "Operando", "noticia_r4": "",
            }
            for nome in ["Empresa Alfa", "Empresa Beta", "Empresa Gama", "Empresa Sigma"]
        },
        "rodada_atual": 1
    }

db_global = obter_banco_dados_global()

# ─────────────────────────────────────────────────────────────────────────────
# 3. Mapeamentos e Constantes
# ─────────────────────────────────────────────────────────────────────────────
EMPRESAS = ["Empresa Alfa", "Empresa Beta", "Empresa Gama", "Empresa Sigma"]

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
# 4. Funções de Lógica do Jogo
# ─────────────────────────────────────────────────────────────────────────────
def todos_votaram_na_rodada(rodada):
    if rodada > 3:
        return False
    campo_voto = f"voto_r{rodada}"
    for nome, d in db_global["dados_empresas"].items():
        if d[campo_voto] is None:
            return False
    return True

def aplicar_auditoria_final():
    for nome, d in db_global["dados_empresas"].items():
        if len(d["precos"]) >= 5:
            continue
            
        v1, v2, v3 = d["voto_r1"], d["voto_r2"], d["voto_r3"]
        if None in (v1, v2, v3):
            continue

        qtd_c = [v1, v2, v3].count('C')

        if qtd_c == 0:
            valor_final = d["precos"][-1]
            if f"{v1}{v2}{v3}" == "BBB":
                d["status"] = "🏆 EXCELÊNCIA TÉCNICA E ÉTICA"
                d["noticia_r4"] = "🏆 **Gestão exemplar!** Crescimento sustentável e transparente com normas CPC."
            elif f"{v1}{v2}{v3}" == "AAA":
                d["status"] = "📉 HONESTA, MAS SEM CRESCIMENTO"
                d["noticia_r4"] = "📉 **Empresa honesta, porém estagnada.** Postura ultraconservadora afastou investidores."
            else:
                d["status"] = "⚖️ ESTABILIDADE COM RESSALVAS"
                d["noticia_r4"] = "⚖️ **Governança preservada.** A empresa manteve conduta ética com ressalvas."

        elif qtd_c == 1:
            valor_final = 10.00
            d["status"] = "🚨 INVESTIGAÇÃO EM CURSO"
            d["noticia_r4"] = "🚨 **O mercado descobriu a fraude pontual.** Investigação em curso pelo MP e CFC."

        else:
            valor_final = 1.00
            d["status"] = "🚔 FRAUDE ESTRUTURAL: GESTÃO PRESA"
            d["noticia_r4"] = "🚔 **O esquema foi desmantelado.** CEO e CFO foram presos por organização criminosa."

        d["precos"].append(round(valor_final, 2))

# ─────────────────────────────────────────────────────────────────────────────
# 5. Roteamento de Perfis por URL
# ─────────────────────────────────────────────────────────────────────────────
url_id = st.query_params.get("id", "").lower()

if url_id == "mestre123":
    perfil = "👑 Painel Apresentador"
elif url_id == "alfa":
    perfil = "Empresa Alfa"
elif url_id == "beta":
    perfil = "Empresa Beta"
elif url_id == "gama":
    perfil = "Empresa Gama"
elif url_id == "sigma":
    perfil = "Empresa Sigma"
else:
    perfil = "📈 Telão (Bolsa)"

# Remove sidebar para os alunos (melhor layout no celular)
if perfil in EMPRESAS:
    st.empty()
else:
    st.sidebar.title("🔐 Administração")
    st.sidebar.write(f"Modo: **{perfil}**")

# ═════════════════════════════════════════════════════════════════════════════
# 1. PORTAL DOS ALUNOS (CELULAR)
# ═════════════════════════════════════════════════════════════════════════════
if perfil in EMPRESAS:
    empresa_atual = perfil
    d = db_global["dados_empresas"][empresa_atual]
    rodada = db_global["rodada_atual"]

    # Cabeçalho limpo para celular
    st.markdown(f"## 🏢 {empresa_atual}")
    st.markdown(f"**Ano Atual do Mercado:** {rodada} | **Ação:** R$ {d['precos'][-1]:.2f}")
    st.markdown("---")

    # Verifica se a empresa já votou nesta rodada
    voto_ja_realizado = d[f"voto_r{rodada}"] is not None if rodada <= 3 else False

    if rodada <= 3:
        if not voto_ja_realizado:
            st.markdown(f"### 📋 Escolha sua estratégia para o **Ano {rodada}**:")
            
            # Textos resumidos para caber bem no celular
            if rodada == 1:
                st.info("**CENÁRIO RISCO SACADO:** Como classificar a operação de R$ 1,2B com juros de fornecedores?")
            elif rodada == 2:
                st.info("**CENÁRIO EXPANSÃO:** Como a diretoria vai gerar ou aparentar crescimento de caixa?")
            elif rodada == 3:
                st.info("**CENÁRIO DRE SOB PRESSÃO:** Resultado operacional abaixo da meta. Como fechar o ano?")

            escolha = st.radio("Selecione uma opção:", ["A", "B", "C"],
                               format_func=lambda x: LABELS[x], key=f"voto_{empresa_atual}_{rodada}")
            
            if st.button("🗳️ Enviar Voto Oficial", key=f"btn_{empresa_atual}_{rodada}", use_container_width=True):
                d[f"voto_r{rodada}"] = escolha
                d["precos"].append(round(d["precos"][-1] * IMPACTOS[rodada][escolha], 2))
                st.rerun()
        else:
            # Se já votou, exibe tela de espera
            st.success(f"✅ Voto registrado: **Opção {d[f'voto_r{rodada}']}**")
            st.write("Aguardando as demais empresas votarem...")

            # Condição crucial: Só mostra o botão se TODOS responderem a rodada
            if todos_votaram_na_rodada(rodada):
                st.markdown("---")
                st.balloons()
                st.markdown("### 🚀 Próxima Etapa Liberada!")
                if st.button("Avançar para Próxima Rodada ➡️", use_container_width=True):
                    # O primeiro aluno que clicar vira a rodada global
                    if db_global["rodada_atual"] == rodada:
                        db_global["rodada_atual"] += 1
                        if db_global["rodada_atual"] == 4:
                            aplicar_auditoria_final()
                    st.rerun()
            else:
                # Mostra o status de quem falta votar de forma resumida
                fata_votar = [n for n, dados in db_global["dados_empresas"].items() if dados[f"voto_r{rodada}"] is None]
                st.warning(f"⏳ Aguardando respostas de: {', '.join(fata_votar)}")

    elif rodada == 4:
        st.markdown("### ⚖️ FIM DE JOGO: Veredito da Auditoria")
        status = d.get("status", "")
        noticia = d.get("noticia_r4", "")
        
        if "PRESA" in status:
            st.error(f"**{status}**\n\n{noticia}\n\n**Valor Final:** R$ {d['precos'][-1]:.2f}")
        elif "EXCELÊNCIA" in status:
            st.success(f"**{status}**\n\n{noticia}\n\n**Valor Final:** R$ {d['precos'][-1]:.2f}")
        else:
            st.info(f"**{status}**\n\n{noticia}\n\n**Valor Final:** R$ {d['precos'][-1]:.2f}")

# ═════════════════════════════════════════════════════════════════════════════
# 2. PAINEL DO APRESENTADOR (SUA TELA DE GESTÃO)
# ═════════════════════════════════════════════════════════════════════════════
elif perfil == "👑 Painel Apresentador":
    st.title("👑 PAINEL DE CONTROLE INTEGRADO (MASTER)")
    st.subheader(f"Ano atual da simulação: {db_global['rodada_atual']}")

    if st.button("🚨 LIMPAR BANCO E REINICIAR DINÂMICA"):
        db_global["dados_empresas"] = {
            nome: {
                "precos": [50.0],
                "voto_r1": None, "voto_r2": None, "voto_r3": None,
                "status": "Operando", "noticia_r4": "",
            }
            for nome in EMPRESAS
        }
        db_global["rodada_atual"] = 1
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Status e Votos em Tempo Real")
    
    # Exibe as 4 empresas em colunas integradas para você ver quem já respondeu
    cols = st.columns(4)
    for i, (nome, d) in enumerate(db_global["dados_empresas"].items()):
        with cols[i]:
            st.markdown(f"#### {nome}")
            st.metric("Preço Atual", f"R$ {d['precos'][-1]:.2f}")
            st.write(f"Ano 1: **{d['voto_r1'] or '⏳ Aguardando...'}**")
            st.write(f"Ano 2: **{d['voto_r2'] or '⏳ Aguardando...'}**")
            st.write(f"Ano 3: **{d['voto_r3'] or '⏳ Aguardando...'}**")

# ═════════════════════════════════════════════════════════════════════════════
# 3. TELÃO (PROJETOR PRINCIPAL)
# ═════════════════════════════════════════════════════════════════════════════
else:
    st.title("📊 BOLSA DE VALORES — HOME BROKER REAL TIME")
    st.subheader(f"Ano atual da simulação: {db_global['rodada_atual']}")
    st.button("🔄 Atualizar Cotações")

    cols = st.columns(4)
    for i, (nome, d) in enumerate(db_global["dados_empresas"].items()):
        delta = round(d["precos"][-1] - d["precos"][-2], 2) if len(d["precos"]) > 1 else 0
        cols[i].metric(nome, f"R$ {d['precos'][-1]:.2f}", delta=f"R$ {delta:+.2f}")

    st.markdown("---")

    fig, ax = plt.subplots(figsize=(11, 4))
    rotulos_eixo = ["Início", "Ano 1", "Ano 2", "Ano 3", "Veredito"]
    cores = ["#1976D2", "#388E3C", "#F57C00", "#7B1FA2"]
    for i, (nome, d) in enumerate(db_global["dados_empresas"].items()):
        x = rotulos_eixo[: len(d["precos"])]
        ax.plot(x, d["precos"], marker="o", linewidth=2.5, label=nome, color=cores[i])
        ax.text(len(d["precos"]) - 1, d["precos"][-1] + 1.5,
                f"R${d['precos'][-1]:.2f}", fontsize=9, color=cores[i], fontweight="bold")
    ax.set_ylabel("Preço da Ação (R$)")
    ax.set_ylim(-5, 130)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="upper left")
    st.pyplot(fig)

    if db_global["rodada_atual"] == 4:
        st.markdown("## 🏁 VEREDITO FINAL")
        for nome, d in db_global["dados_empresas"].items():
            st.info(f"**{nome}** — {d['status']} | R$ {d['precos'][-1]:.2f}")
📱 Como fica a experiência deles no celular agora:
Eles acessam pelo link individual (ex: /?id=alfa).

Aparece o texto explicativo da rodada e os botões grandes de A, B ou C.

Assim que clicam em "Enviar Voto", a tela bloqueia e aparece: "✅ Voto registrado. Aguardando as demais empresas..." seguido de um aviso mostrando quem ainda falta votar (ex: "⏳ Aguardando respostas de: Empresa Gama, Empresa Sigma").

A Mágica: No momento exato em que a última empresa clicar em enviar voto, a tela de todo mundo atualiza instantaneamente, solta balões virtuais (st.balloons()) e mostra o botão grande: "Avançar para Próxima Rodada ➡️".

👑 Como fica para você (Painel Integrado):
Você só precisa ficar com a aba /?id=mestre123 aberta no seu notebook. Conforme os grupos clicam no celular deles, você vê as letrinhas A, B ou C aparecendo na sua tabela em tempo real, permitindo monitorar perfeitamente a dinâmica sem precisar sair do lugar!
                
