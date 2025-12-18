#!/bin/bash

# Script de démarrage de l'interface web

echo "🚀 Démarrage de Code Analyzer Web UI..."
echo ""

# Vérifier que Flask est installé
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installation de Flask..."
    pip install flask
fi

# Créer le dossier pour les rapports
mkdir -p web_reports

# Lancer l'application
echo ""
echo "✅ Serveur prêt!"
echo "📊 Accédez à: http://localhost:5000"
echo ""

cd web_ui
python3 app.py
