#!/bin/bash
# Script pour initialiser Ollama et précharger le modèle

echo "⏳ Attente du démarrage d'Ollama..."
sleep 5

# Attendre que le service Ollama soit prêt
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "⏳ Ollama n'est pas encore prêt, nouvelle tentative dans 2s..."
    sleep 2
done

echo "✅ Ollama est prêt!"

# Vérifier si le modèle est déjà installé
if ollama list | grep -q "llama3.2"; then
    echo "✅ Le modèle llama3.2 est déjà installé"
else
    echo "📥 Téléchargement du modèle llama3.2..."
    ollama pull llama3.2
    echo "✅ Modèle llama3.2 installé avec succès!"
fi

echo "🎉 Initialisation terminée!"
