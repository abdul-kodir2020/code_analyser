from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import threading
import subprocess
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Configuration
DATABASE = 'analyses.db'
REPORTS_DIR = Path('web_reports')
REPORTS_DIR.mkdir(exist_ok=True)

# Agent IA (lazy loading - sera initialisé au premier appel)
_ai_advisor = None

def get_ai_advisor():
    """Retourne l'agent IA (lazy loading)"""
    global _ai_advisor
    if _ai_advisor is None:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.ai_advisor import AIAdvisor
        _ai_advisor = AIAdvisor(provider="auto")
    return _ai_advisor

def init_db():
    """Initialise la base de données"""
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            repo_url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            total_modules INTEGER,
            total_dependencies INTEGER,
            vulnerabilities_critical INTEGER DEFAULT 0,
            vulnerabilities_high INTEGER DEFAULT 0,
            vulnerabilities_medium INTEGER DEFAULT 0,
            attack_surface_points INTEGER DEFAULT 0,
            report_path TEXT,
            error_message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    """Connexion à la base de données"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def run_analysis(analysis_id, repo_url):
    """Exécute l'analyse en arrière-plan"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        print(f"🔄 Démarrage de l'analyse {analysis_id} pour {repo_url}")
        
        # Mettre à jour le statut
        c.execute('UPDATE analyses SET status = ? WHERE id = ?', ('running', analysis_id))
        conn.commit()
        
        # Créer un dossier pour cette analyse
        analysis_dir = REPORTS_DIR / f'analysis_{analysis_id}'
        analysis_dir.mkdir(exist_ok=True)
        print(f"📁 Dossier créé: {analysis_dir}")
        
        # Chemin vers le script main.py (un niveau au-dessus de web_ui)
        main_script = Path(__file__).parent.parent / 'main.py'
        project_root = Path(__file__).parent.parent
        
        print(f"🐍 Script: {main_script}")
        print(f"📂 Workdir: {project_root}")
        
        if not main_script.exists():
            raise FileNotFoundError(f"Script main.py introuvable: {main_script}")
        
        # Lancer l'analyse
        print(f"▶️  Lancement: python3 {main_script} {repo_url}")
        
        # Utiliser Popen pour voir la progression en temps réel
        process = subprocess.Popen(
            ['python3', str(main_script), repo_url],
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Attendre avec un timeout
        try:
            stdout, stderr = process.communicate(timeout=1200)  # 20 minutes max pour gros projets
            result_returncode = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise subprocess.TimeoutExpired(process.args, 1200)
        
        print(f"✅ Analyse terminée avec code: {result_returncode}")
        
        if result_returncode == 0:
            # Déplacer les fichiers générés
            files_moved = []
            for file in ['report.html', 'output_graph_simple.png', 'output_graph_metrics.png', 'graph_interactive.html']:
                src = project_root / file
                if src.exists():
                    dst = analysis_dir / file
                    src.rename(dst)
                    files_moved.append(file)
                    print(f"📦 Déplacé: {file}")
            
            if not files_moved:
                raise Exception("Aucun fichier généré par l'analyse")
            
            # Extraire les métriques du rapport si possible
            report_path = analysis_dir / 'report.html'
            
            # Parser les résultats (basique - on pourrait améliorer)
            modules = 0
            deps = 0
            vuln_critical = 0
            vuln_high = 0
            vuln_medium = 0
            attack_points = 0
            
            # Lire le rapport HTML pour extraire les stats de sécurité
            if report_path.exists():
                try:
                    with open(report_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extraire les vulnérabilités depuis le JSON
                    match = re.search(r'<script id="ai-issues" type="application/json">\s*(.*?)\s*</script>', content, re.DOTALL)
                    if match:
                        issues_json = match.group(1).strip()
                        if issues_json:
                            vulnerabilities = json.loads(issues_json)
                            print(f"📊 Extraction: {len(vulnerabilities)} vulnérabilités trouvées dans le rapport")
                            for vuln in vulnerabilities:
                                severity = vuln.get('severity', '')
                                if severity == 'CRITIQUE':
                                    vuln_critical += 1
                                elif severity == 'ÉLEVÉ':
                                    vuln_high += 1
                                elif severity == 'MOYEN':
                                    vuln_medium += 1
                            print(f"📊 Vulnérabilités par sévérité: {vuln_critical} critiques, {vuln_high} élevées, {vuln_medium} moyennes")
                        else:
                            print(f"⚠️  Script ai-issues trouvé mais vide")
                    else:
                        print(f"⚠️  Script ai-issues non trouvé dans le rapport")
                    
                    # Extraire les points d'attaque (optionnel - pattern basique)
                    attack_match = re.search(r'Points d\'entrée.*?(\d+)', content, re.IGNORECASE)
                    if attack_match:
                        attack_points = int(attack_match.group(1))
                        
                except Exception as e:
                    print(f"⚠️  Erreur extraction stats: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"⚠️  Rapport introuvable: {report_path}")
            
            # Extraction basique des métriques depuis stdout
            for line in stdout.split('\n'):
                if 'Nœuds (modules)' in line:
                    try:
                        modules = int(line.split(':')[1].strip())
                    except:
                        pass
                if 'Arêtes (dépendances)' in line:
                    try:
                        deps = int(line.split(':')[1].strip())
                    except:
                        pass
            
            c.execute('''
                UPDATE analyses 
                SET status = ?, completed_at = ?, total_modules = ?, total_dependencies = ?, report_path = ?,
                    vulnerabilities_critical = ?, vulnerabilities_high = ?, vulnerabilities_medium = ?,
                    attack_surface_points = ?
                WHERE id = ?
            ''', ('completed', datetime.now(), modules, deps, str(report_path), 
                  vuln_critical, vuln_high, vuln_medium, attack_points, analysis_id))
            print(f"✅ Analyse {analysis_id} terminée avec succès")
        else:
            error_msg = stderr[:500] if stderr else "Erreur inconnue"
            print(f"❌ Erreur analyse {analysis_id}: {error_msg}")
            c.execute('''
                UPDATE analyses 
                SET status = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            ''', ('failed', datetime.now(), error_msg, analysis_id))
        
        conn.commit()
    
    except subprocess.TimeoutExpired:
        error_msg = 'Timeout: analyse trop longue (>20min)'
        print(f"⏱️  {error_msg}")
        c.execute('''
            UPDATE analyses 
            SET status = ?, error_message = ?
            WHERE id = ?
        ''', ('failed', error_msg, analysis_id))
        conn.commit()
    
    except Exception as e:
        error_msg = str(e)[:500]
        print(f"💥 Erreur analyse {analysis_id}: {error_msg}")
        import traceback
        traceback.print_exc()
        c.execute('''
            UPDATE analyses 
            SET status = ?, error_message = ?
            WHERE id = ?
        ''', ('failed', error_msg, analysis_id))
        conn.commit()
    
    finally:
        conn.close()

@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@app.route('/history')
def history():
    """Historique des analyses"""
    conn = get_db()
    c = conn.cursor()
    analyses = c.execute('''
        SELECT * FROM analyses 
        ORDER BY created_at DESC 
        LIMIT 50
    ''').fetchall()
    conn.close()
    
    return render_template('history.html', analyses=analyses)

@app.route('/analysis/<int:analysis_id>')
def view_analysis(analysis_id):
    """Voir les détails d'une analyse"""
    conn = get_db()
    c = conn.cursor()
    analysis = c.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    
    if not analysis:
        return "Analyse non trouvée", 404
    
    return render_template('analysis.html', analysis=analysis)

@app.route('/analysis/<int:analysis_id>/ai-suggestions')
def view_ai_suggestions(analysis_id):
    """Voir les suggestions IA pour une analyse"""
    conn = get_db()
    c = conn.cursor()
    analysis = c.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    
    if not analysis:
        return "Analyse non trouvée", 404
    
    return render_template('ai_suggestions.html', analysis=analysis)

@app.route('/api/analysis/<int:analysis_id>/issues')
def get_analysis_issues(analysis_id):
    """Récupère tous les problèmes (vulnérabilités + cycles) d'une analyse"""
    conn = get_db()
    c = conn.cursor()
    analysis = c.execute('SELECT report_path FROM analyses WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    
    if not analysis or not analysis['report_path']:
        return jsonify({'error': 'Analyse non trouvée'}), 404
    
    # Charger le rapport HTML et extraire les problèmes
    report_path = Path(analysis['report_path'])
    if not report_path.exists():
        return jsonify({'error': 'Rapport introuvable'}), 404
    
    try:
        # Lire le rapport HTML
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire le script JSON (si présent dans le rapport)
        # Chercher le script ai-issues dans le HTML
        match = re.search(r'<script id="ai-issues" type="application/json">\s*(.*?)\s*</script>', content, re.DOTALL)
        
        if match:
            issues_json = match.group(1)
            issues = json.loads(issues_json)
            return jsonify({'issues': issues})
        else:
            # Si pas de script, retourner vide
            return jsonify({'issues': []})
    
    except Exception as e:
        print(f"Erreur lors du chargement des problèmes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/compare')
def compare_page():
    """Page de comparaison entre deux analyses"""
    conn = get_db()
    c = conn.cursor()
    # Récupérer toutes les analyses complétées pour la sélection
    analyses = c.execute('''
        SELECT id, project_name, repo_url, created_at, total_modules, vulnerabilities_critical
        FROM analyses 
        WHERE status = 'completed'
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('compare.html', analyses=analyses)

@app.route('/api/compare')
def api_compare():
    """API pour comparer deux analyses"""
    analysis1_id = request.args.get('analysis1', type=int)
    analysis2_id = request.args.get('analysis2', type=int)
    
    if not analysis1_id or not analysis2_id:
        return jsonify({'error': 'Deux IDs d\'analyses requis'}), 400
    
    if analysis1_id == analysis2_id:
        return jsonify({'error': 'Les deux analyses doivent être différentes'}), 400
    
    try:
        # Charger les données des deux analyses
        analysis1_data = _load_analysis_data(analysis1_id)
        analysis2_data = _load_analysis_data(analysis2_id)
        
        if not analysis1_data or not analysis2_data:
            return jsonify({'error': 'Analyse introuvable'}), 404
        
        # Comparer
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.comparer import AnalysisComparer
        
        comparer = AnalysisComparer(analysis1_data, analysis2_data)
        comparison = comparer.compare()
        recommendations = comparer.get_recommendations()
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'recommendations': recommendations
        })
    
    except Exception as e:
        print(f"Erreur lors de la comparaison: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def _load_analysis_data(analysis_id):
    """Charge les données d'une analyse depuis la DB et le rapport"""
    conn = get_db()
    c = conn.cursor()
    analysis = c.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    
    if not analysis or analysis['status'] != 'completed':
        print(f"Analyse {analysis_id} introuvable ou non complétée")
        return None
    
    # Charger les données depuis le rapport HTML
    report_path = Path(analysis['report_path'])
    if not report_path.exists():
        print(f"Rapport introuvable : {report_path}")
        return None
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraire les vulnérabilités depuis le JSON
        vulnerabilities = []
        match = re.search(r'<script id="ai-issues" type="application/json">\s*(.*?)\s*</script>', content, re.DOTALL)
        if match:
            issues_json = match.group(1).strip()
            if issues_json:
                try:
                    vulnerabilities = json.loads(issues_json)
                    print(f"Analyse {analysis_id} : {len(vulnerabilities)} vulnérabilités chargées depuis JSON")
                except json.JSONDecodeError as e:
                    print(f"Erreur JSON pour analyse {analysis_id}: {e}")
        else:
            print(f"Pas de script ai-issues trouvé dans le rapport {analysis_id}")
        
        # Calculer le total de vulnérabilités
        total_vulns = (analysis['vulnerabilities_critical'] or 0) + \
                     (analysis['vulnerabilities_high'] or 0) + \
                     (analysis['vulnerabilities_medium'] or 0)
        
        print(f"Analyse {analysis_id} - Total vulns DB: {total_vulns}, JSON: {len(vulnerabilities)}")
        
        # Extraire les modules (depuis les nœuds du graphe si disponible)
        modules = []
        # TODO: Extraire depuis le graphe si nécessaire
        
        data = {
            'id': analysis['id'],
            'project_name': analysis['project_name'],
            'created_at': analysis['created_at'],
            'graph_info': {
                'nodes': analysis['total_modules'] or 0,
                'edges': analysis['total_dependencies'] or 0,
                'cycles': 0  # TODO: extraire depuis le rapport
            },
            'security_summary': {
                'total': total_vulns,
                'by_severity': {
                    'CRITIQUE': analysis['vulnerabilities_critical'] or 0,
                    'ÉLEVÉ': analysis['vulnerabilities_high'] or 0,
                    'MOYEN': analysis['vulnerabilities_medium'] or 0
                }
            },
            'vulnerabilities': vulnerabilities,
            'modules': modules,
            'top_modules': {},
            'attack_surface_summary': {
                'total_entry_points': analysis['attack_surface_points'] or 0,
                'critical_paths': 0  # TODO: extraire si disponible
            }
        }
        
        print(f"Données chargées pour analyse {analysis_id}: {len(vulnerabilities)} vulns")
        return data
    
    except Exception as e:
        print(f"Erreur lors du chargement de l'analyse {analysis_id}: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/api/start-analysis', methods=['POST'])
def start_analysis():
    """API pour démarrer une nouvelle analyse"""
    data = request.get_json()
    repo_url = data.get('repo_url', '').strip()
    
    if not repo_url:
        return jsonify({'error': 'URL du repository requise'}), 400
    
    # Extraire le nom du projet depuis l'URL
    project_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
    
    # Créer l'entrée dans la base de données
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO analyses (project_name, repo_url, status)
        VALUES (?, ?, ?)
    ''', (project_name, repo_url, 'pending'))
    analysis_id = c.lastrowid
    conn.commit()
    conn.close()
    
    # Lancer l'analyse en arrière-plan
    thread = threading.Thread(target=run_analysis, args=(analysis_id, repo_url))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'message': 'Analyse démarrée'
    })

@app.route('/api/analysis-status/<int:analysis_id>')
def analysis_status(analysis_id):
    """Obtenir le statut d'une analyse"""
    conn = get_db()
    c = conn.cursor()
    analysis = c.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    
    if not analysis:
        return jsonify({'error': 'Analyse non trouvée'}), 404
    
    return jsonify({
        'id': analysis['id'],
        'project_name': analysis['project_name'],
        'status': analysis['status'],
        'created_at': analysis['created_at'],
        'completed_at': analysis['completed_at'],
        'error_message': analysis['error_message']
    })

@app.route('/api/delete-analysis/<int:analysis_id>', methods=['DELETE'])
def delete_analysis(analysis_id):
    """Supprimer une analyse"""
    import shutil
    
    conn = get_db()
    c = conn.cursor()
    
    # Supprimer le dossier web_reports/analysis_X
    analysis_dir = REPORTS_DIR / f'analysis_{analysis_id}'
    if analysis_dir.exists():
        try:
            shutil.rmtree(analysis_dir)
            print(f"✅ Dossier supprimé : {analysis_dir}")
        except Exception as e:
            print(f"⚠️ Erreur suppression dossier : {e}")
    
    # Supprimer de la base de données
    c.execute('DELETE FROM analyses WHERE id = ?', (analysis_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/analysis/<int:analysis_id>/file/<filename>')
def serve_analysis_file(analysis_id, filename):
    """Servir les fichiers statiques d'une analyse (images, graphes)"""
    from flask import send_file
    
    # Sécurité: vérifier que le fichier est autorisé
    allowed_files = ['output_graph_simple.png', 'output_graph_metrics.png', 'graph_interactive.html']
    if filename not in allowed_files:
        return "Fichier non autorisé", 403
    
    analysis_dir = REPORTS_DIR / f'analysis_{analysis_id}'
    file_path = analysis_dir / filename
    
    if not file_path.exists():
        return "Fichier non trouvé", 404
    
    return send_file(file_path)

@app.route('/report/<int:analysis_id>')
def serve_report(analysis_id):
    """Servir le rapport HTML d'une analyse"""
    conn = get_db()
    c = conn.cursor()
    analysis = c.execute('SELECT report_path FROM analyses WHERE id = ?', (analysis_id,)).fetchone()
    conn.close()
    
    if not analysis or not analysis['report_path']:
        return "Rapport non trouvé", 404
    
    report_path = Path(analysis['report_path'])
    if not report_path.exists():
        return "Fichier de rapport introuvable", 404
    
    # Lire le contenu et corriger les chemins des fichiers
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les chemins relatifs par des chemins absolus vers notre API
    content = content.replace('src="output_graph_simple.png"', f'src="/analysis/{analysis_id}/file/output_graph_simple.png"')
    content = content.replace('src="output_graph_metrics.png"', f'src="/analysis/{analysis_id}/file/output_graph_metrics.png"')
    content = content.replace('href="graph_interactive.html"', f'href="/analysis/{analysis_id}/file/graph_interactive.html"')
    
    return content

@app.route('/api/ai-advisor/status')
def ai_advisor_status():
    """Retourne le statut de l'agent IA"""
    info = get_ai_advisor().get_provider_info()
    return jsonify(info)

@app.route('/api/ai-advisor/suggest', methods=['POST'])
def ai_advisor_suggest():
    """Génère une suggestion pour un problème (vulnérabilité ou cycle)"""
    data = request.json
    
    ai = get_ai_advisor()
    if not ai.is_available():
        return jsonify({
            'error': 'Aucun provider IA configuré',
            'message': 'Configurez OPENAI_API_KEY ou ANTHROPIC_API_KEY dans les variables d\'environnement, ou installez Ollama localement.'
        }), 503
    
    issue = data.get('issue', {})
    
    try:
        suggestion = ai.get_vulnerability_suggestion(issue)
        return jsonify({
            'success': True,
            'suggestion': suggestion
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Erreur lors de la génération de la suggestion'
        }), 500

@app.route('/api/ai-advisor/batch-suggest', methods=['POST'])
def ai_advisor_batch_suggest():
    """Génère des suggestions pour plusieurs problèmes"""
    data = request.json
    
    ai = get_ai_advisor()
    if not ai.is_available():
        return jsonify({
            'error': 'Aucun provider IA configuré',
            'message': 'Configurez OPENAI_API_KEY ou ANTHROPIC_API_KEY dans les variables d\'environnement, ou installez Ollama localement.'
        }), 503
    
    issues = data.get('issues', [])
    
    try:
        suggestions = ai.get_batch_suggestions(issues)
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Erreur lors de la génération des suggestions'
        }), 500

if __name__ == '__main__':
    import os
    init_db()
    
    # Déterminer si on est en développement ou production
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    print("🚀 Interface Web démarrée sur http://localhost:5000")
    print("📊 Accédez à l'interface pour analyser vos projets")
    if debug_mode:
        print("⚠️  Mode DEBUG activé - Ne pas utiliser en production!")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
