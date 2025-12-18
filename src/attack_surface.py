"""
Attack Surface Analyzer - Analyse de la surface d'attaque
Identifie les points d'entrée publics et calcule leur distance vers les modules critiques
"""

import ast
import networkx as nx
from typing import Dict, List, Set, Tuple
from pathlib import Path


# Décorateurs de routes web
ROUTE_DECORATORS = {
    'app.route',        # Flask
    'route',            # Flask
    'api.route',        # Flask Blueprint
    'get',              # FastAPI
    'post',             # FastAPI
    'put',              # FastAPI
    'delete',           # FastAPI
    'patch',            # FastAPI
    'api_view',         # Django REST Framework
    'action',           # Django REST Framework
}

# Patterns de frameworks web
WEB_FRAMEWORKS = {
    'flask': ['Flask', 'Blueprint', '@app.route', '@api.route'],
    'fastapi': ['FastAPI', '@app.get', '@app.post'],
    'django': ['django.views', 'APIView', 'ViewSet'],
}


class AttackSurfaceAnalyzer:
    """Analyse la surface d'attaque d'un projet"""
    
    def __init__(self, graph: nx.DiGraph):
        """
        Initialise l'analyseur
        
        Args:
            graph: Graphe de dépendances du projet
        """
        self.graph = graph
        self.entry_points: Dict[str, List[Dict]] = {}
        self.attack_surface: List[Dict] = []
        self.critical_paths: List[Dict] = []
    
    def analyze_file(self, file_path: Path, module_name: str):
        """
        Analyse un fichier pour détecter les points d'entrée
        
        Args:
            file_path: Chemin du fichier
            module_name: Nom du module
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            entry_points = []
            
            # Parcourir toutes les fonctions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Vérifier si la fonction a des décorateurs de route
                    for decorator in node.decorator_list:
                        if self._is_route_decorator(decorator):
                            route_info = self._extract_route_info(decorator, node)
                            entry_points.append({
                                'type': 'http_route',
                                'function': node.name,
                                'line': node.lineno,
                                'decorator': route_info['decorator'],
                                'path': route_info.get('path', 'unknown'),
                                'methods': route_info.get('methods', [])
                            })
            
            if entry_points:
                self.entry_points[module_name] = entry_points
        
        except Exception as e:
            pass
    
    def _is_route_decorator(self, decorator) -> bool:
        """Vérifie si un décorateur est une route web"""
        if isinstance(decorator, ast.Name):
            return decorator.id.lower() in ['route', 'get', 'post', 'put', 'delete', 'patch']
        
        elif isinstance(decorator, ast.Attribute):
            attr_name = self._get_decorator_name(decorator)
            for route_dec in ROUTE_DECORATORS:
                if attr_name and route_dec in attr_name.lower():
                    return True
        
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Attribute):
                attr_name = self._get_decorator_name(decorator.func)
                for route_dec in ROUTE_DECORATORS:
                    if attr_name and route_dec in attr_name.lower():
                        return True
        
        return False
    
    def _get_decorator_name(self, node) -> str:
        """Extrait le nom complet d'un décorateur"""
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
        
        return '.'.join(reversed(parts))
    
    def _extract_route_info(self, decorator, func_node) -> Dict:
        """Extrait les informations d'une route"""
        info = {
            'decorator': self._get_decorator_name(decorator) if hasattr(decorator, 'attr') else str(decorator.id if hasattr(decorator, 'id') else 'unknown'),
            'function': func_node.name
        }
        
        # Essayer d'extraire le chemin et les méthodes
        if isinstance(decorator, ast.Call):
            for arg in decorator.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    if arg.value.startswith('/'):
                        info['path'] = arg.value
            
            for keyword in decorator.keywords:
                if keyword.arg == 'methods':
                    if isinstance(keyword.value, ast.List):
                        info['methods'] = [
                            elt.value for elt in keyword.value.elts 
                            if isinstance(elt, ast.Constant)
                        ]
        
        return info
    
    def calculate_attack_surface(self, metrics: dict):
        """
        Calcule la surface d'attaque
        
        Args:
            metrics: Dictionnaire des métriques de centralité
        """
        if not self.entry_points:
            return
        
        degree_centrality = metrics.get('degree_centrality', {})
        
        # Pour chaque point d'entrée
        for entry_module, entry_list in self.entry_points.items():
            for entry in entry_list:
                # Calculer les distances vers tous les autres modules
                distances = self._calculate_distances_from_entry(entry_module)
                
                # Identifier les modules critiques accessibles
                for target_module, distance in distances.items():
                    if distance is None or distance > 5:  # Ignorer trop loin
                        continue
                    
                    centrality = degree_centrality.get(target_module, 0)
                    
                    # Si module critique (haute centralité) ET proche de l'entrée
                    if centrality > 0.3 and distance <= 3:
                        risk_level = self._calculate_risk_level(distance, centrality)
                        
                        self.attack_surface.append({
                            'entry_point': entry_module,
                            'entry_function': entry['function'],
                            'entry_path': entry.get('path', 'unknown'),
                            'target_module': target_module,
                            'distance': distance,
                            'centrality': centrality,
                            'risk_level': risk_level
                        })
        
        # Trier par niveau de risque
        self.attack_surface.sort(key=lambda x: (x['risk_level'], -x['distance']), reverse=True)
    
    def _calculate_distances_from_entry(self, entry_module: str) -> Dict[str, int]:
        """Calcule les distances depuis un point d'entrée vers tous les modules"""
        distances = {}
        
        try:
            # Utiliser l'algorithme de Dijkstra pour calculer les distances
            if entry_module in self.graph:
                lengths = nx.single_source_shortest_path_length(self.graph, entry_module, cutoff=5)
                distances = lengths
        except:
            pass
        
        return distances
    
    def _calculate_risk_level(self, distance: int, centrality: float) -> str:
        """Calcule le niveau de risque"""
        # Plus c'est proche ET centrale, plus c'est risqué
        score = (1 / (distance + 1)) * centrality
        
        if score > 0.2:
            return "CRITIQUE"
        elif score > 0.1:
            return "ÉLEVÉ"
        elif score > 0.05:
            return "MOYEN"
        else:
            return "FAIBLE"
    
    def get_summary(self) -> Dict:
        """Retourne un résumé de la surface d'attaque"""
        total_entries = sum(len(entries) for entries in self.entry_points.values())
        
        risk_counts = {
            'CRITIQUE': 0,
            'ÉLEVÉ': 0,
            'MOYEN': 0,
            'FAIBLE': 0
        }
        
        for item in self.attack_surface:
            risk_counts[item['risk_level']] += 1
        
        return {
            'total_entry_points': total_entries,
            'entry_modules': len(self.entry_points),
            'critical_paths': len([x for x in self.attack_surface if x['risk_level'] in ['CRITIQUE', 'ÉLEVÉ']]),
            'total_attack_surface': len(self.attack_surface),
            'by_risk': risk_counts
        }
    
    def get_top_risks(self, top_n: int = 10) -> List[Dict]:
        """Retourne les chemins les plus risqués"""
        return self.attack_surface[:top_n]
