# Interface Web - Code Analyzer

## Démarrage Rapide

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'interface web
cd web_ui
python app.py
```

Accédez à : **http://localhost:5000**

## Fonctionnalités

### ✅ Actuellement Disponibles

- **Nouvelle Analyse** : Interface pour entrer une URL Git et lancer l'analyse
- **Historique** : Voir toutes les analyses passées et en cours
- **Détails d'Analyse** : Consulter les résultats complets
- **Stockage Persistant** : Base de données SQLite pour conserver l'historique
- **Exécution Asynchrone** : Les analyses tournent en arrière-plan
- **Gestion** : Supprimer les analyses inutiles

### 🚀 À Venir

- Comparaison entre 2 analyses
- Filtres et recherche dans l'historique
- Export des résultats (JSON, CSV, PDF)
- API REST documentée
- Authentification utilisateur
- Notifications en temps réel (WebSocket)

## Structure

```
web_ui/
├── app.py                 # Application Flask
├── templates/             # Pages HTML
│   ├── index.html        # Page d'accueil
│   ├── history.html      # Historique
│   └── analysis.html     # Détails d'une analyse
├── static/
│   └── style.css         # Styles CSS
└── web_reports/          # Rapports générés (auto-créé)
```

## Base de Données

SQLite (`analyses.db`) avec table :
- `id` : ID unique
- `project_name` : Nom du projet
- `repo_url` : URL Git
- `status` : pending/running/completed/failed
- `created_at` / `completed_at` : Timestamps
- `total_modules` / `total_dependencies` : Métriques
- `vulnerabilities_*` : Compteurs de sécurité
- `report_path` : Chemin du rapport HTML
