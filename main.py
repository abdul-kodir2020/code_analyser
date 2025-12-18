#!/usr/bin/env python3
"""
Code Dependency Analyzer - Point d'entrée principal
Orchestre l'analyse des dépendances de code Python
"""

from src.parser import CodeParser
from src.graph_builder import GraphBuilder
from src.metrics import MetricsCalculator
from src.visualizer import GraphVisualizer
from src.git_manager import GitManager
from src.html_reporter import HTMLReporter
from src.security_analyzer import SecurityAnalyzer
from src.attack_surface import AttackSurfaceAnalyzer


def main():
    """Point d'entrée principal de l'application"""
    print("🔍 Analyseur de Dépendances de Code")
    print("=" * 50)
    print()
    
    # === ÉTAPE 1 : Cloner le dépôt Git ===
    print("📥 ÉTAPE 1/4 : Clonage du dépôt")
    print("-" * 50)
    git_manager = GitManager("input_data")
    project_path = git_manager.clone_repository("https://github.com/ndleah/python-mini-project.git")
    # project_path = git_manager.clone_repository("https://github.com/aymen1meziane/spagetti-projet.git")
    print()
    
    # === ÉTAPE 2 : Parser le code ===
    print("🔍 ÉTAPE 2/4 : Analyse du code source (AST)")
    print("-" * 50)
    parser = CodeParser(str(project_path))
    dependencies = parser.parse_project()
    external_deps = parser.get_all_external_dependencies()
    print(f"✅ {len(dependencies)} fichiers Python analysés")
    print(f"📄 Fichiers trouvés : {list(dependencies.keys())[:5]}{'...' if len(dependencies) > 5 else ''}")
    print()
    
    # === ÉTAPE 3 : Construire le graphe ===
    print("🕸️  ÉTAPE 3/4 : Construction du graphe de dépendances")
    print("-" * 50)
    graph_builder = GraphBuilder()
    graph = graph_builder.build_graph(dependencies)
    graph_info = graph_builder.get_graph_info()
    
    print(f"✅ Graphe construit")
    print(f"   • Nœuds (modules) : {graph_info['nodes']}")
    print(f"   • Arêtes (dépendances) : {graph_info['edges']}")
    print(f"   • DAG (pas de cycles) : {graph_info['is_dag']}")
    print(f"   • Cycles détectés : {graph_info['cycles']}")
    
    if not graph_info['is_dag']:
        cycles = graph_builder.detect_cycles()
        print(f"\n⚠️  ALERTE : Dépendances circulaires détectées !")
        for i, cycle in enumerate(cycles[:3], 1):
            print(f"   Cycle {i}: {' → '.join(cycle)} → {cycle[0]}")
    print()
    
    # === ANALYSE DE SÉCURITÉ ===
    print("🔒 Analyse de sécurité")
    print("-" * 50)
    security = SecurityAnalyzer()
    
    # Analyser chaque fichier
    python_files = list(project_path.rglob("*.py"))
    for file_path in python_files:
        module_name = str(file_path.relative_to(project_path))
        security.analyze_file(file_path, module_name)
    
    security_summary = security.get_summary()
    print(f"✅ Analyse de sécurité terminée")
    print(f"   ⚠️  {security_summary['total']} vulnérabilités potentielles détectées")
    print(f"      🔴 Critiques: {security_summary['by_severity']['CRITIQUE']}")
    print(f"      🟠 Élevées: {security_summary['by_severity']['ÉLEVÉ']}")
    print(f"      🟡 Moyennes: {security_summary['by_severity']['MOYEN']}")
    print()
    
    # === ANALYSE DE SURFACE D'ATTAQUE ===
    print("🎯 Analyse de surface d'attaque")
    print("-" * 50)
    attack_surface = AttackSurfaceAnalyzer(graph)
    
    # Analyser chaque fichier pour les points d'entrée
    for file_path in python_files:
        module_name = str(file_path.relative_to(project_path))
        attack_surface.analyze_file(file_path, module_name)
    print()
    
    # === ÉTAPE 4 : Calculer les métriques ===
    print("📊 ÉTAPE 4/4 : Calcul des métriques")
    print("-" * 50)
    metrics_calc = MetricsCalculator(graph)
    metrics = metrics_calc.calculate_all_metrics()
    
    print("✅ Métriques calculées\n")
    
    # Top 5 modules par centralité
    print("🏆 Top 5 - Centralité de degré (modules les plus connectés)")
    top_degree = metrics_calc.get_top_modules("degree_centrality", 5)
    for i, (module, score) in enumerate(top_degree, 1):
        print(f"   {i}. {module}: {score:.3f}")
    
    print("\n🔗 Top 5 - Modules les plus dépendants (degré entrant)")
    top_in = metrics_calc.get_top_modules("in_degree", 5)
    for i, (module, count) in enumerate(top_in, 1):
        print(f"   {i}. {module}: {count} dépendants")
    
    print("\n📤 Top 5 - Modules avec le plus de dépendances (degré sortant)")
    top_out = metrics_calc.get_top_modules("out_degree", 5)
    for i, (module, count) in enumerate(top_out, 1):
        print(f"   {i}. {module}: {count} dépendances")
    print()
    
    # === CALCUL DE LA SURFACE D'ATTAQUE ===
    print("🎯 Calcul de la surface d'attaque")
    print("-" * 50)
    attack_surface.calculate_attack_surface(metrics)
    surface_summary = attack_surface.get_summary()
    
    print(f"✅ Surface d'attaque calculée")
    print(f"   🌐 Points d'entrée détectés : {surface_summary['total_entry_points']}")
    print(f"   📍 Modules exposés : {surface_summary['entry_modules']}")
    print(f"   ⚠️  Chemins critiques : {surface_summary['critical_paths']}")
    if surface_summary['critical_paths'] > 0:
        print(f"      🔴 Risque CRITIQUE : {surface_summary['by_risk']['CRITIQUE']}")
        print(f"      🟠 Risque ÉLEVÉ : {surface_summary['by_risk']['ÉLEVÉ']}")
    print()
    
    # === VISUALISATION ===
    print("🎨 Génération des visualisations")
    print("-" * 50)
    visualizer = GraphVisualizer(graph)
    
    # Graphes statiques (PNG)
    visualizer.draw_simple("output_graph_simple.png")
    visualizer.draw_with_metrics(metrics, "output_graph_metrics.png")
    
    # Graphe interactif (HTML) avec sécurité
    interactive_graph = visualizer.draw_interactive(metrics, "graph_interactive.html", security)
    
    print()
    
    # === RAPPORT HTML ===
    print()
    print("📄 Génération du rapport HTML")
    print("-" * 50)
    
    # Extraire le nom du projet depuis le path
    project_name = str(project_path).split('/')[-1]
    
    html_reporter = HTMLReporter(graph, metrics, graph_info, project_name, external_deps, security, attack_surface)
    html_file = html_reporter.generate_report(
        "report.html",
        "output_graph_simple.png",
        "output_graph_metrics.png",
        "graph_interactive.html"
    )
    
    print()
    print("=" * 50)
    print("✅ Analyse terminée avec succès !")
    print("📁 Fichiers générés :")
    print("   • output_graph_simple.png")
    print("   • output_graph_metrics.png")
    print(f"   • graph_interactive.html (🎮 INTERACTIF)")
    print(f"   • {html_file}")
    print()
    print(f"🌐 Ouvrez {html_file} dans votre navigateur !")
    print(f"🎮 Ou explorez le graphe interactif : graph_interactive.html")
    print("=" * 50)


if __name__ == "__main__":
    main()
