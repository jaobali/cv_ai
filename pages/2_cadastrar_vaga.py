import streamlit as st
from database import inserir_vaga


# Configuração da página
st.set_page_config(
    page_title="Cadastrar Vaga - Analisador CV IA",
    page_icon="📋",
    layout="wide"
)

# INJEÇÃO DE CSS PARA REMOVER OS BOTÕES PADRÃO
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# --- MENU LATERAL ---
with st.sidebar:
    st.title("📋 Menu")
    st.markdown("---")
    st.page_link("pages/1_home.py", label="🏠 Página Inicial", use_container_width=True)
    st.page_link("pages/2_cadastrar_vaga.py", label="➕ Cadastrar Vaga", use_container_width=True)
    st.page_link("pages/3_gerenciar_vagas.py", label="✂️ Gerenciar Vagas", use_container_width=True)
    st.page_link("pages/4_enviar_curriculos.py", label="📤 Enviar Currículo", use_container_width=True)
    st.page_link("pages/5_gerenciar_curriculos.py", label="✂️ Gerenciar Currículos", use_container_width=True)
    st.page_link("pages/6_analises_ia.py", label="🤖 Análises com IA", use_container_width=True)
    st.markdown("---")
    if st.session_state.get('authentication_status'):
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.switch_page("0_login.py")
    st.caption("Versão 1.0 | © 2025")

st.logo(image = "imagens/BeAI.svg", icon_image = "imagens/captal_lambda_branco.png")

#################################################################################

# Título da página
st.markdown("""
<div style='text-align: center; margin-bottom: 30px;'>
    <h1>Cadastro de Nova Vaga</h1>
</div>
""", unsafe_allow_html=True)

if not st.session_state.get('authentication_status'):
    st.switch_page("0_login.py")

# Formulário de cadastro
with st.form(key='form_criar_vaga', enter_to_submit=False, clear_on_submit=True):

    nome_vaga = st.text_input("Nome da Vaga", placeholder="Ex: Desenvolvedor Python")
    nome_empresa = st.text_input("Nome da Empresa", placeholder="Ex: Tech Solutions")
    atividades = st.text_area("Atividades", placeholder="Descreva as atividades da vaga...")
    requisitos = st.text_area("Requisitos", placeholder="Liste os requisitos da vaga...")
    diferenciais = st.text_area("Diferenciais", placeholder="Liste os diferenciais da vaga...")
    
    submitted = st.form_submit_button("Criar Vaga")
    
    if submitted:
        if not nome_vaga or not nome_empresa:
            st.error("Por favor, preencha o nome da vaga e o nome da empresa.")
        else:
            try:
                inserir_vaga(nome_vaga, nome_empresa, atividades, requisitos, diferenciais, st.session_state.get('user_id'))
                st.success("Vaga criada com sucesso!")
                st.balloons()
                # st.rerun()
            except Exception as e:
                st.error(f"Erro ao criar vaga: {str(e)}")