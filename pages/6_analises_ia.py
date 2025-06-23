import streamlit as st
from database import (
    listar_curriculos_por_usuario,
    atualizar_opiniao_curriculo,
    atualizar_score_curriculo,
    atualizar_tempo_execucao_opiniao,
    atualizar_tempo_execucao_score,
    atualizar_tokens_opiniao,
    atualizar_tokens_score,
    atualizar_llm_model,
    atualizar_custo_opiniao,
    atualizar_custo_score
)
import sys
import os
import analises_llm
import altair as alt
import pandas as pd

# Configura caminhos para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Análises com IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    .small-font { font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

# Menu Lateral
with st.sidebar:
    st.title("📋 Menu")
    st.markdown("---")
    st.page_link("pages/1_home.py", label="🏠 Página Inicial", use_container_width=True)
    st.page_link("pages/2_cadastrar_vaga.py", label="➕ Cadastrar Vaga", use_container_width=True)
    st.page_link("pages/3_gerenciar_vagas.py", label="✂️ Gerenciar Vagas", use_container_width=True)
    st.page_link("pages/4_enviar_curriculos.py", label="📤 Enviar Currículo", use_container_width=True)
    st.page_link("pages/5_gerenciar_curriculos.py", label="✂️ Gerenciar Currículos", use_container_width=True)
    st.page_link("pages/6_analises_ia.py", label="🧠 Análises com IA", use_container_width=True)
    st.markdown("---")
    if st.session_state.get('authentication_status'):
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.switch_page("0_login.py")
    st.caption("Versão 1.0 | © 2025")

st.logo(image = "imagens/BeAI.svg", icon_image = "imagens/captal_lambda_branco.png")

##########################################################

# Verifica se o usuário está logado
if not st.session_state.get('authentication_status'):
    st.warning("Você precisa estar logado para ver as análises!")
    st.switch_page("0_login.py")

col1, col2, col3 = st.columns([60, 20, 20], vertical_alignment="center")

with col1:
    st.title("🧠 Análises com IA de Currículos")

with col2:
    score_de_corte = st.number_input(
        "Score de corte para análise crítica",
        min_value=0.0,
        max_value=10.0,
        value=5.0,
        step=0.1,
        format="%.1f"
    )

with col3:
    st.write("")
    st.write("")
    botao_processar = st.button("🔄 Atualizar Processamento com IA", type="secondary", use_container_width=True)


# Processamento principal
if botao_processar:
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Lista apenas os currículos do usuário logado
        curriculos = listar_curriculos_por_usuario(st.session_state.get('user_id'))

        ids_ultimos = st.session_state.get('ultimos_curriculos_upados')
        if ids_ultimos:
            curriculos = [c for c in curriculos if c['id_curriculo'] in ids_ultimos]

        total = len(curriculos)

        if not curriculos:
            st.info("ℹ️ Nenhum currículo encontrado para processamento")
        else:
            # 1. Score com LLM
            for i, curriculo in enumerate(curriculos):
                nome_candidato = curriculo.get('nome_candidato', f'Currículo {curriculo["id_curriculo"]}')
                status_text.text(f"Gerando score do candidato {i+1}/{total}: {nome_candidato}")
                progress_bar.progress((i + 1) / total)
                try:
                    if curriculo['status_score_llm'] == False and curriculo['resumo_llm']:
                        desc_vaga = f'''
                            Atividades: {curriculo['atividades']}\n
                            Requisitos: {curriculo['requisitos']}\n
                            Diferenciais: {curriculo['diferenciais']}\n
                            '''
                        score, tempo_score, input_tokens, output_tokens, model_name, custo_chamada = analises_llm.gerar_score_curriculo(curriculo['resumo_llm'], desc_vaga)
                        if score is not None:
                            atualizar_score_curriculo(curriculo['id_curriculo'], score)
                            atualizar_tempo_execucao_score(curriculo['id_curriculo'], tempo_score)
                            atualizar_tokens_score(curriculo['id_curriculo'], input_tokens, output_tokens)
                            atualizar_llm_model(curriculo['id_curriculo'], model_name)
                            atualizar_custo_score(curriculo['id_curriculo'], custo_chamada)
                except Exception as e:
                    st.error(f"Erro no currículo {curriculo['id_curriculo']}: {str(e)}")
                    continue

            # Atualiza curriculos após score
            curriculos = listar_curriculos_por_usuario(st.session_state.get('user_id'))

            curriculos = pd.DataFrame(curriculos)
            curriculos = curriculos.loc[
                    (curriculos['status_md'] == True) &
                    (curriculos['status_resumo_llm'] == True)
                ]

            ids_ultimos = st.session_state.get('ultimos_curriculos_upados')
            if ids_ultimos:
                curriculos = curriculos[curriculos['id_curriculo'].isin(ids_ultimos)]
            total = len(curriculos)

            # 2. Opinião com LLM (apenas para quem atingiu score de corte)
            for i, curriculo in enumerate(curriculos):
                nome_candidato = curriculo['nome_candidato']
                status_text.text(f"Gerando análise crítica {i+1}/{total}: {nome_candidato}")
                progress_bar.progress((i + 1) / total)
                try:
                    score = curriculo['score_llm']
                    if score is not None and float(score) > float(score_de_corte):
                        if curriculo['status_opiniao_llm'] == False and curriculo['resumo_llm']:
                            desc_vaga = f'''
                            Atividades: {curriculo['atividades']}\n
                            Requisitos: {curriculo['requisitos']}\n
                            Diferenciais: {curriculo['diferenciais']}\n
                            '''
                            opiniao, tempo_opiniao, input_tokens, output_tokens, model_name, custo_chamada = analises_llm.gerar_opiniao_curriculo(curriculo['resumo_llm'], desc_vaga)
                            if opiniao:
                                atualizar_opiniao_curriculo(curriculo['id_curriculo'], opiniao)
                                atualizar_tempo_execucao_opiniao(curriculo['id_curriculo'], tempo_opiniao)
                                atualizar_tokens_opiniao(curriculo['id_curriculo'], input_tokens, output_tokens)
                                atualizar_llm_model(curriculo['id_curriculo'], model_name)
                                atualizar_custo_opiniao(curriculo['id_curriculo'], custo_chamada)
                    else:
                        # Salva frase padrão para quem não atingiu a nota de corte
                        atualizar_opiniao_curriculo(curriculo['id_curriculo'], f"Candidato não atingiu a nota de corte ({score_de_corte}) para análise crítica.")
                        atualizar_tempo_execucao_opiniao(curriculo['id_curriculo'], 0)
                        atualizar_tokens_opiniao(curriculo['id_curriculo'], 0, 0)
                        atualizar_custo_opiniao(curriculo['id_curriculo'], 0)
                except Exception as e:
                    st.error(f"Erro no currículo {curriculo['id_curriculo']}: {str(e)}")
                    continue

            st.toast("Processamento concluído com sucesso!", icon="✅")

    except Exception as e:
        st.error(f"❌ Erro geral no processamento: {str(e)}")
    finally:
        progress_bar.empty()
        status_text.empty()

# Seção para visualização de resultados
st.markdown("---")
st.subheader("📊 Score dos Candidatos")

# Lista apenas os currículos do usuário logado
curriculos = listar_curriculos_por_usuario(st.session_state.get('user_id'))

if curriculos:
    df_curriculos = pd.DataFrame(curriculos)
    # Mantém apenas a linha com maior score_llm para cada nome_candidato
    df_curriculos = df_curriculos.sort_values('score_llm', ascending=False).drop_duplicates(subset=['nome_candidato', 'id_vaga'], keep='first')

    if len(df_curriculos) == 0:
        st.info("ℹ️ Nenhum currículo encontrado para análise")
    else:
        # Obtenção da lista de vagas únicas do usuário logado, removendo valores nulos
        vagas_disponiveis = df_curriculos['nome_vaga'].dropna().unique()

        cols = st.columns(3)
        with cols[0]:
            # Filtro de vaga com opção neutra
            opcoes_vagas = ["Selecione uma vaga"] + list(vagas_disponiveis)
            vaga_selecionada = st.selectbox(
                "Selecione uma vaga:",
                options=opcoes_vagas
            )

        # Só mostra o conteúdo se uma vaga válida for selecionada
        if vaga_selecionada and vaga_selecionada != "Selecione uma vaga":
            # Filtragem do DataFrame com base na vaga selecionada
            df_filtrado = df_curriculos[df_curriculos['nome_vaga'] == vaga_selecionada]

            # Criação do gráfico com Altair
            grafico = alt.Chart(df_filtrado).mark_bar(
                cornerRadius=5,
                color='#3e82af'  # Cor verde neon que combina com o tema
            ).encode(
                x=alt.X('score_llm:Q', title='Score', axis=alt.Axis(titleFontSize=18, labelFontSize=12), scale=alt.Scale(domain=[0, 10])),
                y=alt.Y('nome_candidato:N', sort='-x', title='', axis=alt.Axis(labelFontSize=17)),
                tooltip=['nome_candidato', 'score_llm']
            ).properties(
                width=700,
                height= 100 + 40 * len(df_filtrado)
            ).configure_axis(
                labelFontSize=18,
                titleFontSize=18,
                domainColor='#CFCFCF',  # Cor das linhas do eixo
                labelColor='#CFCFCF'    # Cor dos labels
            ).configure_view(
                strokeWidth=0
            ).configure_axisY(
                labelPadding=10,
                labelLimit=0
            )

            st.altair_chart(grafico, use_container_width=True)

            st.markdown("---")
            st.subheader("💭 Análise Crítica")

            cols = st.columns(3)
            with cols[0]:
                # Filtro de candidato
                filtro_candidato = st.selectbox(
                    "Selecione um candidato:",
                    options=df_filtrado['nome_candidato'],
                )

            if filtro_candidato:
                opiniao_candidato = df_filtrado.loc[df_filtrado['nome_candidato'] == filtro_candidato, 'opiniao_llm'].iloc[0]
                st.write(opiniao_candidato)
else:
    st.warning("ℹ️ Nenhum currículo encontrado para análise")