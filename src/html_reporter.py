"""
Générateur de rapport HTML avec système d'onglets
Crée une page web dashboard interactive
"""

import networkx as nx
import json
import os
from datetime import datetime
from pathlib import Path
from src.attack_surface_html import generate_attack_surface_section


class HTMLReporter:
    """Génère un rapport HTML complet en mode dashboard avec onglets"""
    
    def __init__(self, graph: nx.DiGraph, metrics: dict, graph_info: dict, project_name: str, external_deps: set = None, security=None, attack_surface=None, project_path=None):
        self.graph = graph
        self.metrics = metrics
        self.graph_info = graph_info
        self.project_name = project_name
        self.external_deps = external_deps or set()
        self.security = security
        self.attack_surface = attack_surface
        self.project_path = Path(project_path) if project_path else None
        
        # Créer un mapping module_name -> file_path pour extraction de code
        self.module_to_file = {}
        for node_name, data in self.graph.nodes(data=True):
            if 'file' in data:
                self.module_to_file[node_name] = data['file']
        
        # Cache pour éviter de relire les mêmes fichiers
        self._file_cache = {}
    
    def generate_report(self, output_file: str = "report.html", 
                       img_simple: str = "output_graph_simple.png",
                       img_metrics: str = "output_graph_metrics.png",
                       interactive_graph: str = "graph_interactive.html"):
        html_content = self._generate_dashboard_html(img_simple, img_metrics, interactive_graph)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Rapport HTML généré : {output_file}")
        return output_file
    
    def _generate_dashboard_html(self, img_simple, img_metrics, interactive_graph):
        """Génère le HTML avec système d'onglets"""
        
        # Préparer les données
        security_summary = self.security.get_summary() if self.security else None
        attack_summary = self.attack_surface.get_summary() if self.attack_surface and self.attack_surface.entry_points else None
        
        # Générer les sections
        overview_tab = self._generate_overview_tab(security_summary, attack_summary)
        metrics_tab = self._generate_metrics_tab()
        security_tab = self._generate_security_tab() if self.security else ""
        attack_tab = self._generate_attack_surface_tab() if attack_summary else ""
        deps_tab = self._generate_dependencies_tab()
        graphs_tab = self._generate_graphs_tab(img_simple, img_metrics, interactive_graph)
        ai_tab = self._generate_ai_suggestions_tab() if self.security else ""
        
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - {self.project_name}</title>
    {self._get_styles()}
</head>
<body>
    <div class="dashboard">
        <nav class="sidebar">
            <div class="sidebar-header">
                <h1>📊 Code Analyzer</h1>
                <p>{self.project_name}</p>
                <small>{datetime.now().strftime('%d/%m/%Y %H:%M')}</small>
            </div>
            <div class="nav-tabs">
                <div class="nav-tab active" data-tab="overview">
                    <span class="nav-tab-icon">🏠</span>
                    <span>Vue d'ensemble</span>
                </div>
                <div class="nav-tab" data-tab="metrics">
                    <span class="nav-tab-icon">📈</span>
                    <span>Métriques</span>
                </div>
                {f'''<div class="nav-tab" data-tab="security">
                    <span class="nav-tab-icon">🔒</span>
                    <span>Sécurité</span>
                </div>''' if self.security else ''}
                {f'''<div class="nav-tab" data-tab="attack-surface">
                    <span class="nav-tab-icon">🎯</span>
                    <span>Attack Surface</span>
                </div>''' if attack_summary else ''}
                {f'''<div class="nav-tab" data-tab="ai-suggestions">
                    <span class="nav-tab-icon">🤖</span>
                    <span>Suggestions IA</span>
                </div>''' if self.security else ''}
                <div class="nav-tab" data-tab="dependencies">
                    <span class="nav-tab-icon">🔗</span>
                    <span>Dépendances</span>
                </div>
                <div class="nav-tab" data-tab="graphs">
                    <span class="nav-tab-icon">🌐</span>
                    <span>Visualisations</span>
                </div>
            </div>
        </nav>
        
        <main class="main-content">
            <div id="overview" class="tab-content active">
                {overview_tab}
            </div>
            
            <div id="metrics" class="tab-content">
                {metrics_tab}
            </div>
            
            {f'<div id="security" class="tab-content">{security_tab}</div>' if self.security else ''}
            
            {f'<div id="attack-surface" class="tab-content">{attack_tab}</div>' if attack_summary else ''}
            
            {f'<div id="ai-suggestions" class="tab-content">{ai_tab}</div>' if self.security else ''}
            
            <div id="dependencies" class="tab-content">
                {deps_tab}
            </div>
            
            <div id="graphs" class="tab-content">
                {graphs_tab}
            </div>
        </main>
    </div>
    
    <button id="themeToggle" onclick="toggleTheme()">🌙 Mode Sombre</button>
    
    {self._get_javascript()}
</body>
</html>"""

    def _get_styles(self):
        """Retourne le CSS complet"""
        return """<style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg: #f5f7fa;
            --text: #333;
            --card-bg: white;
            --border: #e2e8f0;
            --sidebar-bg-start: #1e3a8a;
            --sidebar-bg-end: #312e81;
        }
        
        body.dark-theme {
            --bg: #1a1a1a;
            --text: #e0e0e0;
            --card-bg: #2d2d2d;
            --border: #404040;
            --sidebar-bg-start: #0f1729;
            --sidebar-bg-end: #1a1540;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            transition: background-color 0.3s, color 0.3s;
        }
        
        .dashboard {
            display: flex;
            min-height: 100vh;
        }
        
        /* Sidebar */
        .sidebar {
            width: 280px;
            background: linear-gradient(180deg, var(--sidebar-bg-start) 0%, var(--sidebar-bg-end) 100%);
            color: white;
            padding: 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            box-shadow: 4px 0 10px rgba(0,0,0,0.1);
        }
        
        .sidebar-header {
            padding: 30px 20px;
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .sidebar-header h1 {
            font-size: 1.3em;
            margin-bottom: 5px;
            font-weight: 600;
        }
        
        .sidebar-header p {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 5px;
        }
        
        .sidebar-header small {
            font-size: 0.75em;
            opacity: 0.6;
        }
        
        .nav-tabs {
            padding: 20px 0;
        }
        
        .nav-tab {
            display: flex;
            align-items: center;
            padding: 15px 25px;
            color: rgba(255,255,255,0.7);
            cursor: pointer;
            transition: all 0.3s;
            border-left: 3px solid transparent;
        }
        
        .nav-tab:hover {
            background: rgba(255,255,255,0.1);
            color: white;
        }
        
        .nav-tab.active {
            background: rgba(255,255,255,0.15);
            color: white;
            border-left-color: #60a5fa;
            font-weight: 600;
        }
        
        .nav-tab-icon {
            font-size: 1.3em;
            margin-right: 12px;
            min-width: 25px;
        }
        
        /* Main Content */
        .main-content {
            flex: 1;
            margin-left: 280px;
            padding: 30px;
        }
        
        .tab-content {
            display: none;
            animation: fadeIn 0.3s;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: var(--card-bg);
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #667eea;
            transition: transform 0.2s, background-color 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.12);
        }
        
        .stat-card h3 {
            font-size: 0.85em;
            color: var(--text);
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #1e293b;
        }
        
        .stat-card.success { border-left-color: #10b981; }
        .stat-card.success .value { color: #10b981; }
        
        .stat-card.warning { border-left-color: #f59e0b; }
        .stat-card.warning .value { color: #f59e0b; }
        
        .stat-card.danger { border-left-color: #ef4444; }
        .stat-card.danger .value { color: #ef4444; }
        
        .stat-card.info { border-left-color: #3b82f6; }
        .stat-card.info .value { color: #3b82f6; }
        
        /* Section Card */
        .section-card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: background-color 0.3s;
        }
        
        .section-card h2 {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: var(--text);
            border-bottom: 2px solid var(--border);
            padding-bottom: 15px;
        }
        
        /* Bouton toggle thème */
        #themeToggle {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 1000;
            padding: 12px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transition: all 0.3s;
        }
        
        #themeToggle:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5);
        }
        
        body.dark-theme #themeToggle {
            background: linear-gradient(135deg, #4a5dc9 0%, #5a3a7a 100%);
        }
        
        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
        }
        
        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        th {
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
            color: var(--text);
        }
        
        tr:hover {
            background: rgba(0,0,0,0.02);
        }
        
        body.dark-theme tr:hover {
            background: rgba(255,255,255,0.05);
        }
        
        /* Badges */
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge-danger { background: #fee2e2; color: #dc2626; }
        .badge-warning { background: #fef3c7; color: #d97706; }
        .badge-info { background: #dbeafe; color: #2563eb; }
        .badge-success { background: #d1fae5; color: #059669; }
        
        /* Alert */
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid;
        }
        
        .alert-danger { background: #fef2f2; border-left-color: #dc2626; color: #991b1b; }
        .alert-warning { background: #fffbeb; border-left-color: #f59e0b; color: #92400e; }
        .alert-info { background: #eff6ff; border-left-color: #3b82f6; color: #1e40af; }
        
        /* Graph Container */
        .graph-container {
            text-align: center;
            margin: 30px 0;
        }
        
        .graph-container img {
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        
        .interactive-link {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        
        .interactive-link:hover {
            transform: scale(1.05);
        }
        
        /* AI Suggestions */
        .ai-suggestion-card {
            background: var(--card-bg);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .ai-vulnerability-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--border);
        }
        
        .ai-vulnerability-title {
            font-size: 1.1em;
            font-weight: bold;
            color: var(--text);
        }
        
        .ai-severity-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .ai-severity-CRITIQUE {
            background: #fee2e2;
            color: #dc2626;
        }
        
        .ai-severity-ÉLEVÉ {
            background: #fef3c7;
            color: #d97706;
        }
        
        .ai-severity-MOYEN {
            background: #dbeafe;
            color: #2563eb;
        }
        
        .ai-suggestion-section {
            margin: 15px 0;
        }
        
        .ai-suggestion-section h4 {
            font-size: 1em;
            margin-bottom: 10px;
            color: var(--text);
        }
        
        .ai-code-block {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
        }
        
        body.dark-theme .ai-code-block {
            background: #0d0d0d;
        }
        
        .ai-steps-list {
            list-style: none;
            padding: 0;
        }
        
        .ai-steps-list li {
            padding: 10px 15px;
            margin: 8px 0;
            background: rgba(102, 126, 234, 0.1);
            border-left: 3px solid #667eea;
            border-radius: 4px;
        }
        
        .ai-copy-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            margin-top: 10px;
            transition: transform 0.2s;
        }
        
        .ai-copy-btn:hover {
            transform: translateY(-2px);
        }
        
        .spinner {
            border: 4px solid rgba(102, 126, 234, 0.3);
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                width: 100%;
                position: relative;
                height: auto;
            }
            
            .main-content {
                margin-left: 0;
                padding: 15px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>"""

    def _get_javascript(self):
        """Retourne le JavaScript pour les onglets"""
        return """<script>
        function showTab(tabId) {
            // Cacher tous les onglets
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Retirer active de tous les nav-tabs
            document.querySelectorAll('.nav-tab').forEach(nav => {
                nav.classList.remove('active');
            });
            
            // Afficher l'onglet sélectionné
            const selectedTab = document.getElementById(tabId);
            if (selectedTab) {
                selectedTab.classList.add('active');
            }
            
            // Activer le nav-tab correspondant
            const selectedNav = document.querySelector('[data-tab="' + tabId + '"]');
            if (selectedNav) {
                selectedNav.classList.add('active');
            }
        }
        
        // Toggle de thème
        function toggleTheme() {
            const body = document.body;
            const button = document.getElementById('themeToggle');
            
            body.classList.toggle('dark-theme');
            
            if (body.classList.contains('dark-theme')) {
                button.innerHTML = '☀️ Mode Clair';
                localStorage.setItem('theme', 'dark');
            } else {
                button.innerHTML = '🌙 Mode Sombre';
                localStorage.setItem('theme', 'light');
            }
        }
        
        // Initialisation au chargement de la page
        window.addEventListener('DOMContentLoaded', function() {
            // Gestionnaire de clics sur les nav-tabs
            document.querySelectorAll('.nav-tab').forEach(function(tab) {
                tab.addEventListener('click', function() {
                    const tabId = this.getAttribute('data-tab');
                    showTab(tabId);
                });
            });
            
            // Charger le thème sauvegardé
            const savedTheme = localStorage.getItem('theme');
            const button = document.getElementById('themeToggle');
            
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-theme');
                if (button) {
                    button.innerHTML = '☀️ Mode Clair';
                }
            }
        });
    </script>"""

    def _generate_overview_tab(self, security_summary, attack_summary):
        """Génère l'onglet vue d'ensemble"""
        security_cards = ""
        if security_summary:
            security_cards = f"""
            <div class="stat-card danger">
                <h3>Vuln. Critiques</h3>
                <div class="value">{security_summary['by_severity']['CRITIQUE']}</div>
            </div>
            <div class="stat-card warning">
                <h3>Vuln. Élevées</h3>
                <div class="value">{security_summary['by_severity']['ÉLEVÉ']}</div>
            </div>"""
        
        attack_cards = ""
        if attack_summary:
            attack_cards = f"""
            <div class="stat-card info">
                <h3>Points d'Entrée</h3>
                <div class="value">{attack_summary['total_entry_points']}</div>
            </div>
            <div class="stat-card danger">
                <h3>Chemins Critiques</h3>
                <div class="value">{attack_summary['critical_paths']}</div>
            </div>"""
        
        is_dag_text = "✅ Oui" if self.graph_info['is_dag'] else "❌ Non"
        
        return f"""
        <div class="stats-grid">
            <div class="stat-card info">
                <h3>Modules</h3>
                <div class="value">{self.graph_info['nodes']}</div>
            </div>
            <div class="stat-card success">
                <h3>Dépendances</h3>
                <div class="value">{self.graph_info['edges']}</div>
            </div>
            <div class="stat-card {'success' if self.graph_info['is_dag'] else 'warning'}">
                <h3>DAG (Sans Cycles)</h3>
                <div class="value" style="font-size: 1.5em;">{is_dag_text}</div>
            </div>
            <div class="stat-card warning">
                <h3>Dép. Externes</h3>
                <div class="value">{len(self.external_deps)}</div>
            </div>
            {security_cards}
            {attack_cards}
        </div>
        
        <div class="section-card">
            <h2>📊 Résumé de l'Analyse</h2>
            <p style="color: #64748b; line-height: 1.8;">
                Ce projet contient <strong>{self.graph_info['nodes']} modules</strong> avec 
                <strong>{self.graph_info['edges']} dépendances</strong>. 
                {'Le graphe est acyclique (DAG), ce qui indique une bonne architecture sans dépendances circulaires.' if self.graph_info['is_dag'] else 
                 f"<span style='color: #dc2626;'>⚠️ Attention : {self.graph_info['cycles']} cycle(s) de dépendances détecté(s).</span>"}
            </p>
        </div>
        """
    
    def _generate_metrics_tab(self):
        """Génère l'onglet métriques"""
        top_degree = self._get_top_modules("degree_centrality", 10)
        top_in = self._get_top_modules("in_degree", 10)
        top_out = self._get_top_modules("out_degree", 10)
        top_betweenness = self._get_top_modules("betweenness_centrality", 10)
        
        return f"""
        <div class="section-card">
            <h2>📈 Top 10 - Centralité de Degré</h2>
            <p style="color: #64748b; margin-bottom: 20px;">Modules les plus connectés (hubs du système)</p>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Module</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'<tr><td>{i}</td><td>{mod}</td><td>{score:.3f}</td></tr>' 
                             for i, (mod, score) in enumerate(top_degree, 1)])}
                </tbody>
            </table>
        </div>
        
        <div class="section-card">
            <h2>🔗 Top 10 - Degré Entrant</h2>
            <p style="color: #64748b; margin-bottom: 20px;">Modules les plus utilisés (impact fort si modifiés)</p>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Module</th>
                        <th>Dépendants</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'<tr><td>{i}</td><td>{mod}</td><td>{count}</td></tr>' 
                             for i, (mod, count) in enumerate(top_in, 1)])}
                </tbody>
            </table>
        </div>
        
        <div class="section-card">
            <h2>📤 Top 10 - Degré Sortant</h2>
            <p style="color: #64748b; margin-bottom: 20px;">Modules avec le plus de dépendances (couplage fort)</p>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Module</th>
                        <th>Dépendances</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'<tr><td>{i}</td><td>{mod}</td><td>{count}</td></tr>' 
                             for i, (mod, count) in enumerate(top_out, 1)])}
                </tbody>
            </table>
        </div>
        
        <div class="section-card">
            <h2>🌉 Top 10 - Centralité d'Intermédiarité</h2>
            <p style="color: #64748b; margin-bottom: 20px;">Modules "pont" critiques (goulots d'étranglement)</p>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Module</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'<tr><td>{i}</td><td>{mod}</td><td>{score:.3f}</td></tr>' 
                             for i, (mod, score) in enumerate(top_betweenness, 1)])}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_security_tab(self):
        """Génère l'onglet sécurité"""
        if not self.security:
            return ""
        
        summary = self.security.get_summary()
        
        # Récupérer toutes les vulnérabilités (c'est un dict module -> liste)
        all_vulns = []
        for module_name, vulns_list in self.security.vulnerabilities.items():
            all_vulns.extend(vulns_list)
        
        # Générer le tableau des vulnérabilités
        vuln_rows = []
        for vuln in all_vulns[:50]:  # Limiter à 50 pour la performance
            severity_class = {
                'CRITIQUE': 'badge-danger',
                'ÉLEVÉ': 'badge-warning',
                'MOYEN': 'badge-info'
            }.get(vuln['severity'], 'badge-info')
            
            vuln_rows.append(f"""
            <tr>
                <td><span class="badge {severity_class}">{vuln['severity']}</span></td>
                <td style="font-family: monospace; font-size: 0.9em;">{vuln['module']}</td>
                <td>{vuln.get('type', 'N/A')}</td>
                <td style="color: #dc2626; font-weight: 600;">{vuln['function']}</td>
                <td style="color: #64748b;">{vuln.get('description', '')}</td>
                <td style="text-align: center;">{vuln['line']}</td>
            </tr>
            """)
        
        return f"""
        <div class="stats-grid">
            <div class="stat-card danger">
                <h3>Total Vulnérabilités</h3>
                <div class="value">{summary['total']}</div>
            </div>
            <div class="stat-card danger">
                <h3>Critiques</h3>
                <div class="value">{summary['by_severity']['CRITIQUE']}</div>
            </div>
            <div class="stat-card warning">
                <h3>Élevées</h3>
                <div class="value">{summary['by_severity']['ÉLEVÉ']}</div>
            </div>
            <div class="stat-card info">
                <h3>Moyennes</h3>
                <div class="value">{summary['by_severity']['MOYEN']}</div>
            </div>
        </div>
        
        {f'<div class="alert alert-danger"><strong>⚠️ Attention Critique !</strong> {summary["by_severity"]["CRITIQUE"]} vulnérabilité(s) critique(s) détectée(s). Action immédiate requise.</div>' if summary['by_severity']['CRITIQUE'] > 0 else ''}
        
        <div class="section-card">
            <h2>🔒 Détail des Vulnérabilités</h2>
            <table>
                <thead>
                    <tr>
                        <th>Sévérité</th>
                        <th>Module</th>
                        <th>Type</th>
                        <th>Fonction</th>
                        <th>Description</th>
                        <th>Ligne</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(vuln_rows)}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_attack_surface_tab(self):
        """Génère l'onglet attack surface"""
        if not self.attack_surface or not self.attack_surface.entry_points:
            return ""
        
        return generate_attack_surface_section(self.attack_surface)
    
    def _generate_dependencies_tab(self):
        """Génère l'onglet dépendances"""
        cycles_html = self._generate_cycles_section()
        
        deps_badges = []
        for dep in sorted(self.external_deps):
            deps_badges.append(f'<span class="badge badge-info" style="margin: 5px;">{dep}</span>')
        
        return f"""
        <div class="section-card">
            <h2>📦 Dépendances Externes ({len(self.external_deps)})</h2>
            <div style="margin-top: 20px;">
                {''.join(deps_badges) if deps_badges else '<p style="color: #64748b;">Aucune dépendance externe détectée</p>'}
            </div>
        </div>
        
        {cycles_html}
        """
    
    def _generate_graphs_tab(self, img_simple, img_metrics, interactive_graph):
        """Génère l'onglet visualisations"""
        return f"""
        <div class="section-card">
            <h2>🌐 Visualisations Interactives</h2>
            <p style="color: #64748b; margin-bottom: 20px;">
                Explorez le graphe de dépendances de manière interactive avec zoom, déplacement et tooltips.
            </p>
            <a href="{interactive_graph}" target="_blank" class="interactive-link">
                🎮 Ouvrir le Graphe Interactif
            </a>
        </div>
        
        <div class="section-card">
            <h2>📊 Graphe Simple</h2>
            <div class="graph-container">
                <img src="{img_simple}" alt="Graphe simple de dépendances">
            </div>
        </div>
        
        <div class="section-card">
            <h2>📈 Graphe avec Métriques</h2>
            <div class="graph-container">
                <img src="{img_metrics}" alt="Graphe avec métriques de centralité">
            </div>
        </div>
        """
    
    def _generate_ai_suggestions_tab(self):
        """Génère l'onglet suggestions IA"""
        # Extraire les problèmes pour l'API (script JSON caché)
        issues = []
        
        # 1. Ajouter les vulnérabilités de sécurité (limité à 10 pour performance)
        if self.security:
            all_vulns = self.security.get_all_vulnerabilities()
            for vuln in all_vulns[:10]:  # Limiter à 10 pour performance
                # Extraire le code source avec cache
                code_snippet = self._extract_code_snippet(vuln.get('module', ''), vuln.get('line', 0))
                
                issues.append({
                    'category': 'security',
                    'type': vuln.get('type', 'Unknown'),
                    'severity': vuln.get('severity', 'MOYEN'),
                    'description': vuln.get('description', ''),
                    'module': vuln.get('module', ''),
                    'line': vuln.get('line', 0),
                    'code': code_snippet
                })
        
        # 2. Ajouter les dépendances circulaires - DÉSACTIVÉ pour performance
        # La détection de cycles est trop lente sur gros graphes
        # Les cycles sont déjà affichés dans l'onglet Dépendances
        
        issues_json = json.dumps(issues, ensure_ascii=False)
        
        return f"""
        <div class="section-card" style="text-align: center; padding: 60px 40px;">
            <div style="font-size: 4em; margin-bottom: 20px;">🤖</div>
            <h2 style="margin-bottom: 15px;">Suggestions IA Interactives</h2>
            <p style="color: #64748b; font-size: 1.1em; margin-bottom: 30px; max-width: 600px; margin-left: auto; margin-right: auto;">
                Les suggestions IA avec génération dynamique sont disponibles dans l'interface web interactive.
            </p>
            
            <div class="alert alert-info" style="max-width: 700px; margin: 0 auto 30px auto; text-align: left;">
                <strong>🌐 Interface Web</strong><br>
                Pour obtenir des suggestions IA en temps réel avec OpenAI, Claude ou Ollama :
                <ol style="margin-top: 10px; margin-bottom: 0;">
                    <li>Lancez l'interface web : <code>cd web_ui && python app.py</code></li>
                    <li>Ouvrez <code>http://localhost:5000</code> dans votre navigateur</li>
                    <li>Analysez votre projet</li>
                    <li>Cliquez sur "🤖 Suggestions IA Interactives"</li>
                </ol>
            </div>
            
            <div style="background: var(--card-bg); border: 2px solid var(--border); border-radius: 12px; padding: 25px; max-width: 700px; margin: 0 auto; text-align: left;">
                <h3 style="margin-bottom: 15px;">✨ Fonctionnalités disponibles dans l'interface web :</h3>
                <ul style="line-height: 2; color: #64748b;">
                    <li>🔒 Suggestions pour les vulnérabilités de sécurité</li>
                    <li>🔄 Suggestions pour les dépendances circulaires</li>
                    <li>✅ Code corrigé généré automatiquement</li>
                    <li>📋 Étapes de correction détaillées</li>
                    <li>📥 Copie du code en un clic</li>
                    <li>🤖 Support OpenAI GPT-4, Claude 3.5, ou Ollama (local)</li>
                </ul>
            </div>
            
            <p style="color: #94a3b8; margin-top: 30px; font-size: 0.95em;">
                💡 Consultez <code>AI_ADVISOR_GUIDE.md</code> et <code>OLLAMA_DOCKER_SETUP.md</code> pour configurer l'IA
            </p>
        </div>
        
        <!-- Script JSON caché pour l'API -->
        <script id="ai-issues" type="application/json">
        {issues_json}
        </script>
        """
    
    def _extract_code_snippet(self, module_name: str, line_number: int, context_lines: int = 2) -> str:
        """Extrait un snippet de code autour d'une ligne donnée"""
        if not module_name or line_number <= 0:
            return ""
        
        try:
            # module_name peut être un chemin relatif comme "src/mymodule.py" ou "Word_Jumble/word_jumble.py"
            # Essayer de trouver le fichier correspondant
            file_path = None
            
            # 1. Essayer directement si c'est un chemin absolu
            if os.path.exists(module_name):
                file_path = module_name
            # 2. Essayer avec project_path si disponible
            elif self.project_path:
                candidate = self.project_path / module_name
                if candidate.exists():
                    file_path = str(candidate)
            # 3. Chercher dans module_to_file par correspondance partielle
            if not file_path:
                for node_name, node_file in self.module_to_file.items():
                    if module_name in node_file or node_file.endswith(module_name):
                        file_path = node_file
                        break
            
            if not file_path or not os.path.exists(file_path):
                return ""  # Retourner vide au lieu d'un message d'erreur
            
            # Utiliser le cache pour éviter de relire le même fichier
            if file_path not in self._file_cache:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._file_cache[file_path] = f.readlines()
            
            lines = self._file_cache[file_path]
            
            # Extraire les lignes avec contexte
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            snippet_lines = lines[start_line:end_line]
            return ''.join(snippet_lines).strip()
        
        except Exception as e:
            return ""  # Retourner vide en cas d'erreur
    
    def _generate_cycles_section(self):
        """Génère la section des cycles"""
        if self.graph_info['is_dag']:
            return '<div class="alert alert-info">✅ Aucun cycle détecté. Le graphe est acyclique (DAG).</div>'
        
        cycles = []
        try:
            cycles_found = list(nx.simple_cycles(self.graph))[:5]
            for i, cycle in enumerate(cycles_found, 1):
                cycle_str = ' → '.join(cycle) + f' → {cycle[0]}'
                cycles.append(f'<li><strong>Cycle {i}:</strong> {cycle_str}</li>')
        except:
            pass
        
        if cycles:
            return f"""
            <div class="section-card">
                <h2>⚠️ Cycles de Dépendances Détectés</h2>
                <div class="alert alert-warning">
                    <strong>Attention !</strong> Des dépendances circulaires ont été détectées.
                </div>
                <ul style="line-height: 2; color: #64748b;">
                    {''.join(cycles)}
                </ul>
            </div>
            """
        return ""
    
    def _get_top_modules(self, metric: str, top_n: int = 10) -> list:
        """Récupère les top modules pour une métrique donnée"""
        if metric not in self.metrics:
            return []
        
        sorted_modules = sorted(
            self.metrics[metric].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_modules[:top_n]
