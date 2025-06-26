from docling.utils.model_downloader import download_models
from pathlib import Path

if __name__ == "__main__":
    print("Baixando os modelos necessários para o Docling (layout, tableformer, easyocr etc.)...")
    download_models(
        output_dir=Path(r'C:\Users\Joao\Documents\GitHub\cv_ai\docling_models'),
        force=False,
        progress=True,
        with_layout=True,
        with_tableformer=True,
        with_code_formula=True,
        with_picture_classifier=True,
        with_smolvlm=False,
        with_granite_vision=False,
        with_easyocr=True,
    )
    print("Download dos modelos concluído!")
