"""
Comparateur d'analyses - Compare deux analyses pour détecter les différences
"""

class AnalysisComparer:
    """Compare deux analyses et génère un rapport de différences"""
    
    def __init__(self, analysis1_data, analysis2_data):
        """
        Args:
            analysis1_data: Données de la première analyse (ancienne)
            analysis2_data: Données de la deuxième analyse (nouvelle)
        """
        self.old = analysis1_data
        self.new = analysis2_data
    
    def compare(self):
        """Effectue la comparaison complète et retourne un rapport"""
        return {
            'summary': self._compare_summary(),
            'structure': self._compare_structure(),
            'security': self._compare_security(),
            'metrics': self._compare_metrics(),
            'attack_surface': self._compare_attack_surface()
        }
    
    def _compare_summary(self):
        """Compare les statistiques globales"""
        old_graph = self.old.get('graph_info', {})
        new_graph = self.new.get('graph_info', {})
        
        old_security = self.old.get('security_summary', {})
        new_security = self.new.get('security_summary', {})
        
        # Utiliser le nombre réel de vulnérabilités depuis le tableau plutôt que la DB
        old_vulns_count = len(self.old.get('vulnerabilities', []))
        new_vulns_count = len(self.new.get('vulnerabilities', []))
        
        # Si le tableau est vide, utiliser le total de la DB (fallback)
        if old_vulns_count == 0:
            old_vulns_count = old_security.get('total', 0)
        if new_vulns_count == 0:
            new_vulns_count = new_security.get('total', 0)
        
        modules_delta = new_graph.get('nodes', 0) - old_graph.get('nodes', 0)
        deps_delta = new_graph.get('edges', 0) - old_graph.get('edges', 0)
        cycles_delta = new_graph.get('cycles', 0) - old_graph.get('cycles', 0)
        vulns_delta = new_vulns_count - old_vulns_count
        
        return {
            'modules': {
                'old': old_graph.get('nodes', 0),
                'new': new_graph.get('nodes', 0),
                'delta': modules_delta
            },
            'dependencies': {
                'old': old_graph.get('edges', 0),
                'new': new_graph.get('edges', 0),
                'delta': deps_delta
            },
            'cycles': {
                'old': old_graph.get('cycles', 0),
                'new': new_graph.get('cycles', 0),
                'delta': cycles_delta,
                'trend': 'improvement' if cycles_delta < 0 else ('regression' if cycles_delta > 0 else 'stable')
            },
            'vulnerabilities': {
                'old': old_vulns_count,
                'new': new_vulns_count,
                'delta': vulns_delta,
                'trend': 'improvement' if vulns_delta < 0 else ('regression' if vulns_delta > 0 else 'stable')
            }
        }
    
    def _compare_structure(self):
        """Compare la structure du graphe"""
        old_nodes = set(self.old.get('modules', []))
        new_nodes = set(self.new.get('modules', []))
        
        added = list(new_nodes - old_nodes)
        removed = list(old_nodes - new_nodes)
        common = list(old_nodes & new_nodes)
        
        return {
            'modules_added': sorted(added),
            'modules_removed': sorted(removed),
            'modules_common': sorted(common),
            'total_added': len(added),
            'total_removed': len(removed)
        }
    
    def _compare_security(self):
        """Compare les vulnérabilités"""
        old_vulns = self.old.get('vulnerabilities', [])
        new_vulns = self.new.get('vulnerabilities', [])
        
        # Créer des clés uniques pour chaque vulnérabilité (module + ligne + type)
        def vuln_key(v):
            return f"{v.get('module', '')}:{v.get('line', 0)}:{v.get('type', '')}"
        
        old_vuln_dict = {vuln_key(v): v for v in old_vulns}
        new_vuln_dict = {vuln_key(v): v for v in new_vulns}
        
        old_keys = set(old_vuln_dict.keys())
        new_keys = set(new_vuln_dict.keys())
        
        fixed_keys = old_keys - new_keys
        new_keys_only = new_keys - old_keys
        
        fixed = [old_vuln_dict[k] for k in fixed_keys]
        new_issues = [new_vuln_dict[k] for k in new_keys_only]
        
        # Compter par sévérité
        def count_by_severity(vulns):
            counts = {'CRITIQUE': 0, 'ÉLEVÉ': 0, 'MOYEN': 0}
            for v in vulns:
                severity = v.get('severity', 'MOYEN')
                if 'CRITIQUE' in severity:
                    counts['CRITIQUE'] += 1
                elif 'ÉLEVÉ' in severity:
                    counts['ÉLEVÉ'] += 1
                else:
                    counts['MOYEN'] += 1
            return counts
        
        return {
            'fixed': fixed,
            'new': new_issues,
            'total_fixed': len(fixed),
            'total_new': len(new_issues),
            'fixed_by_severity': count_by_severity(fixed),
            'new_by_severity': count_by_severity(new_issues),
            'critical_regression': any('CRITIQUE' in v.get('severity', '') for v in new_issues)
        }
    
    def _compare_metrics(self):
        """Compare les métriques du graphe"""
        old_metrics = self.old.get('top_modules', {})
        new_metrics = self.new.get('top_modules', {})
        
        # Comparer les modules les plus centraux
        old_top = set([m[0] for m in old_metrics.get('degree_centrality', [])[:5]])
        new_top = set([m[0] for m in new_metrics.get('degree_centrality', [])[:5]])
        
        return {
            'top_modules_changed': old_top != new_top,
            'new_critical_modules': list(new_top - old_top),
            'less_critical_modules': list(old_top - new_top)
        }
    
    def _compare_attack_surface(self):
        """Compare la surface d'attaque"""
        old_surface = self.old.get('attack_surface_summary', {})
        new_surface = self.new.get('attack_surface_summary', {})
        
        old_entries = old_surface.get('total_entry_points', 0)
        new_entries = new_surface.get('total_entry_points', 0)
        
        old_critical = old_surface.get('critical_paths', 0)
        new_critical = new_surface.get('critical_paths', 0)
        
        return {
            'entry_points': {
                'old': old_entries,
                'new': new_entries,
                'delta': new_entries - old_entries
            },
            'critical_paths': {
                'old': old_critical,
                'new': new_critical,
                'delta': new_critical - old_critical,
                'trend': 'improvement' if new_critical < old_critical else ('regression' if new_critical > old_critical else 'stable')
            }
        }
    
    def get_recommendations(self):
        """Génère des recommandations basées sur la comparaison"""
        comparison = self.compare()
        recommendations = []
        
        # Vérifier les vulnérabilités
        security = comparison['security']
        if security['total_new'] == 0 and security['total_fixed'] > 0:
            recommendations.append({
                'type': 'success',
                'message': f"Excellent ! {security['total_fixed']} vulnérabilité(s) corrigée(s) sans régression."
            })
        elif security['critical_regression']:
            recommendations.append({
                'type': 'critical',
                'message': f"ALERTE : {security['new_by_severity']['CRITIQUE']} nouvelle(s) vulnérabilité(s) CRITIQUE(S) introduite(s) !"
            })
        elif security['total_new'] > 0:
            recommendations.append({
                'type': 'warning',
                'message': f"Attention : {security['total_new']} nouvelle(s) vulnérabilité(s) détectée(s)."
            })
        
        # Vérifier les cycles
        cycles = comparison['summary']['cycles']
        if cycles['trend'] == 'improvement':
            recommendations.append({
                'type': 'success',
                'message': f"Architecture améliorée : {abs(cycles['delta'])} cycle(s) de dépendances résolu(s)."
            })
        elif cycles['trend'] == 'regression':
            recommendations.append({
                'type': 'warning',
                'message': f"Attention : {cycles['delta']} nouveau(x) cycle(s) de dépendances introduit(s)."
            })
        
        # Vérifier la surface d'attaque
        attack = comparison['attack_surface']
        if attack['critical_paths']['trend'] == 'improvement':
            recommendations.append({
                'type': 'success',
                'message': "Surface d'attaque réduite : moins de chemins critiques."
            })
        elif attack['critical_paths']['trend'] == 'regression':
            recommendations.append({
                'type': 'warning',
                'message': "Surface d'attaque augmentée : nouveaux chemins critiques détectés."
            })
        
        # Vérifier la complexité
        structure = comparison['structure']
        if structure['total_added'] > structure['total_removed'] + 5:
            recommendations.append({
                'type': 'info',
                'message': f"Le projet s'agrandit rapidement (+{structure['total_added']} modules). Pensez à la modularisation."
            })
        
        return recommendations
