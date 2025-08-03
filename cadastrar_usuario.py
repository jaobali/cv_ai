import streamlit as st
from database import (
    criar_usuario,
    alterar_senha_usuario,
)
import time

# Configuração da página
st.set_page_config(
    page_title="Login and Register",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)


st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    .small-font { font-size: 0.9rem !important; }
    
    /* Estilos personalizados para o botão */
    div[data-testid="stButton"] > button {
        width: 50%;
        height: 3.5rem;
        font-size: 1.2rem;
        font-weight: 600;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background-color: #56aa8a;
        color: #1E1E1E;
        border: none;
        transition: all 0.3s ease;
    }
    
    div[data-testid="stButton"] > button:hover {
        background-color: #56aa8a;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    div[data-testid="stButton"] > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)


tab1, tab2 = st.tabs(["Cadastrar Novo Usuário", "Alterar Senha"])

with tab1:
    with st.form("register_form", enter_to_submit=False):
        st.title("Registro")
        new_username = st.text_input("Novo usuário")
        new_email = st.text_input("Email")
        empresa = st.text_input("Empresa")
        new_password = '123456'
        submit = st.form_submit_button("Registrar")
        if submit:
            if criar_usuario(new_username, new_password, new_email, empresa):
                st.success("Usuário registrado com sucesso!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Nome de usuário ou email já existente")

with tab2:
    with st.form("password_form", enter_to_submit=False):
        st.title("Alterar Senha")
        # Carrega dados salvos para usar como valor padrão

        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        new_password = st.text_input("Nova senha", type="password")
        if st.form_submit_button("Alterar Senha"):
            if alterar_senha_usuario(email, new_password):
                st.success("Senha alterada com sucesso!")
            else:
                st.error("Erro ao alterar senha")
