"""
Étape 2 : Construction du graphe de dépendances avec NetworkX
Transforme les dépendances en graphe orienté
"""

import networkx as nx
from typing import Dict, Set


class GraphBuilder:
    """Construit un graphe de dépendances à partir des données parsées"""
    
    def __init__(self):
        """Initialise le graphe"""
        self.graph = nx.DiGraph()
    
    def build_graph(self, dependencies: Dict[str, Set[str]]) -> nx.DiGraph:
        """
        Construit le graphe de dépendances
        
        Args:
            dependencies: Dictionnaire {module: ensemble_des_dépendances}
            
        Returns:
            Graphe NetworkX orienté
        """
        # Ajouter tous les nœuds (modules)
        for module in dependencies.keys():
            self.graph.add_node(module)
        
        # Créer une map pour matcher les imports aux modules
        module_map = {}
        for module in dependencies.keys():
            # Enlever .py et obtenir le chemin du module
            module_path = module.replace('.py', '')
            
            # Pour __init__.py, le package est le dossier parent
            if module_path.endswith('/__init__'):
                package_name = module_path.replace('/__init__', '')
                module_map[package_name] = module
                # Aussi avec juste le nom final du package
                if '/' in package_name:
                    module_map[package_name.split('/')[-1]] = module
            else:
                # Nom complet du module (avec path)
                module_map[module_path] = module
                # Nom simple (juste le fichier)
                simple_name = module_path.split('/')[-1]
                module_map[simple_name] = module
        
        # Ajouter les arêtes (dépendances)
        for module, deps in dependencies.items():
            for dep in deps:
                # Essayer de trouver la correspondance
                matched_module = None
                
                # 1. Correspondance exacte
                if dep in module_map:
                    matched_module = module_map[dep]
                
                # 2. Premier segment de l'import (ex: "app.models" -> "app")
                if not matched_module:
                    first_segment = dep.split('.')[0]
                    if first_segment in module_map:
                        matched_module = module_map[first_segment]
                
                # 3. Chemin complet (ex: "app/models")
                if not matched_module:
                    dep_as_path = dep.replace('.', '/')
                    if dep_as_path in module_map:
                        matched_module = module_map[dep_as_path]
                
                if matched_module and matched_module != module:
                    self.graph.add_edge(module, matched_module)
        
        return self.graph
    
    def detect_cycles(self) -> list:
        """
        Détecte les dépendances circulaires
        
        Returns:
            Liste des cycles détectés
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except:
            return []
    
    def get_graph_info(self) -> dict:
        """
        Retourne des informations sur le graphe
        
        Returns:
            Dictionnaire avec les statistiques du graphe
        """
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
            "cycles": len(self.detect_cycles())
        }
