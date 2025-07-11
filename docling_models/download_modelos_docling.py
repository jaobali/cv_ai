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

# precisei executar isso aqui no terminal pq o tamanho do arquivo do modelo é maior que os 100Mb suportado nativamente pelo github
# git lfs install
# git lfs track "*.safetensors"
# git add .gitattributes
# git add docling_models/ds4sd--docling-models/model_artifacts/layout/model.safetensors
# git commit -m "Adiciona modelo layout safetensors via LFS"
# git push