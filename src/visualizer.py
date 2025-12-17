"""
Étape 4 : Visualisation du graphe de dépendances
Crée des représentations graphiques avec Matplotlib
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Optional


class GraphVisualizer:
    """Visualise le graphe de dépendances"""
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialise le visualiseur
        
        Args:
            graph: Graphe NetworkX à visualiser
        """
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
