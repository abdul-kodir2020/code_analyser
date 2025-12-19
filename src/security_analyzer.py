"""
Analyseur de sécurité - Détection de fonctions dangereuses
Identifie les patterns de code risqués et vulnérabilités potentielles
"""

import ast
from typing import Dict, List, Set, Tuple
from pathlib import Path


# Base de données des fonctions dangereuses
DANGEROUS_FUNCTIONS = {
    'eval': '🔴 CRITIQUE - Exécution de code arbitraire (RCE)',
    'exec': '🔴 CRITIQUE - Exécution de code arbitraire (RCE)',
    'compile': '🟠 ÉLEVÉ - Compilation de code dynamique',
    '__import__': '🟠 ÉLEVÉ - Import dynamique non contrôlé',
    'pickle.loads': '🔴 CRITIQUE - Désérialisation non sécurisée',
    'pickle.load': '🔴 CRITIQUE - Désérialisation non sécurisée',
    'yaml.load': '🔴 CRITIQUE - YAML deserialization (utilisez safe_load)',
    'os.system': '🔴 CRITIQUE - Injection de commandes',
    'os.popen': '🔴 CRITIQUE - Injection de commandes',
    'subprocess.call': '🟠 ÉLEVÉ - Risque si shell=True',
    'subprocess.run': '🟠 ÉLEVÉ - Risque si shell=True',
    'subprocess.Popen': '🟠 ÉLEVÉ - Risque si shell=True',
    'input': '🟡 MOYEN - Entrée utilisateur non validée',
}

DANGEROUS_MODULES = {
    'pickle': 'Désérialisation dangereuse',
    'marshal': 'Désérialisation dangereuse',
    'shelve': 'Stockage non sécurisé',
}

# Patterns SQL injection
SQL_EXECUTION_FUNCTIONS = {
    'execute': 'Exécution SQL - Risque d\'injection',
    'executemany': 'Exécution SQL - Risque d\'injection',
    'executescript': 'Exécution SQL - Risque d\'injection',
}


class SecurityAnalyzer:
    """Analyse les fichiers Python pour détecter les vulnérabilités"""
    
    def __init__(self):
        """Initialise l'analyseur de sécurité"""
        self.vulnerabilities: Dict[str, List[Dict]] = {}
        self.dangerous_modules: Dict[str, Set[str]] = {}
    
    def analyze_file(self, file_path: Path, module_name: str) -> List[Dict]:
        """
        Analyse un fichier pour détecter les fonctions dangereuses
        
        Args:
            file_path: Chemin du fichier à analyser
            module_name: Nom du module
            
        Returns:
            Liste des vulnérabilités détectées
        """
        vulnerabilities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            
            # Analyser les appels de fonction
            for node in ast.walk(tree):
                # Détection d'appels de fonctions
                if isinstance(node, ast.Call):
                    vuln = self._check_function_call(node, module_name)
                    if vuln:
                        vulnerabilities.append(vuln)
                
                # Détection d'imports dangereux
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in DANGEROUS_MODULES:
                            vulnerabilities.append({
                                'type': 'dangerous_import',
                                'module': module_name,
                                'line': node.lineno,
                                'function': alias.name,
                                'severity': '🟠 ÉLEVÉ',
                                'description': f'Import de module dangereux: {DANGEROUS_MODULES[alias.name]}'
                            })
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module in DANGEROUS_MODULES:
                        vulnerabilities.append({
                            'type': 'dangerous_import',
                            'module': module_name,
                            'line': node.lineno,
                            'function': node.module,
                            'severity': '🟠 ÉLEVÉ',
                            'description': f'Import de module dangereux: {DANGEROUS_MODULES[node.module]}'
                        })
        
        except Exception as e:
            pass
        
        if vulnerabilities:
            self.vulnerabilities[module_name] = vulnerabilities
            
            # Marquer le module comme dangereux
            dangerous_funcs = set()
            for vuln in vulnerabilities:
                dangerous_funcs.add(vuln['function'])
            self.dangerous_modules[module_name] = dangerous_funcs
        
        return vulnerabilities
    
    def _check_function_call(self, node: ast.Call, module_name: str) -> dict:
        """Vérifie si un appel de fonction est dangereux"""
        func_name = self._get_function_name(node)
        
        if not func_name:
            return None
        
        # Vérifier les fonctions dangereuses
        if func_name in DANGEROUS_FUNCTIONS:
            return {
                'type': 'dangerous_function',
                'module': module_name,
                'line': node.lineno,
                'function': func_name,
                'severity': self._get_severity(DANGEROUS_FUNCTIONS[func_name]),
                'description': DANGEROUS_FUNCTIONS[func_name]
            }
        
        # Vérifier les fonctions SQL
        simple_name = func_name.split('.')[-1]
        if simple_name in SQL_EXECUTION_FUNCTIONS:
            # Vérifier si c'est une f-string ou concaténation (signe d'injection)
            if self._has_string_formatting(node):
                return {
                    'type': 'sql_injection',
                    'module': module_name,
                    'line': node.lineno,
                    'function': func_name,
                    'severity': '🔴 CRITIQUE',
                    'description': f'Risque d\'injection SQL - Utilisation de formatage de chaîne avec {simple_name}'
                }
        
        # Vérifier subprocess avec shell=True
        if 'subprocess' in func_name:
            if self._has_shell_true(node):
                return {
                    'type': 'command_injection',
                    'module': module_name,
                    'line': node.lineno,
                    'function': func_name,
                    'severity': '🔴 CRITIQUE',
                    'description': 'subprocess avec shell=True - Risque d\'injection de commande'
                }
        
        return None
    
    def _get_function_name(self, node: ast.Call) -> str:
        """Extrait le nom complet d'une fonction"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return None
    
    def _get_severity(self, description: str) -> str:
        """Extrait le niveau de sévérité de la description"""
        if '🔴' in description:
            return '🔴 CRITIQUE'
        elif '🟠' in description:
            return '🟠 ÉLEVÉ'
        elif '🟡' in description:
            return '🟡 MOYEN'
        return '🟢 FAIBLE'
    
    def _has_string_formatting(self, node: ast.Call) -> bool:
        """Détecte si l'appel utilise du formatage de chaîne"""
        for arg in node.args:
            if isinstance(arg, ast.JoinedStr):  # f-string
                return True
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):  # % formatting
                return True
            if isinstance(arg, ast.Call):
                func_name = self._get_function_name(arg)
                if func_name and 'format' in func_name:  # .format()
                    return True
        return False
    
    def _has_shell_true(self, node: ast.Call) -> bool:
        """Détecte si subprocess est appelé avec shell=True"""
        for keyword in node.keywords:
            if keyword.arg == 'shell':
                if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                    return True
                if isinstance(keyword.value, ast.NameConstant) and keyword.value.value is True:
                    return True
        return False
    
    def get_summary(self) -> Dict:
        """Retourne un résumé des vulnérabilités"""
        total = sum(len(vulns) for vulns in self.vulnerabilities.values())
        
        by_severity = {'CRITIQUE': 0, 'ÉLEVÉ': 0, 'MOYEN': 0, 'FAIBLE': 0}
        by_type = {}
        
        for vulns in self.vulnerabilities.values():
            for vuln in vulns:
                # Compter par sévérité
                if 'CRITIQUE' in vuln['severity']:
                    by_severity['CRITIQUE'] += 1
                elif 'ÉLEVÉ' in vuln['severity']:
                    by_severity['ÉLEVÉ'] += 1
                elif 'MOYEN' in vuln['severity']:
                    by_severity['MOYEN'] += 1
                else:
                    by_severity['FAIBLE'] += 1
                
                # Compter par type
                vuln_type = vuln['type']
                by_type[vuln_type] = by_type.get(vuln_type, 0) + 1
        
        return {
            'total': total,
            'by_severity': by_severity,
            'by_type': by_type,
            'dangerous_modules_count': len(self.dangerous_modules)
        }
    
    def is_module_dangerous(self, module_name: str) -> bool:
        """Vérifie si un module contient des fonctions dangereuses"""
        return module_name in self.dangerous_modules
    
    def get_module_vulnerabilities(self, module_name: str) -> List[Dict]:
        """Retourne les vulnérabilités d'un module spécifique"""
        return self.vulnerabilities.get(module_name, [])
    
    def get_all_vulnerabilities(self) -> List[Dict]:
        """Retourne toutes les vulnérabilités détectées"""
        all_vulns = []
        for module_vulns in self.vulnerabilities.values():
            all_vulns.extend(module_vulns)
        return all_vulns
