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

import psutil
# import os

# Configura caminhos para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="Análises com IA",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_memory_usage():
    """Retorna o uso atual de memória RAM do processo do app em MB"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_usage_mb = mem_info.rss / (1024 ** 2)  # RSS: memória residente
    return mem_usage_mb

# Mostra o uso de RAM na tela
ram = get_memory_usage()
st.write(f"**Uso atual de RAM:** `{ram:.2f} MB`")


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
        value=7.0,
        step=0.1,
        format="%.1f"
    )

with col3:
    st.write("")
    st.write("")
    botao_processar = st.button("🔄 Atualizar Processamento com IA", type="secondary", use_container_width=True)


# Processamento principal
if botao_processar:
    st.warning("⚠️ Não saia desta página enquanto o processamento estiver em andamento!")
    progress_bar = st.progress(0)
    status_text = st.empty()
    # Define as etapas do processo e seus pesos
    etapas = {
        'score': 0.5,    # 50% do processo
        'opiniao': 0.5   # 50% do processo
    }
    progresso_atual = 0
    status_text.text("⚙️ Iniciando atualização...")
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
            # 1. Score com LLM (em batch)
            curriculos_score = [c for c in curriculos if c['status_score_llm'] == False and c['resumo_llm']]
            total_score = len(curriculos_score)
            processed_score = 0
            if curriculos_score:
                BATCH_SIZE = 40
                for i in range(0, len(curriculos_score), BATCH_SIZE):
                    batch = curriculos_score[i:i+BATCH_SIZE]
                    batch_ids = [c['id_curriculo'] for c in batch]
                    batch_resumos = [c['resumo_llm'] for c in batch]
                    batch_descs = [f"""
                        Atividades: {c['atividades']}\n
                        Requisitos: {c['requisitos']}\n
                        Diferenciais: {c['diferenciais']}\n
                        """ for c in batch]
                    import time
                    from langchain_community.callbacks.manager import get_openai_callback
                    from analises_llm import iniciar_modelo
                    modelo = iniciar_modelo()
                    with get_openai_callback() as cb:
                        start_time = time.time()
                        scores = analises_llm.gerar_score_curriculos_batch(batch_resumos, batch_descs)
                        processing_time = time.time() - start_time
                        n = len(scores)
                        tempo_por_curriculo = processing_time / n if n else 0
                        tokens_entrada = cb.prompt_tokens // n if n else 0
                        tokens_saida = cb.completion_tokens // n if n else 0
                        custo_chamada = cb.total_cost / n if n else 0
                        model_name = modelo.model_name if hasattr(modelo, 'model_name') else str(modelo)
                    # Atualização em batch
                    atualizar_score_curriculo(batch_ids, scores)
                    atualizar_tempo_execucao_score(batch_ids, [tempo_por_curriculo]*n)
                    atualizar_tokens_score(batch_ids, [tokens_entrada]*n, [tokens_saida]*n)
                    atualizar_llm_model(batch_ids, [model_name]*n)
                    atualizar_custo_score(batch_ids, [custo_chamada]*n)
                    processed_score += len(batch)
                    progresso_atual = (processed_score / total_score) * etapas['score']
                    progress_bar.progress(progresso_atual)
                    status_text.text(f"🧮 Gerando score dos currículos... ({processed_score}/{total_score})")
                    # Delay de 10 segundos entre batches, exceto após o último
                    if i + BATCH_SIZE < len(curriculos_score):
                        time.sleep(10)

            # Atualiza curriculos após score
            curriculos = listar_curriculos_por_usuario(st.session_state.get('user_id'))

            curriculos = pd.DataFrame(curriculos)
            curriculos = curriculos.loc[
                    (curriculos['status_md'] == True) &
                    (curriculos['status_resumo_llm'] == True) &
                    (curriculos['status_score_llm'] == True) &
                    (curriculos['status_opiniao_llm'] == False)
                ]

            ids_ultimos = st.session_state.get('ultimos_curriculos_upados')
            if ids_ultimos:
                curriculos = curriculos[curriculos['id_curriculo'].isin(ids_ultimos)]
            total_opiniao = len(curriculos)
            processed_opiniao = 0

            # 2. Opinião com LLM (em batch, apenas para quem atingiu score de corte)
            curriculos_opiniao = []
            for _, curriculo in curriculos.iterrows():
                score = curriculo['score_llm']
                if score is not None and float(score) > float(score_de_corte):
                    if curriculo['status_opiniao_llm'] == False and curriculo['resumo_llm']:
                        curriculos_opiniao.append(curriculo)
            if curriculos_opiniao:
                BATCH_SIZE = 40
                status_text.text("💬 Gerando análises críticas dos currículos...")
                for i in range(0, len(curriculos_opiniao), BATCH_SIZE):
                    batch = curriculos_opiniao[i:i+BATCH_SIZE]
                    batch_ids = [c['id_curriculo'] for c in batch]
                    batch_resumos = [c['resumo_llm'] for c in batch]
                    batch_descs = [f"""
                        Atividades: {c['atividades']}\n
                        Requisitos: {c['requisitos']}\n
                        Diferenciais: {c['diferenciais']}\n
                        """ for c in batch]
                    import time
                    from langchain_community.callbacks.manager import get_openai_callback
                    from analises_llm import iniciar_modelo
                    modelo = iniciar_modelo()
                    with get_openai_callback() as cb:
                        start_time = time.time()
                        opinioes = analises_llm.gerar_opiniao_curriculos_batch(batch_resumos, batch_descs)
                        processing_time = time.time() - start_time
                        n = len(opinioes)
                        tempo_por_curriculo = processing_time / n if n else 0
                        tokens_entrada = cb.prompt_tokens // n if n else 0
                        tokens_saida = cb.completion_tokens // n if n else 0
                        custo_chamada = cb.total_cost / n if n else 0
                        model_name = modelo.model_name if hasattr(modelo, 'model_name') else str(modelo)
                    # Atualização em batch
                    atualizar_opiniao_curriculo(batch_ids, opinioes)
                    atualizar_tempo_execucao_opiniao(batch_ids, [tempo_por_curriculo]*n)
                    atualizar_tokens_opiniao(batch_ids, [tokens_entrada]*n, [tokens_saida]*n)
                    atualizar_llm_model(batch_ids, [model_name]*n)
                    atualizar_custo_opiniao(batch_ids, [custo_chamada]*n)
                    processed_opiniao += len(batch)
                    progresso_atual = etapas['score'] + (processed_opiniao / total_opiniao) * etapas['opiniao']
                    progress_bar.progress(progresso_atual)
                    status_text.text(f"💬 Gerando análises críticas dos currículos... ({processed_opiniao}/{total_opiniao})")
                    # Delay de 10 segundos entre batches, exceto após o último
                    if i + BATCH_SIZE < len(curriculos_opiniao):
                        time.sleep(10)
            # Para quem não atingiu score de corte
            for _, curriculo in curriculos.iterrows():
                score = curriculo['score_llm']
                if not (score is not None and float(score) > float(score_de_corte)):
                    atualizar_opiniao_curriculo(curriculo['id_curriculo'], f"Candidato não atingiu a nota de corte ({score_de_corte}) para análise crítica.")
                    atualizar_tempo_execucao_opiniao(curriculo['id_curriculo'], 0)
                    atualizar_tokens_opiniao(curriculo['id_curriculo'], 0, 0)
                    atualizar_custo_opiniao(curriculo['id_curriculo'], 0)
            progress_bar.progress(1.0)
            status_text.text("✅ Processamento concluído!")
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