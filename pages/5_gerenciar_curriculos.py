import streamlit as st
from database import (
    listar_vagas_por_usuario,
    listar_curriculos_por_usuario,
    deletar_curriculo
)
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Gerenciar Currículos",
    page_icon="📄",
    layout="wide"
)

# CSS para remover botões padrão
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

################################################################

# Título da página
st.title("✂️ Gerenciar Currículos")

# Verifica se o usuário está logado
if not st.session_state.get('authentication_status'):
    st.warning("Você precisa estar logado para gerenciar currículos!")
    st.switch_page("0_login.py")

# Filtros
col1, col2, col3 = st.columns([40, 40, 20])


vagas = listar_vagas_por_usuario(st.session_state.get('user_id'))

if not vagas:
    st.warning("Você precisa cadastrar uma vaga antes de gerenciar currículos!")
else:
    # Adiciona a opção padrão "Selecione uma vaga"
    with col1:
        opcoes_vagas = [("", "Selecione uma vaga")] + [(v[0], v[1]) for v in vagas]
        filtro_vaga = st.selectbox(
            "Filtrar por vaga:",
            options=opcoes_vagas,
            format_func=lambda x: x[1]
        )

    # Só mostra o conteúdo se uma vaga válida for selecionada
    if filtro_vaga and filtro_vaga[0]:
        # Lista os currículos do usuário logado
        curriculos = listar_curriculos_por_usuario(st.session_state.get('user_id'))

        if curriculos:
            df_curriculos = pd.DataFrame(curriculos)
            df_curriculos = df_curriculos.loc[df_curriculos['id_vaga'] == filtro_vaga[0]]

            if len(df_curriculos) == 0:
                st.warning("Nenhum currículo encontrado com os filtros selecionados!")
            else:
                with col2:
                    filtro_candidato = st.selectbox(
                        "Filtrar por candidato:",
                        options= ["Todos"] + (df_curriculos['nome_candidato'].tolist())
                    )
                if filtro_candidato != "Todos":
                    df_curriculos = df_curriculos.loc[
                        (df_curriculos['nome_candidato'] == filtro_candidato)
                    ]

                with col3:
                    st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                    if st.button("🗑️ Excluir Tudo",
                                key="delete_all",
                                use_container_width=True):
                        st.session_state.show_delete_all_dialog = True

        else:
            st.warning("Nenhum currículo encontrado para esta vaga")

    # Lista de currículos individuais
    if filtro_vaga and filtro_vaga[0]:
        if curriculos:
            col_a, col_b = st.columns(2)
            for idx, (_, curriculo) in enumerate(df_curriculos.iterrows()):
                target_col = col_a if idx % 2 == 0 else col_b
                with target_col:
                    with st.container(border=True):
                        cols = st.columns([0.7, 0.3])
                        # Coluna 1: Metadados
                        with cols[0]:
                            st.markdown(f"### {curriculo['nome_candidato']}")
                            st.caption(f"**Enviado em:** {curriculo['data_upload']}")
                        # Coluna 2: Ações
                        with cols[1]:
                            st.markdown('<div style="margin-top: 22px;"></div>', unsafe_allow_html=True)
                            if st.button("🗑️ Excluir",
                                key=f"del_{curriculo['id_curriculo']}",
                                use_container_width=True):
                                st.session_state.show_delete_dialog = True
                                st.session_state.curriculo_to_delete = curriculo

# Dialog para excluir um currículo específico
@st.dialog("Confirmar Exclusão")
def delete_curriculo_dialog():
    curriculo = st.session_state.curriculo_to_delete
    st.write(f"⚠️ Você está prestes a excluir o currículo de {curriculo['nome_candidato']}.")
    st.write("Esta ação não pode ser desfeita!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirmar", type="primary", use_container_width=True):
            # Remove do banco de dados
            deletar_curriculo(curriculo['id_curriculo'])
            st.session_state.show_delete_dialog = False
            st.rerun()

    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.show_delete_dialog = False
            st.rerun()

# Dialog para excluir todos os currículos
@st.dialog("Confirmar Exclusão")
def delete_all_curriculos_dialog():
    st.write("⚠️ Você está prestes a excluir TODOS os currículos desta vaga.")
    st.write("Esta ação não pode ser desfeita!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirmar", type="primary", use_container_width=True):
            # Deleta todos os currículos da vaga selecionada
            for _, curriculo in df_curriculos.iterrows():
                # Remove do banco de dados
                deletar_curriculo(curriculo['id_curriculo'])
            st.session_state.show_delete_all_dialog = False
            st.rerun()

    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.show_delete_all_dialog = False
            st.rerun()

# Inicializa as variáveis de estado se não existirem
if 'show_delete_dialog' not in st.session_state:
    st.session_state.show_delete_dialog = False
if 'show_delete_all_dialog' not in st.session_state:
    st.session_state.show_delete_all_dialog = False

# Mostra os diálogos se necessário
if st.session_state.show_delete_dialog:
    delete_curriculo_dialog()
if st.session_state.show_delete_all_dialog:
    delete_all_curriculos_dialog()