elif perfil in EMPRESA_MAP:
    estado = carregar_estado()
    nome_interno = EMPRESA_MAP[perfil]

    # ── AUTENTICAÇÃO DA EMPRESA ──────────────────────────────────────────────
    chave_auth = f"auth_{nome_interno}"
    sessoes_ativas = estado.get("sessoes_ativas", [])

    if not st.session_state.get(chave_auth, False):

        # Verifica se já está ocupada por outro PC
        if nome_interno in sessoes_ativas:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#b71c1c,#c62828);border-radius:16px;
                        padding:48px 32px;margin:24px 0;text-align:center;color:#fff;
                        box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-size:72px;margin-bottom:16px;">🔒</div>
                <div style="font-size:24px;font-weight:900;margin-bottom:12px;">ESTAÇÃO OCUPADA</div>
                <div style="font-size:15px;opacity:0.85;">
                    A bancada <b>{perfil}</b> já está sendo acessada em outro dispositivo.<br>
                    Apenas um acesso simultâneo é permitido por empresa.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.stop()

        # Tela de login
        st.title("🔒 Acesso Restrito")
        st.markdown(f"### Estação de Trabalho: {perfil}")
        st.markdown("Identifique-se para acessar sua bancada corporativa.")

        SENHAS_EMPRESAS = {
            "Empresa Alfa": "ALFA10",
            "Empresa Beta": "BETA20",
            "Empresa Gama": "GAMA30",
        }

        senha_input = st.text_input("Senha da empresa:", type="password", key=f"senha_{nome_interno}")

        if st.button("Entrar", use_container_width=True, type="primary"):
            if senha_input == SENHAS_EMPRESAS.get(nome_interno, ""):
                st.session_state[chave_auth] = True
                st.session_state["empresa_origem"] = perfil
                # Registra sessão ativa no estado compartilhado
                if nome_interno not in sessoes_ativas:
                    sessoes_ativas.append(nome_interno)
                    estado["sessoes_ativas"] = sessoes_ativas
                    salvar_estado(estado)
                st.rerun()
            else:
                st.error("❌ Senha incorreta.")
        st.stop()

    # ── TELA DA EMPRESA (autenticada) ────────────────────────────────────────
    d = estado["dados_empresas"][nome_interno]
    rodada = estado.get("rodada_atual", 1)

    st.session_state["empresa_origem"] = perfil
    st.markdown(f"## 🏢 Estação de Trabalho: {perfil}")

    _origem = perfil
    nav1, nav2, nav3, _ = st.columns([1, 1, 1, 3])
    with nav1:
        if st.button("📋 Rodada", use_container_width=True, type="primary"):
            st.session_state["pagina_atual"] = _origem
            st.rerun()
    with nav2:
        if st.button("📈 Telão", use_container_width=True):
            st.session_state["pagina_atual"] = "📈 Telão (Bolsa)"
            st.rerun()
    with nav3:
        if st.button("📰 Mídia", use_container_width=True):
            st.session_state["pagina_atual"] = "📰 Mídia (Notícias)"
            st.rerun()

    # Timer
    chave_timer = f"timer_inicio_r{rodada}" if rodada <= 3 else None
    ts_inicio = estado.get(chave_timer) if chave_timer else None

    if ts_inicio and rodada <= 3:
        restante_i = max(0, int(10 * 60 - (time.time() - ts_inicio)))
        minutos = restante_i // 60
        segundos = restante_i % 60

        if restante_i >= 7 * 60:
            cor_timer, bg_timer, emoji_timer = "#2e7d32", "#e8f5e9", "🟢"
        elif restante_i >= 3 * 60:
            cor_timer, bg_timer, emoji_timer = "#f57f17", "#fff8e1", "🟡"
        else:
            cor_timer, bg_timer, emoji_timer = "#c62828", "#ffebee", "🔴"

        st.markdown(
            f"<div style='background:{bg_timer};border:1px solid {cor_timer};border-radius:8px;"
            f"padding:8px 14px;color:{cor_timer};font-weight:bold;font-size:16px;display:inline-block;'>"
            f"{emoji_timer} Tempo restante — Rodada {rodada}: {minutos:02d}:{segundos:02d}</div>",
            unsafe_allow_html=True
        )

    # ── RODADAS 1-3 ──────────────────────────────────────────────────────────
    if rodada <= 3:
        if not ts_inicio:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1a237e,#283593);border-radius:16px;
                        padding:48px 32px;margin:24px 0;text-align:center;color:#fff;
                        box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-size:72px;margin-bottom:16px;">🔒</div>
                <div style="font-size:24px;font-weight:900;margin-bottom:12px;">AGUARDANDO INÍCIO</div>
                <div style="font-size:15px;opacity:0.85;">O Gerenciador ainda não iniciou esta rodada.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if rodada == 1:
                st.markdown(narrativa_rodada_1())
            elif rodada == 2:
                st.markdown(narrativa_rodada_2(-16_500_000_000.0, -300_000_000.0))
            elif rodada == 3:
                st.markdown(narrativa_rodada_3())

            voto_atual = d.get(f"voto_r{rodada}")
            if voto_atual is None:
                escolha = st.radio(
                    "Selecione o tratamento contábil:",
                    ["A", "B", "C"],
                    format_func=lambda x: get_labels(rodada)[x]
                )
                if st.button("✅ Homologar Resolução", use_container_width=True):
                    d[f"voto_r{rodada}"] = escolha
                    d[f"tempo_voto_r{rodada}"] = time.time()
                    salvar_estado(estado)
                    st.rerun()
            else:
                st.success(f"📌 Estratégia Adotada — Opção {voto_atual}")

                apurado = estado.get(f"apurado_r{rodada}", False)
                if apurado:
                    exibir_dre({f"r{r}": d.get(f"voto_r{r}") for r in range(1, rodada + 1)}, rodada, mostrar_score=False)
                    bonus_vel = d.get(f"bonus_velocidade_r{rodada}")
                    if bonus_vel == "primeiro":
                        st.info("📈 O mercado aprecia agilidade. Por ser a primeira bancada a responder: **+R$ 0,10 por ação.**")
                    elif bonus_vel == "ultimo":
                        st.warning("⏳ Tempo é dinheiro... Vocês foram a última bancada a se posicionar. **-R$ 0,10 por ação.**")
                    elif bonus_vel == "meio":
                        st.info("⏱️ Posicionamento no tempo médio. Sem bônus ou penalidade de velocidade.")

                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32);border-radius:12px;
                                padding:20px 24px;margin:16px 0;text-align:center;color:#fff;">
                        <div style="font-size:32px;margin-bottom:8px;">📰</div>
                        <div style="font-size:18px;font-weight:bold;">Resultados apurados!</div>
                        <div style="font-size:14px;margin-top:6px;opacity:0.9;">Acesse a aba <b>Mídia</b> para ver a cobertura completa da rodada.</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background:linear-gradient(135deg,#e65100,#bf360c);border-radius:12px;
                                padding:24px;margin:16px 0;text-align:center;color:#fff;">
                        <div style="font-size:48px;margin-bottom:10px;">⏳</div>
                        <div style="font-size:20px;font-weight:bold;">Aguardando apuração...</div>
                        <div style="font-size:14px;margin-top:8px;opacity:0.9;">Sua decisão foi registrada. Aguarde o Gerenciador apurar os resultados.</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── RODADA 4 ──────────────────────────────────────────────────────────────
    else:
        apuracao_feita = estado.get("apuracao_r4_feita", False)

        if not apuracao_feita:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#1a237e,#283593);border-radius:16px;padding:48px 32px;margin:24px 0;text-align:center;color:#fff;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-size:72px;margin-bottom:16px;animation:spin 2s linear infinite;">⏳</div>
                <div style="font-size:28px;font-weight:900;letter-spacing:1px;margin-bottom:12px;">AUDITORIA EM ANDAMENTO</div>
                <div style="font-size:16px;opacity:0.85;">A CVM está analisando os demonstrativos financeiros dos últimos três exercícios.</div>
                <div style="font-size:14px;margin-top:16px;opacity:0.7;">Aguarde o resultado...</div>
            </div>
            <style>
            @keyframes spin { 0%{transform:rotate(0deg)} 50%{transform:rotate(15deg)} 100%{transform:rotate(0deg)} }
            </style>
            """, unsafe_allow_html=True)

        else:
            r1 = d.get("voto_r1")
            r2 = d.get("voto_r2")
            r3 = d.get("voto_r3")
            qtd_c = [r1, r2, r3].count("C")
            qtd_b = [r1, r2, r3].count("B")

            if qtd_c == 3:
                icone_res, cor_res = "⛓️", "#b71c1c"
                titulo_res = "OPERAÇÃO EXCEL CRIATIVO — PRISÃO DOS EXECUTIVOS! O Direito de Permanecer Calado é uma garantia fundamental que eles vão usar."
                texto_res  = "A CVM e a Polícia Federal deflagraram operação contra sua empresa. CEO e CFO presos preventivamente 🔗."
            elif qtd_c == 2:
                icone_res, cor_res = "💰🚫", "#c62828"
                titulo_res = "JUSTIÇA BLOQUEIA BENS DOS EXECUTIVOS!"
                texto_res  = "A Justiça determinou o bloqueio cautelar dos bens dos executivos. CEO, CFO e Diretor de RI foram substituídos. Os conselheiros estão 'profundamente surpresos'."
            elif qtd_c == 1 and qtd_b >= 1:
                icone_res, cor_res = "💸", "#e65100"
                titulo_res = "CEO E CFO VIRAM EX-FUNCIONÁRIOS!"
                texto_res  = "A CVM identificou fraude combinada com accruals. CEO e CFO foram demitidos 🚪. O LinkedIn deles foi atualizado em tempo recorde."
            elif qtd_c == 1:
                icone_res, cor_res = "🥲", "#f57f17"
                titulo_res = "FRAUDE/ ERRO PONTUAL — CEO DEMITIDO!"
                texto_res  = "Mesmo considerada pontual, a irregularidade destruiu a confiança dos investidores. CEO foi convidado a 'buscar novos desafios profissionais' 💼."
            elif qtd_b >= 2:
                icone_res, cor_res = "📉", "#1565c0"
                titulo_res = "MESTRE DO PÔQUER CONTÁBIL! e VIGILÂNCIA REDOBRADA"
                texto_res  = "Sem fraude identificada, mas o abuso de accruals discricionário colocou o CFO sob monitoramento permanente de três auditores independentes ♠️ e do estagiário de compliance 👀."
            elif qtd_b == 1:
                icone_res, cor_res = "ℹ️", "#2e7d32"
                titulo_res = "🦸‍♂️ CFO vira HERÓI/ HEROÍNA DO MERCADO!"
                texto_res  = "Com apenas um ajuste contábil estratégico, salvou a operação sem cruzar a linha vermelha da CVM. Alguns heróis usam capa!!! A empresa está salva e a gestão foi aplaudida!"
            else:
                icone_res, cor_res = "☠️", "#4a148c"
                titulo_res = "ÉTICA PRESERVADA — AÇÕES AFUNDARAM"
                texto_res  = "Transparência total. Governança check ✅. Orgulho da professora ❤️! Os auditores aplaudiram 👏. Os investidores venderam 📉. Os bônus desapareceram 💸. A reputação sobreviveu. O preço da ação, não."

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,{cor_res}dd,{cor_res}88);border:2px solid {cor_res};border-radius:16px;padding:32px;margin:24px 0;text-align:center;color:#fff;box-shadow:0 8px 32px rgba(0,0,0,0.4);">
                <div style="font-size:56px;margin-bottom:12px;">{icone_res}</div>
                <div style="font-size:22px;font-weight:900;letter-spacing:1px;margin-bottom:16px;text-transform:uppercase;">{titulo_res}</div>
                <div style="background:rgba(255,255,255,0.12);border-radius:10px;padding:16px 20px;font-size:14px;line-height:1.7;text-align:left;">
                    {texto_res}
                </div>
            </div>
            """, unsafe_allow_html=True)

            carta_html = gerar_carta_destino(nome_interno, r1, r2, r3)
            st.markdown(carta_html, unsafe_allow_html=True)

            st.markdown("""
            <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32);border-radius:12px;padding:16px 24px;margin:12px 0;text-align:center;color:#fff;">
                <div style="font-size:14px;">Acesse a aba <b>Mídia</b> para ver o veredicto completo de todas as empresas.</div>
            </div>
            """, unsafe_allow_html=True)

    # Auto-refresh
    time.sleep(6)
    st.rerun()
