import json
import hashlib
import secrets
import psycopg2
from dotenv import load_dotenv
import os
import streamlit as st


def get_connection():
    # Primeiro tenta carregar do Streamlit Cloud
    if "DB_HOST" in st.secrets:
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            port=st.secrets["DB_PORT"],
            dbname=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            sslmode='require'
        )
    else:
        # Se estiver rodando localmente, carrega do .env
        from dotenv import load_dotenv
        load_dotenv()
        return psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            sslmode='require'
        )

def criar_tabelas():
    """Cria as tabelas necessárias no banco de dados Supabase/PostgreSQL"""
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


def inserir_vaga(nome_vaga, nome_empresa, atividades, requisitos, diferenciais, id_usuario):
    """Adiciona uma nova vaga ao banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO vagas (nome_vaga, nome_empresa, atividades, requisitos, diferenciais, id_usuario_cadastro_vaga)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (nome_vaga, nome_empresa, atividades, requisitos, diferenciais, id_usuario))

    conn.commit()
    cursor.close()
    conn.close()

def listar_vagas():
    """Retorna todas as vagas cadastradas não deletadas"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM vagas
    WHERE fl_delete = FALSE
    ORDER BY data_cadastro DESC
    """)

    colunas = [desc[0] for desc in cursor.description]
    vagas = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return vagas

def listar_vagas_por_usuario(id_usuario):
    """Retorna as vagas cadastradas por um usuário específico que não foram deletadas"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM vagas
    WHERE id_usuario_cadastro_vaga = %s AND fl_delete = FALSE
    ORDER BY data_cadastro DESC
    """, (id_usuario,))
    vagas = cursor.fetchall()
    cursor.close()
    conn.close()
    return vagas

def deletar_vaga(vaga_id):
    """Marca uma vaga como deletada no banco de dados pelo ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE vagas SET fl_delete = TRUE WHERE id_vaga = %s", (vaga_id,))

    conn.commit()
    cursor.close()
    conn.close()

# Novas funções para currículos
def inserir_curriculo(id_vaga, id_usuario):
    """Adiciona um novo currículo ao banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO curriculos (id_vaga, id_usuario_cadastro_curriculo)
    VALUES (%s, %s)
    """, (id_vaga, id_usuario))

    conn.commit()
    cursor.close()
    conn.close()


def listar_curriculos():
    """Retorna todos os currículos cadastrados não deletados"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.*, v.nome_vaga as nome
    FROM curriculos c
    LEFT JOIN vagas v ON c.id_vaga = v.id_vaga
    WHERE c.fl_delete = FALSE
    ORDER BY c.data_upload DESC
    """)

    colunas = [desc[0] for desc in cursor.description]
    curriculos = [dict(zip(colunas, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()
    return curriculos

def listar_curriculos_por_usuario(id_usuario):
    """Retorna os currículos cadastrados por um usuário específico que não foram deletados"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT c.*, v.*
    FROM curriculos c
    LEFT JOIN vagas v ON c.id_vaga = v.id_vaga
    WHERE c.id_usuario_cadastro_curriculo = %s AND c.fl_delete = FALSE
    ORDER BY c.data_upload DESC
    """, (id_usuario,))
    colunas = [desc[0] for desc in cursor.description]
    curriculos = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return curriculos

def deletar_curriculo(curriculo_id):
    """Marca um currículo como deletado no banco de dados pelo ID"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE curriculos SET fl_delete = TRUE WHERE id_curriculo = %s", (curriculo_id,))

    conn.commit()
    cursor.close()
    conn.close()

def atualizar_md_curriculo(id_curriculo, md):
    """Atualiza o MD do currículo e marca como convertido"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE curriculos
        SET md = %s, status_md = TRUE
        WHERE id_curriculo = %s
    """, (md, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_resumo_curriculo(id_curriculo, resumo: dict):
    """Atualiza o resumo LLM no banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()
    resumo_json = json.dumps(resumo, ensure_ascii=False)
    cursor.execute("""
    UPDATE curriculos
    SET resumo_llm = %s, status_resumo_llm = TRUE
    WHERE id_curriculo = %s
    """, (resumo_json, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_nome_candidato(id_curriculo, nome_candidato):
    """Atualiza o nome do candidato no banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE curriculos
    SET nome_candidato = %s
    WHERE id_curriculo = %s
    """, (nome_candidato, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_opiniao_curriculo(id_curriculo, opiniao_llm):
    """Atualiza a opinião LLM do currículo e marca como processado"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE curriculos
        SET opiniao_llm = %s, status_opiniao_llm = TRUE
        WHERE id_curriculo = %s
    """, (opiniao_llm, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_score_curriculo(id_curriculo, score):
    """Atualiza o score LLM do currículo e marca como processado"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE curriculos
        SET score_llm = %s, status_score_llm = TRUE
        WHERE id_curriculo = %s
    """, (score, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def criar_usuario(username, password, email, role='user'):
    """Cria um novo usuário no banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()

    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()

    try:
        cursor.execute("""
        INSERT INTO usuarios (username, password_hash, salt, email, role)
        VALUES (%s, %s, %s, %s, %s)
        """, (username, password_hash, salt, email, role))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verificar_usuario(username, password):
    """Verifica as credenciais do usuário"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id_usuario, password_hash, salt, role
    FROM usuarios
    WHERE username = %s
    """, (username,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        id_usuario, stored_hash, salt, role = result
        input_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        if input_hash == stored_hash:
            return {"id": id_usuario, "username": username, "role": role}
    return None

def listar_usuarios():
    """Retorna todos os usuários cadastrados"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id_usuario, username, email, role, data_criacao
    FROM usuarios
    ORDER BY data_criacao DESC
    """)

    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return usuarios

def deletar_usuario(id_usuario):
    """Remove um usuário do banco de dados"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
    conn.commit()
    cursor.close()
    conn.close()

def contar_vagas_ativas_por_usuario(id_usuario):
    """Retorna o número de vagas ativas cadastradas por um usuário específico"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) FROM vagas
    WHERE id_usuario_cadastro_vaga = %s
    """, (id_usuario,))

    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

def contar_curriculos_por_usuario(id_usuario):
    """Retorna o número de currículos cadastrados por um usuário específico"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) FROM curriculos
    WHERE id_usuario_cadastro_curriculo = %s
    """, (id_usuario,))

    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

def atualizar_tempo_execucao_md(id_curriculo, tempo_segundos):
    """Atualiza o tempo de execução do markdown em segundos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE curriculos 
    SET md_time_execution = %s
    WHERE id_curriculo = %s
    """, (tempo_segundos, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_tempo_execucao_resumo(id_curriculo, tempo_segundos):
    """Atualiza o tempo de execução do resumo em segundos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE curriculos 
    SET resumo_llm_time_execution = %s
    WHERE id_curriculo = %s
    """, (tempo_segundos, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_tempo_execucao_opiniao(id_curriculo, tempo_segundos):
    """Atualiza o tempo de execução da opinião em segundos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE curriculos 
    SET opiniao_llm_time_execution = %s
    WHERE id_curriculo = %s
    """, (tempo_segundos, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_tempo_execucao_score(id_curriculo, tempo_segundos):
    """Atualiza o tempo de execução do score em segundos"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE curriculos 
    SET score_llm_time_execution = %s
    WHERE id_curriculo = %s
    """, (tempo_segundos, id_curriculo))
    conn.commit()
    cursor.close()
    conn.close()

def atualizar_tokens_resumo(id_curriculo, input_tokens, output_tokens):
    """Atualiza os tokens de input e output do resumo LLM"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE curriculos
    SET resumo_llm_input_tokens = %s, resumo_llm_output_tokens = %s
    WHERE id_curriculo = %s
    """, (input_tokens, output_tokens, id_curriculo))

    conn.commit()
    cursor.close()
    conn.close()

def atualizar_tokens_opiniao(id_curriculo, input_tokens, output_tokens):
    """Atualiza os tokens de input e output da opinião LLM"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE curriculos
    SET opiniao_llm_input_tokens = %s, opiniao_llm_output_tokens = %s
    WHERE id_curriculo = %s
    """, (input_tokens, output_tokens, id_curriculo))

    conn.commit()
    cursor.close()
    conn.close()

def atualizar_tokens_score(id_curriculo, input_tokens, output_tokens):
    """Atualiza os tokens de input e output do score LLM"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE curriculos
    SET score_llm_input_tokens = %s, score_llm_output_tokens = %s
    WHERE id_curriculo = %s
    """, (input_tokens, output_tokens, id_curriculo))

    conn.commit()
    cursor.close()
    conn.close()

def atualizar_llm_model(id_curriculo, model_name):
    """Atualiza o modelo LLM utilizado"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE curriculos
    SET llm_model = %s
    WHERE id_curriculo = %s
    """, (model_name, id_curriculo))

    conn.commit()
    cursor.close()
    conn.close()

def atualizar_custo_resumo(id_curriculo, custo_chamada):
    """Atualiza o custo da chamada do resumo LLM em USD"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE curriculos
    SET resumo_llm_custo_chamada_USD = %s
    WHERE id_curriculo = %s
    """, (custo_chamada, id_curriculo))

    conn.commit()
    cursor.close()
    conn.close()

def atualizar_custo_opiniao(id_curriculo, custo_chamada):
    """Atualiza o custo da chamada da opinião LLM em USD"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE curriculos
    SET opiniao_llm_custo_chamada_USD = %s
    WHERE id_curriculo = %s
    """, (custo_chamada, id_curriculo))

    conn.commit()
    cursor.close()
    conn.close()

def atualizar_custo_score(id_curriculo, custo_chamada):
    """Atualiza o custo da chamada do score em USD"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE curriculos
    SET score_llm_custo_chamada_USD = %s
    WHERE id_curriculo = %s
    """, (custo_chamada, id_curriculo))

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    criar_tabelas()