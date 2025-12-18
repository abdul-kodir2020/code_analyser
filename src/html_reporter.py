"""
Générateur de rapport HTML
Crée une page web interactive pour visualiser les résultats de l'analyse
"""

import networkx as nx
from datetime import datetime
from pathlib import Path
from src.attack_surface_html import generate_attack_surface_section


class HTMLReporter:
    """Génère un rapport HTML complet de l'analyse"""
    
    def __init__(self, graph: nx.DiGraph, metrics: dict, graph_info: dict, project_name: str, external_deps: set = None, security=None, attack_surface=None):
        """
        Initialise le générateur de rapport
        
        Args:
            graph: Graphe de dépendances
            metrics: Dictionnaire des métriques calculées
            graph_info: Informations sur le graphe
            project_name: Nom du projet analysé
            external_deps: Ensemble des dépendances externes
            security: Analyseur de sécurité
            attack_surface: Analyseur de surface d'attaque
        """
        self.graph = graph
        self.metrics = metrics
        self.graph_info = graph_info
        self.project_name = project_name
        self.external_deps = external_deps or set()
        self.security = security
        self.attack_surface = attack_surface
    
    def generate_report(self, output_file: str = "report.html", 
                       img_simple: str = "output_graph_simple.png",
                       img_metrics: str = "output_graph_metrics.png",
                       interactive_graph: str = "graph_interactive.html"):
        """
        Génère le rapport HTML complet
        
        Args:
            output_file: Nom du fichier HTML de sortie
            img_simple: Chemin de l'image du graphe simple
            img_metrics: Chemin de l'image du graphe avec métriques
            interactive_graph: Chemin du graphe interactif HTML
        """
        html_content = self._generate_html(img_simple, img_metrics, interactive_graph)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Rapport HTML généré : {output_file}")
        return output_file
    
    def _generate_html(self, img_simple: str, img_metrics: str, interactive_graph: str) -> str:
        """Génère le contenu HTML complet"""
        
        # Calculer les top modules
        top_degree = self._get_top_modules("degree_centrality", 10)
        top_in = self._get_top_modules("in_degree", 10)
        top_out = self._get_top_modules("out_degree", 10)
        top_betweenness = self._get_top_modules("betweenness_centrality", 10)
        
        # Détecter les cycles
        cycles_html = self._generate_cycles_section()
        
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analyse de Dépendances - {self.project_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-card.success .value {{
            color: #10b981;
        }}
        
        .stat-card.warning .value {{
            color: #f59e0b;
        }}
        
        .stat-card.danger .value {{
            color: #ef4444;
        }}
        
        .section {{
            padding: 40px;
        }}
        
        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #1f2937;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}
        
        .metric-table {{
            background: #f9fafb;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .metric-table h3 {{
            background: #667eea;
            color: white;
            padding: 15px;
            font-size: 1.1em;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        table th {{
            background: #e5e7eb;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
        }}
        
        table td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            word-wrap: break-word;
            overflow-wrap: break-word;
            max-width: 300px;
        }}
        
        table tr:hover {{
            background: #f3f4f6;
        }}  
        
        table td:first-child {{ 
            max-width: 50px;
        }}
        
        table td:last-child {{
            max-width: 100px;
        }}
        
        .rank {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .module-name {{
            font-family: 'Courier New', monospace;
            color: #1f2937;            word-break: break-all;
            font-size: 0.9em;        }}
        
        .score {{
            font-weight: 600;
            color: #059669;
        }}
        
        .graph-container {{
            margin-top: 30px;
            text-align: center;
        }}
        
        .graph-container img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 20px;
        }}
        
        .alert {{
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        
        .alert-warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            color: #92400e;
        }}
        
        .alert-success {{
            background: #d1fae5;
            border-left: 4px solid #10b981;
            color: #065f46;
        }}
        
        .cycle-list {{
            margin-top: 10px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        .cycle-item {{
            padding: 8px;
            background: white;
            margin: 5px 0;
            border-radius: 4px;
        }}
        
        footer {{
            background: #1f2937;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Analyse de Dépendances</h1>
            <p>{self.project_name}</p>
            <p style="font-size: 0.9em; opacity: 0.8;">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Modules</h3>
                <div class="value">{self.graph_info['nodes']}</div>
            </div>
            <div class="stat-card">
                <h3>Dépendances</h3>
                <div class="value">{self.graph_info['edges']}</div>
            </div>
            <div class="stat-card {'success' if self.graph_info['is_dag'] else 'danger'}">
                <h3>Structure</h3>
                <div class="value">{'✓ DAG' if self.graph_info['is_dag'] else '✗ Cycles'}</div>
            </div>
            <div class="stat-card {'success' if self.graph_info['cycles'] == 0 else 'danger'}">
                <h3>Cycles détectés</h3>
                <div class="value">{self.graph_info['cycles']}</div>
            </div>
        </div>
        
        {cycles_html}
                {self._generate_security_section()}
                <div class="section">
            <h2>� Dépendances Externes</h2>
            <div class="alert alert-success">
                <strong>{len(self.external_deps)} bibliothèques externes</strong> utilisées dans le projet
            </div>
            <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 10px;">
                {self._generate_external_deps_badges()}
            </div>
        </div>
        
        <div class="section">
            <h2>�📊 Métriques de Centralité</h2>
            
            <div class="metrics-grid">
                <div class="metric-table">
                    <h3>🏆 Top Centralité de Degré</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Module</th>
                                <th>Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_table_rows(top_degree)}
                        </tbody>
                    </table>
                </div>
                
                <div class="metric-table">
                    <h3>🔗 Top Modules Dépendants</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Module</th>
                                <th>Dépendants</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_table_rows(top_in)}
                        </tbody>
                    </table>
                </div>
                
                <div class="metric-table">
                    <h3>📤 Top Modules avec Dépendances</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Module</th>
                                <th>Dépendances</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_table_rows(top_out)}
                        </tbody>
                    </table>
                </div>
                
                <div class="metric-table">
                    <h3>🌉 Top Centralité d'Intermédiarité</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Module</th>
                                <th>Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            {self._generate_table_rows(top_betweenness)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Visualisations du Graphe</h2>
            
            <div class="alert alert-success">
                <strong>🎮 Graphe Interactif</strong> - Cliquez sur le bouton ci-dessous pour explorer le graphe avec zoom, drag & drop et filtres !
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{interactive_graph}" target="_blank" style="
                    display: inline-block;
                    padding: 15px 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    font-size: 1.2em;
                    font-weight: bold;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    transition: transform 0.2s;
                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    🎮 Ouvrir le Graphe Interactif
                </a>
            </div>
            
            <div class="graph-container">
                <h3>Graphe Simple</h3>
                <img src="{img_simple}" alt="Graphe simple de dépendances">
                
                <h3>Graphe avec Métriques</h3>
                <img src="{img_metrics}" alt="Graphe avec métriques">
            </div>
        </div>
        
        {self._generate_attack_surface_section() if self.attack_surface and self.attack_surface.entry_points else ''}
        
        <footer>
            <p>Généré par Code Dependency Analyzer | © 2025</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html
    
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
    
    def _generate_table_rows(self, data: list) -> str:
        """Génère les lignes HTML pour un tableau"""
        rows = []
        for i, (module, score) in enumerate(data, 1):
            rows.append(f"""
                <tr>
                    <td class="rank">{i}</td>
                    <td class="module-name">{module}</td>
                    <td class="score">{score:.3f}</td>
                </tr>
            """)
        
        return '\n'.join(rows) if rows else '<tr><td colspan="3">Aucune donnée</td></tr>'
    
    def _generate_cycles_section(self) -> str:
        """Génère la section des cycles détectés"""
        if self.graph_info['is_dag']:
            return """
            <div class="section">
                <div class="alert alert-success">
                    <strong>✅ Aucun cycle détecté !</strong> Le graphe est un DAG (Directed Acyclic Graph). 
                    C'est une bonne pratique : pas de dépendances circulaires.
                </div>
            </div>
            """
        
        try:
            cycles = list(nx.simple_cycles(self.graph))[:5]  # Top 5 cycles
            cycle_items = '\n'.join([
                f'<div class="cycle-item">{" → ".join(cycle)} → {cycle[0]}</div>'
                for cycle in cycles
            ])
            
            return f"""
            <div class="section">
                <div class="alert alert-warning">
                    <strong>⚠️ Dépendances circulaires détectées !</strong>
                    <div class="cycle-list">
                        {cycle_items}
                        {f'<p style="margin-top: 10px;"><em>... et {len(cycles) - 5} autres cycles</em></p>' if len(cycles) > 5 else ''}
                    </div>
                </div>
            </div>
            """
        except:
            return ""
    
    def _generate_external_deps_badges(self) -> str:
        """Génère les badges des dépendances externes"""
        if not self.external_deps:
            return '<p style="color: #666;">Aucune dépendance externe détectée</p>'
        
        badges = []
        for dep in sorted(self.external_deps):
            badges.append(f"""
                <span style="
                    display: inline-block;
                    padding: 6px 12px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 6px;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                    font-weight: 500;
                ">{dep}</span>
            """)
        
        return '\n'.join(badges)
    
    def _generate_security_section(self) -> str:
        """Génère la section de sécurité"""
        if not self.security:
            return ""
        
        summary = self.security.get_summary()
        
        if summary['total'] == 0:
            return """
            <div class="section">
                <h2>🔒 Analyse de Sécurité</h2>
                <div class="alert alert-success">
                    <strong>✅ Aucune vulnérabilité détectée !</strong> Le code ne contient pas de patterns dangereux connus.
                </div>
            </div>
            """
        
        # Générer les cartes de statistiques
        severity_cards = f"""
        <div class="stats" style="margin-top: 20px;">
            <div class="stat-card danger">
                <h3>Critiques</h3>
                <div class="value">{summary['by_severity']['CRITIQUE']}</div>
            </div>
            <div class="stat-card warning">
                <h3>Élevées</h3>
                <div class="value">{summary['by_severity']['ÉLEVÉ']}</div>
            </div>
            <div class="stat-card" style="color: #f59e0b;">
                <h3>Moyennes</h3>
                <div class="value">{summary['by_severity']['MOYEN']}</div>
            </div>
            <div class="stat-card success">
                <h3>Modules à risque</h3>
                <div class="value">{summary['dangerous_modules_count']}</div>
            </div>
        </div>
        """
        
        # Générer la liste des vulnérabilités
        vuln_table = self._generate_vulnerabilities_table()
        
        # Générer la liste des modules dangereux
        dangerous_modules_section = self._generate_dangerous_modules_section()
        
        return f"""
        <div class="section">
            <h2>🔒 Analyse de Sécurité</h2>
            <div class="alert alert-warning">
                <strong>⚠️ {summary['total']} vulnérabilités potentielles détectées</strong>
            </div>
            
            {severity_cards}
            
            {dangerous_modules_section}
            
            <div style="margin-top: 30px;">
                <h3>📋 Détails des Vulnérabilités</h3>
                {vuln_table}
            </div>
        </div>
        """
    
    def _generate_vulnerabilities_table(self) -> str:
        """Génère le tableau des vulnérabilités"""
        if not self.security or not self.security.vulnerabilities:
            return ""
        
        rows = []
        for module, vulns in self.security.vulnerabilities.items():
            for vuln in vulns:
                rows.append(f"""
                <tr>
                    <td class="rank">{vuln['severity']}</td>
                    <td class="module-name">{module}</td>
                    <td>{vuln['line']}</td>
                    <td style="font-family: 'Courier New', monospace; color: #dc2626;">{vuln['function']}</td>
                    <td>{vuln['description'].replace('🔴', '').replace('🟠', '').replace('🟡', '').strip()}</td>
                </tr>
                """)
        
        return f"""
        <div class="metric-table">
            <table>
                <thead>
                    <tr>
                        <th>Sévérité</th>
                        <th>Fichier</th>
                        <th>Ligne</th>
                        <th>Fonction</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_dangerous_modules_section(self) -> str:
        """Génère la section des modules dangereux"""
        if not self.security or not self.security.dangerous_modules:
            return ""
        
        # Trier les modules par nombre de vulnérabilités
        modules_with_counts = []
        for module, funcs in self.security.dangerous_modules.items():
            vuln_count = len(self.security.get_module_vulnerabilities(module))
            modules_with_counts.append((module, vuln_count, funcs))
        
        modules_with_counts.sort(key=lambda x: x[1], reverse=True)
        
        # Générer les cartes de modules
        module_cards = []
        for module, vuln_count, dangerous_funcs in modules_with_counts[:10]:  # Top 10
            severity_class = 'danger' if vuln_count >= 3 else 'warning' if vuln_count >= 2 else ''
            
            # Obtenir les vulnérabilités pour ce module
            vulns = self.security.get_module_vulnerabilities(module)
            vuln_details = '<br>'.join([
                f"• <code>{v['function']}</code> (ligne {v['line']})" 
                for v in vulns[:5]
            ])
            if len(vulns) > 5:
                vuln_details += f"<br><em>... et {len(vulns) - 5} autres</em>"
            
            module_cards.append(f"""
            <div class="metric-table" style="margin-bottom: 20px;">
                <div style="background: {'#fee2e2' if severity_class == 'danger' else '#fef3c7'}; padding: 20px; border-left: 4px solid {'#dc2626' if severity_class == 'danger' else '#f59e0b'};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; font-family: 'Courier New', monospace; color: #1f2937;">
                            🔴 {module}
                        </h4>
                        <span style="
                            background: {'#dc2626' if severity_class == 'danger' else '#f59e0b'};
                            color: white;
                            padding: 4px 12px;
                            border-radius: 12px;
                            font-weight: bold;
                            font-size: 0.9em;
                        ">
                            {vuln_count} vulnérabilité{'s' if vuln_count > 1 else ''}
                        </span>
                    </div>
                    <div style="font-size: 0.9em; color: #374151; margin-top: 10px;">
                        {vuln_details}
                    </div>
                </div>
            </div>
            """)
        
        return f"""
        <div style="margin-top: 30px;">
            <h3>🚨 Modules Dangereux ({len(modules_with_counts)})</h3>
            <p style="color: #666; margin-bottom: 20px;">
                Modules contenant des fonctions à risque ou des patterns de code vulnérables
            </p>
            {''.join(module_cards)}
        </div>
        """
    
    def _generate_attack_surface_section(self) -> str:
        """Génère la section de surface d'attaque"""
        if not self.attack_surface or not self.attack_surface.entry_points:
            return ""
        
        return generate_attack_surface_section(self.attack_surface)
