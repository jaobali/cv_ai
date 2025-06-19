import psycopg2
from dotenv import load_dotenv
import os
import streamlit as st

def get_connection():
    try:
        # Se st.secrets existir e tiver DB_HOST → Streamlit Cloud
        if st.secrets.get("DB_HOST"):
            return psycopg2.connect(
                host=st.secrets["DB_HOST"],
                port=int(st.secrets["DB_PORT"]),
                dbname=st.secrets["DB_NAME"],
                user=st.secrets["DB_USER"],
                password=st.secrets["DB_PASSWORD"],
                sslmode='require'
            )
    except Exception:
        # Se der qualquer erro ao acessar st.secrets → Continua e tenta .env
        pass

    # Ambiente local
    load_dotenv()
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode='require'
    )

def criar_tabelas():
    """Cria as tabelas necessárias no banco de dados PostgreSQL (Aiven)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT DEFAULT 'user',
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabela de vagas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vagas (
        id_vaga SERIAL PRIMARY KEY,
        nome_vaga TEXT NOT NULL,
        nome_empresa TEXT NOT NULL,
        atividades TEXT,
        requisitos TEXT,
        diferenciais TEXT,
        data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        id_usuario_cadastro_vaga INTEGER,
        fl_delete BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (id_usuario_cadastro_vaga) REFERENCES usuarios(id_usuario)
    )
    """)

    # Tabela de currículos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS curriculos (
        id_curriculo SERIAL PRIMARY KEY,
        id_vaga INTEGER,
        id_usuario_cadastro_curriculo INTEGER,
        nome_candidato TEXT,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fl_delete BOOLEAN DEFAULT FALSE,

        status_md BOOLEAN DEFAULT FALSE,
        status_resumo_llm BOOLEAN DEFAULT FALSE,
        status_opiniao_llm BOOLEAN DEFAULT FALSE,
        status_score_llm BOOLEAN DEFAULT FALSE,

        md TEXT,
        resumo_llm TEXT,
        opiniao_llm TEXT,
        score_llm FLOAT,

        md_time_execution FLOAT,
        resumo_llm_time_execution FLOAT,
        opiniao_llm_time_execution FLOAT,
        score_llm_time_execution FLOAT,

        resumo_llm_input_tokens INTEGER,
        resumo_llm_output_tokens INTEGER,
        resumo_llm_custo_chamada_USD FLOAT,

        opiniao_llm_input_tokens INTEGER,
        opiniao_llm_output_tokens INTEGER,
        opiniao_llm_custo_chamada_USD FLOAT,

        score_llm_input_tokens INTEGER,
        score_llm_output_tokens INTEGER,
        score_llm_custo_chamada_USD FLOAT,

        llm_model TEXT,

        FOREIGN KEY (id_vaga) REFERENCES vagas(id_vaga),
        FOREIGN KEY (id_usuario_cadastro_curriculo) REFERENCES usuarios(id_usuario)
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tabelas criadas com sucesso!")

if __name__ == "__main__":
    criar_tabelas()
