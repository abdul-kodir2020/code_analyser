"""
Étape 4 : Visualisation du graphe de dépendances
Crée des représentations graphiques avec Matplotlib et PyVis (interactif)
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional
from pyvis.network import Network


class GraphVisualizer:
    """Visualise le graphe de dépendances"""
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialise le visualiseur
        
        Args:
            graph: Graphe NetworkX à visualiser
        """
        self.graph = graph
        self.graph = graph
    
    def draw_simple(self, output_file: Optional[str] = None):
        """
        Dessine le graphe de manière simple
        
        Args:
            output_file: Chemin du fichier de sortie (None = affichage)
        """
        plt.figure(figsize=(12, 8))
        
        # Layout pour positionner les nœuds
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # Dessiner le graphe
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_color='lightblue',
            node_size=1500,
            font_size=8,
            font_weight='bold',
            arrows=True,
            arrowsize=20,
            edge_color='gray',
            alpha=0.7
        )
        
        plt.title("Graphe de Dépendances", fontsize=16, fontweight='bold')
        
        if output_file:
            plt.savefig(output_file, bbox_inches='tight', dpi=300)
            print(f"✅ Graphe sauvegardé : {output_file}")
        else:
            plt.show()
        
        plt.close()
    
    def draw_with_metrics(self, metrics: dict, output_file: Optional[str] = None):
        """
        Dessine le graphe avec coloration selon les métriques
        
        Args:
            metrics: Dictionnaire des métriques
            output_file: Chemin du fichier de sortie
        """
        fig, ax = plt.subplots(figsize=(14, 10))
        
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # Taille des nœuds selon la centralité
        if 'degree_centrality' in metrics:
            centrality = metrics['degree_centrality']
            node_sizes = [centrality.get(node, 0) * 5000 + 500 for node in self.graph.nodes()]
        else:
            node_sizes = 1500
        
        # Couleurs selon le degré entrant
        if 'in_degree' in metrics:
            in_deg = metrics['in_degree']
            node_colors = [in_deg.get(node, 0) for node in self.graph.nodes()]
        else:
            node_colors = 'lightblue'
        
        # Dessiner
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_color=node_colors,
            node_size=node_sizes,
            font_size=8,
            font_weight='bold',
            arrows=True,
            arrowsize=20,
            edge_color='gray',
            alpha=0.7,
            cmap=plt.cm.Blues,
            ax=ax
        )
        
        ax.set_title("Graphe de Dépendances (avec métriques)", fontsize=16, fontweight='bold')
        
        # Ajouter colorbar seulement si il y a des données
        if isinstance(node_colors, list) and len(node_colors) > 0 and max(node_colors) > 0:
            import matplotlib.cm as cm
            from matplotlib.colors import Normalize
            norm = Normalize(vmin=min(node_colors), vmax=max(node_colors))
            sm = cm.ScalarMappable(cmap=plt.cm.Blues, norm=norm)
            sm.set_array([])
            fig.colorbar(sm, ax=ax, label='Degré entrant')
        
        if output_file:
            plt.savefig(output_file, bbox_inches='tight', dpi=300)
            print(f"✅ Graphe avec métriques sauvegardé : {output_file}")
        else:
            plt.show()
        
        plt.close()
    
    def draw_hierarchical(self, output_file: Optional[str] = None):
        """
        Dessine le graphe en disposition hiérarchique
        
        Args:
            output_file: Chemin du fichier de sortie
        """
        plt.figure(figsize=(14, 10))
        
        # Layout hiérarchique (si le graphe est un DAG)
        if nx.is_directed_acyclic_graph(self.graph):
            pos = nx.nx_agraph.graphviz_layout(self.graph, prog='dot')
        else:
            pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        nx.draw(
            self.graph,
            pos,
            with_labels=True,
            node_color='lightgreen',
            node_size=1500,
            font_size=8,
            font_weight='bold',
            arrows=True,
            arrowsize=20,
            edge_color='gray',
            alpha=0.7
        )
        
        plt.title("Graphe Hiérarchique de Dépendances", fontsize=16, fontweight='bold')
        
        if output_file:
            plt.savefig(output_file, bbox_inches='tight', dpi=300)
            print(f"✅ Graphe hiérarchique sauvegardé : {output_file}")
        else:
            plt.show()
        
        plt.close()
    
    def draw_interactive(self, metrics: dict = None, output_file: str = "graph_interactive.html", security=None):
        """
        Crée un graphe interactif avec PyVis
        
        Args:
            metrics: Dictionnaire des métriques (optionnel)
            output_file: Nom du fichier HTML de sortie
            security: Analyseur de sécurité (optionnel)
        """
        # Créer le réseau PyVis - PLEIN ÉCRAN
        net = Network(
            height='100vh',  # 100% de la hauteur de la fenêtre
            width='100%',
            bgcolor="#1a1a1a",  # Fond plus sombre
            font_color="#e0e0e0",
            directed=True
        )
        
        # Configuration de la physique pour une meilleure visualisation
        net.set_options("""
        {
            "physics": {
                "enabled": true,
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 200,
                    "springConstant": 0.08,
                    "damping": 0.4,
                    "avoidOverlap": 0.5
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {"iterations": 150}
            },
            "nodes": {
                "font": {
                    "size": 16,
                    "face": "Arial",
                    "color": "#ffffff"
                },
                "borderWidth": 2,
                "borderWidthSelected": 4
            },
            "edges": {
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 0.5
                    }
                },
                "smooth": {
                    "type": "continuous"
                },
                "color": {
                    "color": "#666666",
                    "highlight": "#667eea",
                    "hover": "#888888"
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 100,
                "navigationButtons": true,
                "keyboard": {
                    "enabled": true
                }
            },
            "configure": {
                "enabled": false
            }
        }
        """)
        
        # Calculer les métriques pour la taille et couleur des nœuds
        if metrics:
            degree_centrality = metrics.get('degree_centrality', {})
            betweenness_centrality = metrics.get('betweenness_centrality', {})
            in_degree = metrics.get('in_degree', {})
            out_degree = metrics.get('out_degree', {})
        else:
            degree_centrality = nx.degree_centrality(self.graph)
            betweenness_centrality = nx.betweenness_centrality(self.graph)
            in_degree = dict(self.graph.in_degree())
            out_degree = dict(self.graph.out_degree())
        
        # Normaliser les valeurs pour les couleurs
        max_in_degree = max(in_degree.values()) if in_degree.values() else 1
        
        # Ajouter les nœuds avec style amélioré
        for node in self.graph.nodes():
            # Vérifier si le module est dangereux
            is_dangerous = security and security.is_module_dangerous(node)
            
            # Métriques
            centrality = degree_centrality.get(node, 0)
            betweenness = betweenness_centrality.get(node, 0)
            in_deg = in_degree.get(node, 0)
            out_deg = out_degree.get(node, 0)
            
            # Taille basée sur la centralité
            size = 25 + centrality * 120
            
            # Couleur : ROUGE si dangereux, sinon gradient de bleu
            if is_dangerous:
                color = '#ff3333'  # Rouge vif pour modules dangereux
                border_color = '#ff0000'
            else:
                color_intensity = int(255 - (in_deg / max_in_degree * 150)) if max_in_degree > 0 else 255
                color = f'#{color_intensity:02x}{color_intensity:02x}ff'
                border_color = '#4444ff'
            
            # Info bulle simplifiée avec 2 métriques
            title = f"""<div>
<div>{node}</div>
<div><b>Centralité:</b> {centrality:.3f}</div>
<div><b>Dépendants:</b> {in_deg}</div>
</div>"""
            
            # Ajouter les vulnérabilités si présentes
            if is_dangerous:
                vulns = security.get_module_vulnerabilities(node)
                vuln_info = f"<div style='margin-top: 8px; padding-top: 8px; border-top: 1px solid #444;'><b style='color: #ff3333;'>⚠️ {len(vulns)} vulnérabilité{'s' if len(vulns) > 1 else ''}</b></div>"
                title = title.replace('</div>"""', vuln_info + '</div>"""')
            
            net.add_node(
                node,
                label=node.split('/')[-1],  # Afficher seulement le nom du fichier
                title=title,
                size=size,
                color=color,
                borderWidth=3,
                borderWidthSelected=5,
                font={'size': 16, 'color': 'rgba(255,255,255,0.9)', 'face': 'Arial'},
                shadow={'enabled': True, 'size': 10}
            )
        
        # Ajouter les arêtes
        for source, target in self.graph.edges():
            net.add_edge(
                source, 
                target, 
                color={'color': '#666666', 'highlight': '#667eea'},
                width=2,
                arrows={'to': {'enabled': True, 'scaleFactor': 0.8}}
            )
        
        # Générer le fichier HTML
        net.save_graph(output_file)
        
        # Modifier le HTML généré pour forcer le plein écran et améliorer les tooltips
        with open(output_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Ajouter du CSS pour supprimer les marges, plein écran et styliser les tooltips
        html_content = html_content.replace(
            '<head>',
            '''<head>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }
                #mynetwork {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw !important;
                    height: 100vh !important;
                }
                /* Améliorer le style des tooltips */
                .vis-tooltip {
                    background-color: rgba(20, 20, 30, 0.95) !important;
                    border: 2px solid #667eea !important;
                    border-radius: 8px !important;
                    padding: 12px 16px !important;
                    font-family: Arial, sans-serif !important;
                    font-size: 14px !important;
                    color: #e0e0e0 !important;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
                    max-width: 350px !important;
                    min-width: 250px !important;
                }
                /* Améliorer la visibilité des boutons de navigation */
                .vis-button {
                    background-color: #667eea !important;
                    border: 2px solid #5568d3 !important;
                }
                .vis-button:hover {
                    background-color: #5568d3 !important;
                    box-shadow: 0 0 10px #667eea !important;
                }
            </style>'''
        )
        
        # Pas de modification supplémentaire du HTML
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Graphe interactif sauvegardé : {output_file}")
        
        return output_file

