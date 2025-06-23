import streamlit as st
from database import (
    listar_vagas_por_usuario,
    inserir_curriculo,
    atualizar_md_curriculo,
    listar_curriculos_por_usuario,
    atualizar_resumo_curriculo,
    atualizar_nome_candidato,
    atualizar_tempo_execucao_md,
    atualizar_tempo_execucao_resumo,
    atualizar_tokens_resumo,
    atualizar_llm_model,
    atualizar_custo_resumo
)
from datetime import datetime
# from docling.document_converter import DocumentConverter
from pathlib import Path
import pandas as pd
from analises_llm import gerar_resumo_curriculo
import json
import time
import os
import shutil

from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

artifacts_dir = Path(__file__).parent.parent / "docling_models"

pipeline_options = PdfPipelineOptions(
    artifacts_path=str(artifacts_dir),
    # Se quiser OCR:
    # ocr_options=EasyOcrOptions(download_enabled=False)
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)


# Configuração da página
st.set_page_config(
    page_title="Enviar Currículo",
    page_icon="📤",
    layout="centered"
)

# INJEÇÃO DE CSS PARA REMOVER OS BOTÕES PADRÃO
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
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
    st.page_link("pages/6_analises_ia.py", label="🤖 Análises com IA", use_container_width=True)
    st.markdown("---")
    if st.session_state.get('authentication_status'):
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.clear()
            st.switch_page("0_login.py")
    st.caption("Versão 1.0 | © 2025")

st.logo(image = "imagens/BeAI.svg", icon_image = "imagens/captal_lambda_branco.png")


# Verifica se o usuário está logado
if not st.session_state.get('authentication_status'):
    st.switch_page("0_login.py")

######################################################

st.title("📤 Enviar Currículos")
st.markdown("---")

# Lista as vagas do usuário logado
vagas = listar_vagas_por_usuario(st.session_state.get('user_id'))

if not vagas:
    st.warning("Você precisa cadastrar uma vaga antes de enviar currículos!")
else:
    # Adiciona a opção padrão "Selecione uma vaga"
    opcoes_vagas = [("", "Selecione uma vaga")] + vagas
    vaga_selecionada = st.selectbox(
        "Selecione a vaga para enviar currículos:",
        options=opcoes_vagas,
        format_func=lambda x: x[1]  # Mostra o nome da vaga
    )

    # Só mostra o conteúdo se uma vaga válida for selecionada
    if vaga_selecionada and vaga_selecionada[0]:  # Verifica se não é a opção padrão
        # Passo 2: Upload de currículos
        # st.subheader("Upload de Currículos")
        arquivos = st.file_uploader(
            "Upload de Currículos",
            type=['pdf', 'docx', 'doc', 'txt', 'rtf'],
            accept_multiple_files=True
        )

        if arquivos and vaga_selecionada:
            if st.button("Enviar Currículos", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                sucessos = 0
                erros = 0
                total_arquivos = len(arquivos)

                # Define as etapas do processo e seus pesos
                etapas = {
                    'upload': 0.3,  # 30% do processo
                    'markdown': 0.3,  # 30% do processo
                    'resumo': 0.2,  # 20% do processo
                    'nome': 0.2  # 20% do processo
                }
                progresso_atual = 0

                UPLOAD_DIR = "curriculos_temp"
                os.makedirs(UPLOAD_DIR, exist_ok=True)

                # Etapa 1: Upload dos arquivos
                status_text.text("📤 Fazendo upload dos currículos...")
                caminhos_arquivos = []
                for i, arquivo in enumerate(arquivos):
                    try:
                        # Gera nome único para o arquivo
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nome_arquivo = f"{timestamp}_{arquivo.name}"
                        caminho_arquivo = os.path.join(UPLOAD_DIR, nome_arquivo)
                        # Salva o arquivo no disco temporariamente
                        with open(caminho_arquivo, "wb") as f:
                            f.write(arquivo.getbuffer())
                        caminhos_arquivos.append(caminho_arquivo)
                        # Insere no banco de dados (sem o caminho do arquivo)
                        inserir_curriculo(vaga_selecionada[0], st.session_state.get('user_id'))
                        sucessos += 1
                    except Exception as e:
                        st.error(f"Erro ao processar {arquivo.name}: {str(e)}")
                        erros += 1

                    # Atualiza progresso da etapa de upload
                    progresso_etapa = (i + 1) / total_arquivos
                    progresso_atual = progresso_etapa * etapas['upload']
                    progress_bar.progress(progresso_atual)

                # Etapa 2: Gerando Markdown
                status_text.text("📝 Gerando Markdown dos currículos...")
                curriculos_cadastrados = listar_curriculos_por_usuario(st.session_state.get('user_id'))
                df_curriculos_cadastrados = pd.DataFrame(curriculos_cadastrados)
                df_curriculos_cadastrados = df_curriculos_cadastrados.loc[df_curriculos_cadastrados['status_md'] == False]

                # Processa apenas os currículos que acabaram de ser inseridos
                curriculos_para_processar = df_curriculos_cadastrados.tail(len(caminhos_arquivos))

                total_md = len(curriculos_para_processar)
                for i, (index, row) in enumerate(curriculos_para_processar.iterrows()):
                    start_time = time.time()
                    converter = DocumentConverter()
                    doc = converter.convert(str(Path(caminhos_arquivos[i])))
                    md = doc.document.export_to_markdown()
                    processing_time = time.time() - start_time

                    atualizar_md_curriculo(row['id_curriculo'], md)
                    atualizar_tempo_execucao_md(row['id_curriculo'], processing_time)

                    # Atualiza progresso da etapa de markdown
                    progresso_etapa = (i + 1) / total_md
                    progresso_atual = etapas['upload'] + (progresso_etapa * etapas['markdown'])
                    progress_bar.progress(progresso_atual)

                # Após gerar todos os md, deletar a pasta temporária
                try:
                    shutil.rmtree(UPLOAD_DIR)
                except Exception as e:
                    st.warning(f"Não foi possível remover a pasta temporária: {str(e)}")

                # Etapa 3: Gerando Resumo
                status_text.text("🤖 Gerando resumos dos currículos...")
                curriculos_cadastrados = listar_curriculos_por_usuario(st.session_state.get('user_id'))
                df_curriculos_cadastrados = pd.DataFrame(curriculos_cadastrados)
                df_curriculos_cadastrados = df_curriculos_cadastrados.loc[df_curriculos_cadastrados['status_resumo_llm'] == False]
                arquivos_para_resumo = df_curriculos_cadastrados[['id_curriculo','md']]

                total_resumo = len(arquivos_para_resumo)
                for i, (index, row) in enumerate(arquivos_para_resumo.iterrows()):
                    resumo, processing_time, input_tokens, output_tokens, model_name, custo_chamada = gerar_resumo_curriculo(row['md'])
                    atualizar_resumo_curriculo(row['id_curriculo'], resumo.model_dump_json())
                    atualizar_tempo_execucao_resumo(row['id_curriculo'], processing_time)
                    atualizar_tokens_resumo(row['id_curriculo'], input_tokens, output_tokens)
                    atualizar_llm_model(row['id_curriculo'], model_name)
                    atualizar_custo_resumo(row['id_curriculo'], custo_chamada)

                    # Atualiza progresso da etapa de resumo
                    progresso_etapa = (i + 1) / total_resumo
                    progresso_atual = etapas['upload'] + etapas['markdown'] + (progresso_etapa * etapas['resumo'])
                    progress_bar.progress(progresso_atual)

                # Etapa 4: Extraindo nomes
                status_text.text("👤 Extraindo nomes dos candidatos...")
                curriculos_cadastrados = listar_curriculos_por_usuario(st.session_state.get('user_id'))
                df_curriculos_cadastrados = pd.DataFrame(curriculos_cadastrados)
                df_curriculos_cadastrados = df_curriculos_cadastrados.loc[
                    (df_curriculos_cadastrados['status_md'] == True) &
                    (df_curriculos_cadastrados['status_resumo_llm'] == True)
                ]
                arquivos_para_nome_candidato = df_curriculos_cadastrados[['id_curriculo','resumo_llm']]

                total_nomes = len(arquivos_para_nome_candidato)
                for i, (index, row) in enumerate(arquivos_para_nome_candidato.iterrows()):
                    resumo_json = json.loads(json.loads(row['resumo_llm']))
                    nome_candidato = resumo_json['nome_completo']
                    atualizar_nome_candidato(row['id_curriculo'], nome_candidato)

                    # Atualiza progresso da etapa de nomes
                    progresso_etapa = (i + 1) / total_nomes
                    progresso_atual = etapas['upload'] + etapas['markdown'] + etapas['resumo'] + (progresso_etapa * etapas['nome'])
                    progress_bar.progress(progresso_atual)

                # Finaliza o progresso
                progress_bar.progress(1.0)
                status_text.text("✅ Processamento concluído!")
                progress_bar.empty()
                status_text.empty()

                if sucessos > 0:
                    st.success(f"✅ {sucessos} currículo(s) enviado(s) com sucesso!")
                if erros > 0:
                    st.error(f"❌ {erros} currículo(s) falhou/falharam no envio.")
