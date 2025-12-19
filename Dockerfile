# Dockerfile pour l'analyseur de code (CLI)
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

# Copier le code source
COPY src/ ./src/
COPY main.py .

# Créer les répertoires nécessaires
RUN mkdir -p input_data output

# Point d'entrée
ENTRYPOINT ["python", "main.py"]

# Par défaut, analyser un projet de démonstration
CMD ["https://github.com/ndleah/python-mini-project.git"]
