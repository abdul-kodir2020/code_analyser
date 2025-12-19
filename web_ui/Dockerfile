# Dockerfile pour le Web UI Flask
FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    git \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code source (nécessaire pour les imports)
COPY src/ ./src/
COPY main.py .
COPY web_ui/ ./web_ui/

# Créer les répertoires nécessaires
RUN mkdir -p input_data web_ui/data web_ui/analyses

WORKDIR /app/web_ui

# Exposer le port Flask
EXPOSE 5000

# Variables d'environnement par défaut
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Lancer le serveur Flask
CMD ["python", "app.py"]
