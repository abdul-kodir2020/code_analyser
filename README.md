# Code Dependency Analyzer

Outil d'analyse de dépendances pour projets Python avec détection de vulnérabilités de sécurité.

## Description

Cet outil analyse les dépendances dans votre code Python, construit un graphe de dépendances, calcule des métriques pour identifier les points critiques de votre architecture, **détecte automatiquement les vulnérabilités de sécurité**, et **cartographie la surface d'attaque** en identifiant les chemins critiques accessibles depuis l'extérieur.

## Fonctionnalités

### Analyse de Code
- Parsing AST : Analyse complète du code source Python
- Graphe de dépendances : Visualisation des relations entre modules
- Détection de cycles : Identification des dépendances circulaires
- Dépendances externes : Tracking des bibliothèques tierces

### Métriques Avancées
- Centralité de degré : Modules les plus connectés
- Centralité d'intermédiarité : Modules "pont" critiques
- Degré entrant/sortant : Analyse du couplage
- Détection de complexité : Identification des points chauds

### 🔒 Analyse de Sécurité
- **Fonctions dangereuses** : Détection de `eval()`, `exec()`, `pickle.loads()`
- **Injection SQL** : Détection de formatage de chaîne dans les requêtes
- **Injection de commandes** : Détection de `subprocess` avec `shell=True`
- **Modules à risque** : Identification automatique des fichiers vulnérables
- **Rapport de sécurité** : Statistiques par sévérité (Critique, Élevé, Moyen)

### 🎯 Attack Surface Mapping
- **Détection automatique des points d'entrée** : Routes HTTP, API endpoints (Flask, FastAPI, Django)
- **Calcul des distances** : Nombre de sauts depuis l'extérieur vers les modules critiques
- **Évaluation des risques** : Classification CRITIQUE/ÉLEVÉ/MOYEN/FAIBLE
- **Chemins d'attaque** : Identification des routes exposant des fonctions dangereuses
- **Visualisation** : Tableau interactif des risques avec color-coding

### Visualisations
- **Graphes PNG** : Images statiques haute résolution
- **Graphe interactif** : PyVis avec zoom, drag & drop, hover
- **Coloration de sécurité** : Modules dangereux en rouge
- **Rapport HTML** : Dashboard complet avec toutes les métriques

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### Analyse rapide

```bash
python main.py
```

Par défaut, l'outil clone et analyse le projet configuré dans `main.py`.

### Personnalisation

Modifiez l'URL du repository dans `main.py` :

```python
project_path = git_manager.clone_repository("https://github.com/user/projet.git")
```

### Résultats

L'analyse génère automatiquement :
- `output_graph_simple.png` - Graphe simple
- `output_graph_metrics.png` - Graphe avec métriques
- `graph_interactive.html` - Graphe interactif (RECOMMANDÉ)
- `report.html` - Rapport complet

**Ouvrez `report.html` dans votre navigateur pour voir tous les résultats.**

## Structure du Projet

```
code_dependency_analyzer/
├── main.py                 # Point d'entrée principal
├── requirements.txt        # Dépendances
├── README.md              # Documentation
│
├── src/                   # Code source
│   ├── __init__.py
│   ├── parser.py          # Analyse AST
│   ├── graph_builder.py   # Construction du graphe
│   ├── metrics.py         # Calcul des métriques
│   ├── visualizer.py      # Génération des graphes
│   ├── git_manager.py     # Clonage automatique
│   ├── security_analyzer.py    # Analyse de sécurité
│   ├── attack_surface.py       # Attack Surface Mapping
│   ├── attack_surface_html.py  # Génération HTML surface d'attaque
│   └── html_reporter.py        # Génération du rapport
│
└── input_data/            # Projets clonés (auto)
```

## Vulnérabilités Détectées

### Niveau CRITIQUE
- `eval()` / `exec()` - Exécution de code arbitraire
- `pickle.loads()` - Désérialisation non sécurisée
- `yaml.load()` - YAML deserialization (utilisez `safe_load`)
- `os.system()` / `os.popen()` - Injection de commandes
- SQL avec formatage de chaînes - Injection SQL

### Niveau ÉLEVÉ
- `subprocess` avec `shell=True` - Injection de commandes
- `__import__()` - Import dynamique non contrôlé
- `compile()` - Compilation de code dynamique
- Imports de modules dangereux (`pickle`, `marshal`, `shelve`)

### Niveau MOYEN
- `input()` - Entrée utilisateur non validée

## Métriques Calculées

| Métrique | Description | Usage |
|----------|-------------|-------|
| **Centralité de degré** | Modules les plus connectés | Identifier les hubs |
| **Centralité d'intermédiarité** | Modules "pont" critiques | Points de défaillance |
| **Degré entrant** | Nombre de dépendants | Modules critiques |
| **Degré sortant** | Nombre de dépendances | Couplage fort |
| **Cycles** | Dépendances circulaires | Problèmes d'architecture |

## Cas d'Usage

### 1. Audit de Sécurité
Identifiez rapidement les fonctions dangereuses dans un projet :
```bash
python main.py
# Ouvrez report.html → Section "Analyse de Sécurité"
```

### 2. Refactoring
Trouvez les modules trop couplés :
```bash
# Cherchez les modules avec degré élevé dans le rapport
```

### 3. Code Review
Visualisez les dépendances avant une PR :
```bash
# Ouvrez graph_interactive.html pour explorer
```

### 4. Documentation
Générez automatiquement l'architecture :
```bash
# Utilisez les graphes PNG pour la documentation
```

### 5. Analyse de Surface d'Attaque
Identifiez les endpoints exposant des modules critiques :
```bash
python main.py /path/to/web/app
# Ouvrez report.html → Section "Attack Surface Mapping"
# Voir les routes avec risque CRITIQUE
```

## Graphe Interactif

Le graphe interactif (`graph_interactive.html`) offre :
- **Zoom et Pan** : Navigation fluide
- **Drag & Drop** : Réorganisez les nœuds
- **Hover** : Métriques détaillées au survol
- **Coloration** : Modules dangereux en rouge vif
- **Physique** : Organisation automatique intelligente

## Exemple de Sortie

> **Note** : Les valeurs ci-dessous sont des exemples génériques. Les métriques réelles (nombre de fichiers, modules, vulnérabilités, etc.) dépendent du projet analysé.

```
Analyseur de Dépendances de Code
==================================================

ÉTAPE 1/4 : Clonage du dépôt
--------------------------------------------------
✅ Dépôt cloné : input_data/<nom-du-projet>

ÉTAPE 2/4 : Analyse du code source (AST)
--------------------------------------------------
✅ X fichiers Python analysés
   Dépendances externes uniques : N

Analyse de sécurité
--------------------------------------------------
✅ Analyse de sécurité terminée
   ⚠️  Y vulnérabilités potentielles détectées
      Critiques: A
      Élevées: B
      Moyennes: C

Analyse de surface d'attaque
--------------------------------------------------
✅ Surface d'attaque calculée
   🌐 Points d'entrée détectés : P
   📍 Modules exposés : M
   ⚠️  Chemins critiques : K
      Risque CRITIQUE : ...
      Risque ÉLEVÉ : ...

ÉTAPE 3/4 : Construction du graphe
--------------------------------------------------
✅ Graphe construit avec succès
   • Nœuds (modules) : X
   • Arêtes (dépendances) : Y
   • Est un DAG : ✅ Oui / ❌ Non
   • Cycles détectés : Z

ÉTAPE 4/4 : Calcul des métriques
--------------------------------------------------
✅ Métriques calculées

Génération des visualisations
--------------------------------------------------
✅ Graphe sauvegardé : output_graph_simple.png
✅ Graphe avec métriques : output_graph_metrics.png
✅ Graphe interactif : graph_interactive.html

Génération du rapport HTML
--------------------------------------------------
✅ Rapport HTML généré : report.html

==================================================
✅ Analyse terminée avec succès !
Fichiers générés :
   • output_graph_simple.png
   • output_graph_metrics.png
   • graph_interactive.html (INTERACTIF)
   • report.html

Ouvrez report.html dans votre navigateur !
==================================================
```

## Technologies Utilisées

- **NetworkX** - Graphes et métriques
- **Matplotlib** - Visualisations statiques
- **PyVis** - Graphes interactifs
- **AST** - Parsing du code Python
- **Git** - Clonage automatique de repos

## Licence

MIT

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une PR.