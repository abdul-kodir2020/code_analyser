"""
Étape 1 : Analyse du code source avec AST (Abstract Syntax Tree)
Parse les fichiers Python et extrait les dépendances
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set


class CodeParser:
    """Analyse les fichiers Python et extrait les imports et dépendances"""
    
    def __init__(self, project_path: str):
        """
        Initialise le parser
        
        Args:
            project_path: Chemin vers le projet à analyser
        """
        self.project_path = Path(project_path)
        self.dependencies: Dict[str, Set[str]] = {}
        self.external_dependencies: Dict[str, Set[str]] = {}
        self.all_modules: Set[str] = set()
    
    def parse_file(self, file_path: Path) -> Set[str]:
        """
        Parse un fichier Python et extrait ses imports
        
        Args:
            file_path: Chemin du fichier à parser
            
        Returns:
            Ensemble des modules importés
        """
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
        
        except Exception as e:
            print(f"⚠️  Erreur lors du parsing de {file_path}: {e}")
        
        return imports
    
    def parse_project(self) -> Dict[str, Set[str]]:
        """
        Parse tous les fichiers Python du projet
        
        Returns:
            Dictionnaire {fichier: ensemble_des_imports}
        """
        python_files = list(self.project_path.rglob("*.py"))
        print(f"   📁 Chemin projet : {self.project_path}")
        print(f"   📄 Fichiers trouvés : {len(python_files)}")
        
        # Premier passage : collecter tous les modules du projet
        for file_path in python_files:
            module_name = str(file_path.relative_to(self.project_path))
            self.all_modules.add(module_name.replace('.py', ''))
            if module_name.endswith('/__init__.py'):
                package_name = module_name.replace('/__init__.py', '')
                self.all_modules.add(package_name)
        
        # Second passage : parser les imports
        for file_path in python_files:
            module_name = str(file_path.relative_to(self.project_path))
            imports = self.parse_file(file_path)
            self.dependencies[module_name] = imports
            
            # Séparer imports internes vs externes
            internal = set()
            external = set()
            
            for imp in imports:
                # Vérifier si c'est un module interne
                is_internal = False
                for mod in self.all_modules:
                    if imp == mod or imp.split('.')[0] == mod or imp.split('.')[0] == mod.split('/')[-1]:
                        is_internal = True
                        break
                
                if is_internal:
                    internal.add(imp)
                else:
                    external.add(imp)
            
            self.external_dependencies[module_name] = external
            
            # Debug : afficher les premiers fichiers avec imports
            if imports and len(self.dependencies) <= 3:
                print(f"      {module_name}: {list(imports)[:3]}")
        
        # Afficher résumé des dépendances externes
        all_external = set()
        for ext in self.external_dependencies.values():
            all_external.update(ext)
        print(f"   📦 Dépendances externes uniques : {len(all_external)}")
        
        return self.dependencies
    
    def get_external_dependencies(self) -> Dict[str, Set[str]]:
        """Retourne les dépendances externes par module"""
        return self.external_dependencies
    
    def get_all_external_dependencies(self) -> Set[str]:
        """Retourne toutes les dépendances externes uniques"""
        all_external = set()
        for ext in self.external_dependencies.values():
            all_external.update(ext)
        return all_external
