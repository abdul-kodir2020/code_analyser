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
        
        for file_path in python_files:
            module_name = str(file_path.relative_to(self.project_path))
            imports = self.parse_file(file_path)
            self.dependencies[module_name] = imports
            
            # Debug : afficher les premiers fichiers avec imports
            if imports and len(self.dependencies) <= 3:
                print(f"      {module_name}: {list(imports)[:3]}")
        
        return self.dependencies
