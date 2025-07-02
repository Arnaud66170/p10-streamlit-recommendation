# streamlit_app/config.py

import os
from dotenv import load_dotenv

# === Definir le chemin absolu vers la racine du projet
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# === Chemin complet vers .env.prod a la racine
env_file = os.path.join(PROJECT_ROOT, ".env.prod")
load_dotenv(dotenv_path=env_file)

# === Variables d'environnement lues
_raw_url = os.getenv("AZURE_FUNCTION_URL")
_key = os.getenv("AZURE_FUNCTION_KEY")
AZURE_FUNCTION_URL = f"{_raw_url}?code={_key}"

# DEFAULT_DATA_SOURCE = os.getenv("DATA_SOURCE", "azure").lower()
# VALID_SOURCES = ["local", "azure"]
VALID_SOURCES = ["azure"]
DEFAULT_DATA_SOURCE = "azure"

# === Debug : impression de confirmation
print("[config.py] Chargement depuis :", env_file)
print("[config.py] AZURE_CONN_STR =", os.getenv("AZURE_CONN_STR"))
print("[config.py] AZURE_FUNCTION_URL =", AZURE_FUNCTION_URL)