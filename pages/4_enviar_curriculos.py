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
    atualizar_custo_resumo,
    atualizar_curriculos_simultaneos_resumo,
)
from datetime import datetime
from pathlib import Path
import pandas as pd
from analises_llm import gerar_resumo_curriculos_batch
import json
import time
import os
import shutil

from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

import psutil
# import os

from langchain_community.callbacks.manager import get_openai_callback

artifacts_dir = Path(__file__).parent.parent / "docling_models"

pipeline_options = PdfPipelineOptions(
    artifacts_path = str(artifacts_dir),
    do_table_structure = False,  # True: perform table structure extraction
    do_ocr = False,  # True: perform OCR, replace programmatic PDF text
    do_code_enrichment = False,  # True: perform code OCR
    do_formula_enrichment = False,  # True: perform formula OCR, return Latex code
    do_picture_classification = False , # True: classify pictures in documents
    do_picture_description = False , # True: run describe pictures in documents
    force_backend_text = False,  # (To be used with vlms, or other generative models)
    # If True, text from backend will be used instead of generated text

    # table_structure_options: TableStructureOptions = TableStructureOptions()
    ocr_options = EasyOcrOptions(),
    # picture_description_options: PictureDescriptionBaseOptions = (
    #     smolvlm_picture_description
    # )

    # images_scale: float = 1.0
    generate_page_images = False,
    generate_picture_images = False,
    generate_table_images = False,
    generate_parsed_pages = True
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

def get_memory_usage():
    """Retorna o uso atual de memória RAM do processo do app em MB"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_usage_mb = mem_info.rss / (1024 ** 2)  # RSS: memória residente
    return mem_usage_mb

# Mostra o uso de RAM na tela
# ram = get_memory_usage()
# st.write(f"**Uso atual de RAM:** `{ram:.2f} MB`")

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
    st.page_link("pages/6_analises_ia.py", label="🧠 Análises com IA", use_container_width=True)
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
                st.warning("⚠️ Não saia desta página enquanto o processamento estiver em andamento!")
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
                curriculos_para_processar = df_curriculos_cadastrados.sort_values('id_curriculo').tail(len(caminhos_arquivos))

                ids_ultimos_upados = curriculos_para_processar['id_curriculo'].tolist()
                st.session_state['ultimos_curriculos_upados'] = ids_ultimos_upados

                total_md = len(curriculos_para_processar)
                arquivos_grandes = []  # Lista para armazenar nomes de arquivos grandes
                arquivos_invalidos = []  # Lista para armazenar arquivos que deram erro de conversão
                for i, (index, row) in enumerate(curriculos_para_processar.iterrows()):
                    start_time = time.time()
                    caminho_arquivo = str(Path(caminhos_arquivos[i]))
                    # Verifica tamanho do arquivo antes de processar
                    tamanho_arquivo = os.path.getsize(caminho_arquivo)
                    if tamanho_arquivo > 5_000_000:  # 5MB
                        arquivos_grandes.append(os.path.basename(caminho_arquivo))
                        erros += 1
                    else:
                        try:
                            doc = converter.convert(
                                caminho_arquivo,
                                max_num_pages=20,
                                max_file_size=5_000_000
                            )
                            md = doc.document.export_to_markdown()
                            processing_time = time.time() - start_time

                            atualizar_md_curriculo(row['id_curriculo'], md)
                            atualizar_tempo_execucao_md(row['id_curriculo'], processing_time)
                        except Exception as e:
                            if os.path.basename(caminho_arquivo) not in arquivos_grandes:
                                arquivos_invalidos.append(f"{os.path.basename(caminho_arquivo)} (erro: {str(e)})")
                                erros += 1
                            # Opcional: log detalhado para debug
                            print(f"Erro ao converter {caminho_arquivo}: {e}")
                    # Atualiza progresso da etapa de markdown (sempre avança, independente de erro)
                    progresso_etapa = (i + 1) / total_md
                    progresso_atual = etapas['upload'] + (progresso_etapa * etapas['markdown'])
                    progress_bar.progress(progresso_atual)

                # Após gerar todos os md, deletar a pasta temporária
                try:
                    shutil.rmtree(UPLOAD_DIR)
                except Exception as e:
                    st.warning(f"Não foi possível remover a pasta temporária: {str(e)}")

                # Exibe mensagem sobre arquivos grandes não processados
                if arquivos_grandes:
                    st.warning(f"Os seguintes arquivos não foram processados por excederem o tamanho máximo permitido (5MB): {', '.join(arquivos_grandes)}")
                # Exibe mensagem sobre arquivos inválidos
                if arquivos_invalidos:
                    st.warning(f"Os seguintes arquivos não foram processados por erro de conversão ou formato inválido: {', '.join(arquivos_invalidos)}")

                # Etapa 3: Gerando Resumo
                status_text.text("🧠 Gerando resumos dos currículos...")
                curriculos_cadastrados = listar_curriculos_por_usuario(st.session_state.get('user_id'))

                # Se houver ids de últimos upados na sessão, filtra só eles
                ids_ultimos = st.session_state.get('ultimos_curriculos_upados')
                if ids_ultimos:
                    curriculos_cadastrados = [c for c in curriculos_cadastrados if c['id_curriculo'] in ids_ultimos]

                df_curriculos_cadastrados = pd.DataFrame(curriculos_cadastrados)
                df_curriculos_cadastrados = df_curriculos_cadastrados.loc[
                    (df_curriculos_cadastrados['status_resumo_llm'] == False) &
                    (df_curriculos_cadastrados['md'].notnull()) &
                    (df_curriculos_cadastrados['md'].str.strip() != '')
                ]
                arquivos_para_resumo = df_curriculos_cadastrados[['id_curriculo','md']]

                # Limite de 40 currículos por batch (OpenAI docs, gpt-4o-mini)
                BATCH_SIZE = 40
                lista_markdowns = arquivos_para_resumo['md'].tolist()
                ids = arquivos_para_resumo['id_curriculo'].tolist()

                def split_batches(lista, batch_size):
                    for i in range(0, len(lista), batch_size):
                        yield lista[i:i + batch_size]

                total_resumo = len(lista_markdowns)
                batches = list(split_batches(list(zip(ids, lista_markdowns)), BATCH_SIZE))
                batch_count = len(batches)
                processed = 0

                for batch_idx, batch in enumerate(batches):
                    batch_ids, batch_markdowns = zip(*batch)
                    from langchain_community.callbacks.manager import get_openai_callback
                    from analises_llm import iniciar_modelo
                    with get_openai_callback() as cb:
                        start_time = time.time()
                        modelo = iniciar_modelo()
                        resultados = gerar_resumo_curriculos_batch(list(batch_markdowns))
                        processing_time = time.time() - start_time
                        n = len(resultados)
                        tempo_por_curriculo = processing_time / n if n else 0
                        tokens_entrada = cb.prompt_tokens // n if n else 0
                        tokens_saida = cb.completion_tokens // n if n else 0
                        custo_chamada = cb.total_cost / n if n else 0
                        model_name = modelo.model_name if hasattr(modelo, 'model_name') else str(modelo)
                    # Atualização em lote usando as funções otimizadas
                    atualizar_resumo_curriculo(list(batch_ids), [r.model_dump() for r in resultados])
                    atualizar_tempo_execucao_resumo(list(batch_ids), [tempo_por_curriculo]*n)
                    atualizar_tokens_resumo(list(batch_ids), [tokens_entrada]*n, [tokens_saida]*n)
                    atualizar_llm_model(list(batch_ids), [model_name]*n)
                    atualizar_custo_resumo(list(batch_ids), [custo_chamada]*n)
                    # NOVO: Atualiza curriculos_simultaneos_resumo
                    atualizar_curriculos_simultaneos_resumo(list(batch_ids), [n]*n)
                    processed += len(batch)
                    progresso_atual = etapas['upload'] + etapas['markdown'] + (processed / total_resumo) * etapas['resumo']
                    progress_bar.progress(progresso_atual)
                    # Delay de 10 segundos entre batches, exceto após o último
                    if batch_idx < len(batches) - 1:
                        time.sleep(10)

                # Etapa 4: Extraindo nomes
                status_text.text("👤 Extraindo nomes dos candidatos...")
                curriculos_cadastrados = listar_curriculos_por_usuario(st.session_state.get('user_id'))

                # Se houver ids de últimos upados na sessão, filtra só eles
                ids_ultimos = st.session_state.get('ultimos_curriculos_upados')
                if ids_ultimos:
                    curriculos_cadastrados = [c for c in curriculos_cadastrados if c['id_curriculo'] in ids_ultimos]

                df_curriculos_cadastrados = pd.DataFrame(curriculos_cadastrados)
                df_curriculos_cadastrados = df_curriculos_cadastrados.loc[
                    (df_curriculos_cadastrados['status_md'] == True) &
                    (df_curriculos_cadastrados['status_resumo_llm'] == True) &
                    (df_curriculos_cadastrados['md'].notnull()) &
                    (df_curriculos_cadastrados['md'].str.strip() != '')
                ]
                arquivos_para_nome_candidato = df_curriculos_cadastrados[['id_curriculo','resumo_llm']]

                total_nomes = len(arquivos_para_nome_candidato)
                nomes_extraidos = []
                ids_nomes = []
                for i, (index, row) in enumerate(arquivos_para_nome_candidato.iterrows()):
                    nome_candidato = "nao encontrado"
                    try:
                        resumo_json = json.loads(json.loads(row['resumo_llm']))
                        nome_candidato = resumo_json['nome_completo']
                    except Exception:
                        try:
                            resumo_json = json.loads(row['resumo_llm'])
                            nome_candidato = resumo_json['nome_completo']
                        except Exception:
                            nome_candidato = "nao encontrado"
                    if isinstance(nome_candidato, list):
                        nome_candidato = nome_candidato[0]
                    nomes_extraidos.append(nome_candidato)
                    ids_nomes.append(row['id_curriculo'])
                    # Atualiza progresso da etapa de nomes
                    progresso_etapa = (i + 1) / total_nomes
                    progresso_atual = etapas['upload'] + etapas['markdown'] + etapas['resumo'] + (progresso_etapa * etapas['nome'])
                    progress_bar.progress(progresso_atual)
                # Atualização em batch dos nomes
                if ids_nomes:
                    atualizar_nome_candidato(ids_nomes, nomes_extraidos)

                # Finaliza o progresso e exibe mensagem de conclusão após extração de nomes
                progress_bar.progress(1.0)
                status_text.text("✅ Processamento concluído!")
                progress_bar.empty()
                st.session_state['processando_curriculos'] = False
