"""
Extension du générateur HTML pour la section Attack Surface
"""


def generate_attack_surface_section(attack_surface_analyzer) -> str:
    """
    Génère la section HTML pour l'analyse de surface d'attaque
    
    Args:
        attack_surface_analyzer: Instance de AttackSurfaceAnalyzer
    
    Returns:
        HTML de la section
    """
    if not attack_surface_analyzer or not attack_surface_analyzer.entry_points:
        return ""
    
    summary = attack_surface_analyzer.get_summary()
    top_risks = attack_surface_analyzer.get_top_risks(10)
    
    # Cards statistiques
    stats_html = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
        <div class="stat-card">
            <h3>Points d'Entrée</h3>
            <div class="value">{summary['total_entry_points']}</div>
        </div>
        <div class="stat-card">
            <h3>Modules Exposés</h3>
            <div class="value">{summary['entry_modules']}</div>
        </div>
        <div class="stat-card warning">
            <h3>Chemins Critiques</h3>
            <div class="value">{summary['critical_paths']}</div>
        </div>
        <div class="stat-card danger">
            <h3>Risque CRITIQUE</h3>
            <div class="value">{summary['by_risk']['CRITIQUE']}</div>
        </div>
    </div>
    """
    
    # Liste des points d'entrée
    entry_points_html = "<h3 style='margin-top: 30px;'>🌐 Points d'Entrée Détectés</h3>"
    entry_points_html += "<div style='margin: 20px 0;'>"
    
    for module, entries in attack_surface_analyzer.entry_points.items():
        entry_points_html += f"""
        <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; margin-bottom: 15px; border-radius: 4px;">
            <div style="font-weight: bold; color: #333; margin-bottom: 8px;">📁 {module}</div>
            <div style="margin-left: 15px;">
        """
        
        for entry in entries:
            path = entry.get('path', 'N/A')
            methods = ', '.join(entry.get('methods', [])) if entry.get('methods') else 'ALL'
            entry_points_html += f"""
                <div style="color: #666; font-size: 0.9em; margin: 5px 0;">
                    <span style="background: #667eea; color: white; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.85em;">{entry['type']}</span>
                    <code style="background: white; padding: 3px 6px; border-radius: 3px; margin: 0 5px;">{entry['function']}()</code>
                    <span style="color: #999;">→</span> {path}
                    <span style="color: #999; font-size: 0.85em;">[{methods}]</span>
                </div>
            """
        
        entry_points_html += "</div></div>"
    
    entry_points_html += "</div>"
    
    # Tableau des chemins à risque
    risk_table_html = "<h3 style='margin-top: 30px;'>⚠️ Chemins à Risque</h3>"
    
    if not top_risks:
        risk_table_html += "<p style='color: #666;'>Aucun chemin critique détecté.</p>"
    else:
        risk_table_html += """
        <table style="width: 100%; border-collapse: collapse; margin-top: 15px; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    <th style="padding: 12px; text-align: left;">Niveau</th>
                    <th style="padding: 12px; text-align: left;">Point d'Entrée</th>
                    <th style="padding: 12px; text-align: left;">Route</th>
                    <th style="padding: 12px; text-align: left;">Module Cible</th>
                    <th style="padding: 12px; text-align: center;">Distance</th>
                    <th style="padding: 12px; text-align: center;">Centralité</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for i, risk in enumerate(top_risks):
            # Couleur selon le risque
            risk_colors = {
                'CRITIQUE': '#dc2626',
                'ÉLEVÉ': '#f59e0b',
                'MOYEN': '#eab308',
                'FAIBLE': '#10b981'
            }
            color = risk_colors.get(risk['risk_level'], '#999')
            bg_color = '#fff5f5' if risk['risk_level'] == 'CRITIQUE' else '#fffbeb' if risk['risk_level'] == 'ÉLEVÉ' else 'white'
            
            risk_table_html += f"""
                <tr style="background: {bg_color}; border-bottom: 1px solid #e5e7eb;">
                    <td style="padding: 12px;">
                        <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 0.85em;">
                            {risk['risk_level']}
                        </span>
                    </td>
                    <td style="padding: 12px; font-family: monospace; font-size: 0.85em; color: #333;">
                        {risk['entry_function']}()
                    </td>
                    <td style="padding: 12px; color: #666; font-size: 0.9em;">
                        {risk['entry_path']}
                    </td>
                    <td style="padding: 12px; font-family: monospace; font-size: 0.85em; color: #667eea;">
                        {risk['target_module']}
                    </td>
                    <td style="padding: 12px; text-align: center; font-weight: bold;">
                        {risk['distance']} sauts
                    </td>
                    <td style="padding: 12px; text-align: center;">
                        {risk['centrality']:.3f}
                    </td>
                </tr>
            """
        
        risk_table_html += """
            </tbody>
        </table>
        """
    
    # Explication
    explanation = """
    <div class="alert alert-info" style="margin-top: 30px; background: #e0f2fe; border-left: 4px solid #0284c7; padding: 20px; border-radius: 4px;">
        <h4 style="margin-bottom: 10px; color: #0369a1;">📘 Qu'est-ce que l'Attack Surface ?</h4>
        <p style="color: #075985; line-height: 1.6;">
            La <strong>surface d'attaque</strong> représente tous les points par lesquels un attaquant pourrait compromettre votre système.
            Cette analyse identifie :
        </p>
        <ul style="color: #075985; margin-top: 10px; line-height: 1.8;">
            <li><strong>Points d'entrée</strong> : Routes HTTP, API endpoints, fonctions publiques accessibles depuis l'extérieur</li>
            <li><strong>Distance</strong> : Nombre de sauts entre un point d'entrée et un module critique</li>
            <li><strong>Centralité</strong> : Importance du module dans l'architecture (plus haute = plus critique)</li>
            <li><strong>Risque</strong> : Combinaison de la proximité et de l'importance (proche + central = risqué)</li>
        </ul>
        <p style="color: #075985; margin-top: 15px; font-style: italic;">
            ⚠️ Un chemin CRITIQUE signifie qu'un module très important est accessible en peu de sauts depuis l'extérieur.
        </p>
    </div>
    """
    
    # Section complète
    return f"""
    <div class="section" style="background: white; padding: 30px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
        <h2 style="color: #333; border-bottom: 3px solid #667eea; padding-bottom: 15px; margin-bottom: 30px;">
            🎯 Attack Surface Mapping
        </h2>
        
        {stats_html}
        {entry_points_html}
        {risk_table_html}
        {explanation}
    </div>
    """
