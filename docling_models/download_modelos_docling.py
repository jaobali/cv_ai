from docling.utils.model_downloader import download_models
from pathlib import Path

if __name__ == "__main__":
    print("Baixando apenas o modelo de layout necessário para o Docling...")
    download_models(
        output_dir=Path("docling_models"),
        force=False,
        progress=True,
        with_layout=True,           # Só layout
        with_tableformer=False,     # Sem tabelas
        with_code_formula=False,    # Sem fórmulas
        with_picture_classifier=False, # Sem imagens
        with_smolvlm=False,
        with_granite_vision=False,
        with_easyocr=False,         # Sem OCR
    )
    print("Download do modelo de layout concluído!")
