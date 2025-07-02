FROM python:3.11-slim

WORKDIR /app

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'app
COPY . .

# Exposer le port Streamlit
EXPOSE 8501

# Variables d'environnement pour Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Lancer Streamlit
CMD ["streamlit", "run", "test.py", "--server.port=8501", "--server.address=0.0.0.0"]