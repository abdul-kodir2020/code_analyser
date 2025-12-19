# 🐳 Guide Docker - Déploiement avec Docker Compose

Ce guide explique comment déployer l'analyseur de code avec Docker Compose.

## 📋 Prérequis

- Docker Engine 20.10+
- Docker Compose 2.0+

## 🚀 Démarrage rapide

### 1. Lancer tous les services

```bash
# Construire et démarrer le Web UI + Ollama
docker-compose up -d

# Voir les logs
docker-compose logs -f web-ui
```

Le Web UI sera accessible sur **http://localhost:5000**

### 2. Configuration de l'IA

Par défaut, Ollama est utilisé. Pour utiliser OpenAI ou Claude :

```bash
# Créer un fichier .env à la racine
cat > .env << EOF
OPENAI_API_KEY=sk-your-key-here
# OU
ANTHROPIC_API_KEY=sk-ant-your-key-here
EOF

# Redémarrer
docker-compose restart web-ui
```

### 3. Pré-charger un modèle Ollama

```bash
# Télécharger llama3.2
docker-compose exec ollama ollama pull llama3.2

# Vérifier les modèles disponibles
docker-compose exec ollama ollama list
```

## 📦 Services disponibles

### Web UI (Principal)
- **Port** : 5000
- **URL** : http://localhost:5000
- **Volumes** :
  - `./web_ui/data` : Base de données SQLite
  - `./web_ui/analyses` : Rapports générés
  - `./input_data` : Projets clonés

### Ollama (IA locale)
- **Port** : 11434
- **API** : http://localhost:11434
- **Volume** : `ollama-data` (modèles persistants)

### Analyzer CLI (Optionnel)
Pour analyser un projet directement :

```bash
# Analyser un dépôt GitHub
docker-compose run --rm analyzer-cli https://github.com/user/repo.git

# Les résultats seront dans ./output/
```

## 🔧 Commandes utiles

### Gestion des services

```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Reconstruire après modifications
docker-compose up -d --build

# Voir les logs
docker-compose logs -f web-ui
docker-compose logs -f ollama

# Redémarrer un service
docker-compose restart web-ui
```

### Gestion des données

```bash
# Sauvegarder la base de données
docker-compose exec web-ui cp /app/web_ui/data/analyses.db /app/web_ui/data/backup.db

# Nettoyer les analyses
docker-compose exec web-ui rm -rf /app/web_ui/analyses/*

# Nettoyer les projets clonés
rm -rf input_data/*
```

### Gestion d'Ollama

```bash
# Lister les modèles
docker-compose exec ollama ollama list

# Télécharger un modèle
docker-compose exec ollama ollama pull codellama:7b
docker-compose exec ollama ollama pull deepseek-coder:6.7b

# Supprimer un modèle
docker-compose exec ollama ollama rm llama3.2

# Tester un modèle
docker-compose exec ollama ollama run llama3.2 "Hello"
```

## 🌐 Variables d'environnement

Créez un fichier `.env` à la racine :

```bash
# Flask
FLASK_ENV=production

# IA - OpenAI
OPENAI_API_KEY=sk-your-key-here

# IA - Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# IA - Ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=180
```

## 📊 Monitoring

### Vérifier l'état des services

```bash
# Statut
docker-compose ps

# Ressources utilisées
docker stats code-analyzer-web code-analyzer-ollama

# Espace disque
docker system df
```

### Logs détaillés

```bash
# Web UI
docker-compose logs -f --tail=100 web-ui

# Ollama
docker-compose logs -f --tail=100 ollama

# Tous les services
docker-compose logs -f
```

## 🔒 Production

### Recommandations de sécurité

1. **Variables d'environnement** : Utilisez `.env` pour les secrets
2. **Réseau** : Utilisez un reverse proxy (nginx, traefik)
3. **Volumes** : Sauvegardez régulièrement `./web_ui/data`
4. **Mises à jour** : Reconstruisez régulièrement les images

### Exemple avec nginx

```yaml
# Ajouter dans docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./certs:/etc/nginx/certs
  depends_on:
    - web-ui
  networks:
    - code-analyzer-network
```

## 🐛 Dépannage

### Le Web UI ne démarre pas

```bash
# Voir les logs
docker-compose logs web-ui

# Vérifier les permissions
ls -la web_ui/data/

# Reconstruire
docker-compose up -d --build web-ui
```

### Ollama ne répond pas

```bash
# Vérifier qu'il tourne
docker-compose ps ollama

# Tester l'API
curl http://localhost:11434/api/tags

# Voir les logs
docker-compose logs ollama

# Redémarrer
docker-compose restart ollama
```

### Manque d'espace disque

```bash
# Nettoyer les images non utilisées
docker system prune -a

# Nettoyer les volumes non utilisés
docker volume prune

# Voir l'utilisation
docker system df -v
```

## 🔄 Mise à jour

```bash
# Récupérer les dernières modifications
git pull

# Reconstruire et redémarrer
docker-compose down
docker-compose up -d --build

# Vérifier
docker-compose ps
docker-compose logs -f web-ui
```

## 📈 Scaling (optionnel)

Pour gérer plus de charge :

```bash
# Lancer plusieurs instances du Web UI
docker-compose up -d --scale web-ui=3

# Ajouter un load balancer (nginx, haproxy)
```

## 🎯 Modes d'utilisation

### Mode Développement

```bash
# Utiliser des volumes bindés pour le code
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Mode CLI uniquement

```bash
# Désactiver le Web UI, utiliser seulement le CLI
docker-compose run --rm analyzer-cli https://github.com/user/repo.git
```

### Mode sans Ollama

```bash
# Si vous utilisez OpenAI/Claude
docker-compose up -d web-ui
# (ne pas démarrer ollama)
```

## 📞 Support

Pour plus d'informations :
- Consultez `README.md`
- Vérifiez `OLLAMA_DOCKER_SETUP.md` pour Ollama
- Vérifiez `AI_ADVISOR_GUIDE.md` pour l'IA
