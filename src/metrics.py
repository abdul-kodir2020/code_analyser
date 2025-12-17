"""
Étape 3 : Calcul des métriques et statistiques
Analyse la centralité, couplage et complexité du graphe
"""

import networkx as nx
from typing import Dict


class MetricsCalculator:
    """Calcule différentes métriques sur le graphe de dépendances"""
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialise le calculateur de métriques
        
        Args:
            graph: Graphe de dépendances NetworkX
        """
        self.graph = graph
    
    def degree_centrality(self) -> Dict[str, float]:
        """
        Calcule la centralité de degré
        Identifie les modules les plus connectés
        
        Returns:
            Dictionnaire {module: centralité}
        """
        return nx.degree_centrality(self.graph)
    
    def betweenness_centrality(self) -> Dict[str, float]:
        """
        Calcule la centralité d'intermédiarité
        Identifie les modules "pont" critiques
        
        Returns:
            Dictionnaire {module: centralité}
        """
        return nx.betweenness_centrality(self.graph)
    
    def in_degree(self) -> Dict[str, int]:
        """
        Calcule le degré entrant (dépendants)
        Modules dont beaucoup d'autres dépendent
        
        Returns:
            Dictionnaire {module: nombre_de_dépendants}
        """
        return dict(self.graph.in_degree())
    
    def out_degree(self) -> Dict[str, int]:
        """
        Calcule le degré sortant (dépendances)
        Modules qui dépendent de beaucoup d'autres
        
        Returns:
            Dictionnaire {module: nombre_de_dépendances}
        """
        return dict(self.graph.out_degree())
    
    def calculate_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Calcule toutes les métriques
        
        Returns:
            Dictionnaire avec toutes les métriques
        """
        metrics = {
            "degree_centrality": self.degree_centrality(),
            "betweenness_centrality": self.betweenness_centrality(),
            "in_degree": self.in_degree(),
            "out_degree": self.out_degree()
        }
        
        return metrics
    
    def get_top_modules(self, metric: str = "degree_centrality", top_n: int = 5) -> list:
        """
        Retourne les modules avec les valeurs les plus élevées pour une métrique
        
        Args:
            metric: Nom de la métrique à analyser
            top_n: Nombre de modules à retourner
            
        Returns:
            Liste des top modules avec leurs scores
        """
        all_metrics = self.calculate_all_metrics()
        
        if metric not in all_metrics:
            return []
        
        sorted_modules = sorted(
            all_metrics[metric].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_modules[:top_n]
