# 🔍 Code Dependency Analyzer

Outil d'analyse de dépendances pour projets Python.

## 📋 Description

Cet outil analyse les dépendances dans votre code Python, construit un graphe de dépendances et calcule des métriques pour identifier les points critiques de votre architecture.

## 🚀 Installation

```bash
pip install -r requirements.txt
```

## 💻 Utilisation

```bash
python main.py
```

## 📁 Structure du Projet

- `main.py` : Point d'entrée principal
- `src/` : Code source de l'analyseur
  - `parser.py` : Analyse le code source (AST)
  - `graph_builder.py` : Construit le graphe de dépendances (NetworkX)
  - `metrics.py` : Calcule les statistiques et métriques de centralité
  - `visualizer.py` : Génère les visualisations du graphe
- `input_data/` : Exemples de projets à analyser
  - `clean_project/` : Exemple de code bien structuré
  - `dirty_project/` : Exemple de code avec dépendances complexes

## 🎯 Fonctionnalités

- [x] Parsing de code Python avec AST
- [x] Construction de graphe de dépendances
- [x] Calcul de métriques (centralité, complexité)
- [x] Visualisation interactive

## 📊 Métriques Calculées

- Centralité de degré
- Centralité d'intermédiarité
- Dépendances circulaires
- Couplage entre modules

## 📝 Licence

MIT
