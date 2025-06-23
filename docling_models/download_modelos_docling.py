from docling.utils.model_downloader import download_models
from docling.models.layout_model import LayoutModel
from docling.models.utils.hf_model_download import snapshot_download
from docling.utils.model_downloader import download_models

# Baixa apenas o layout model
snapshot_download("ds4sd/docling-models", revision="v2.2.0", local_dir="./docling_models/layout_model")

download_models(models=["layout", "easyocr"])
