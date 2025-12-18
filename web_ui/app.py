from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import threading
import subprocess
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Configuration
DATABASE = 'analyses.db'
REPORTS_DIR = Path('web_reports')
REPORTS_DIR.mkdir(exist_ok=True)

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
        # Mettre à jour le statut
        c.execute('UPDATE analyses SET status = ? WHERE id = ?', ('running', analysis_id))
        conn.commit()
        
        # Créer un dossier pour cette analyse
        analysis_dir = REPORTS_DIR / f'analysis_{analysis_id}'
        analysis_dir.mkdir(exist_ok=True)
        
        # Chemin vers le script main.py (un niveau au-dessus de web_ui)
        main_script = Path(__file__).parent.parent / 'main.py'
        
        # Lancer l'analyse
        result = subprocess.run(
            ['python3', str(main_script), repo_url],
            cwd=str(Path(__file__).parent.parent),  # Exécuter depuis la racine du projet
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes max
        )
        
        if result.returncode == 0:
            # Déplacer les fichiers générés
            project_root = Path(__file__).parent.parent
            for file in ['report.html', 'output_graph_simple.png', 'output_graph_metrics.png', 'graph_interactive.html']:
                src = project_root / file
                if src.exists():
                    dst = analysis_dir / file
                    src.rename(dst)
            
            # Extraire les métriques du rapport si possible
            report_path = analysis_dir / 'report.html'
            
            # Parser les résultats (basique - on pourrait améliorer)
            output = result.stdout
            modules = 0
            deps = 0
            
            # Extraction basique des métriques depuis stdout
            for line in output.split('\n'):
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
                SET status = ?, completed_at = ?, total_modules = ?, total_dependencies = ?, report_path = ?
                WHERE id = ?
            ''', ('completed', datetime.now(), modules, deps, str(report_path), analysis_id))
        else:
            c.execute('''
                UPDATE analyses 
                SET status = ?, completed_at = ?, error_message = ?
                WHERE id = ?
            ''', ('failed', datetime.now(), result.stderr[:500], analysis_id))
        
        conn.commit()
    
    except subprocess.TimeoutExpired:
        c.execute('''
            UPDATE analyses 
            SET status = ?, error_message = ?
            WHERE id = ?
        ''', ('failed', 'Timeout: analyse trop longue (>5min)', analysis_id))
        conn.commit()
    
    except Exception as e:
        c.execute('''
            UPDATE analyses 
            SET status = ?, error_message = ?
            WHERE id = ?
        ''', ('failed', str(e)[:500], analysis_id))
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
    conn = get_db()
    c = conn.cursor()
    
    # Récupérer le chemin du rapport pour supprimer les fichiers
    analysis = c.execute('SELECT report_path FROM analyses WHERE id = ?', (analysis_id,)).fetchone()
    
    if analysis and analysis['report_path']:
        # Supprimer le dossier de l'analyse
        analysis_dir = Path(analysis['report_path']).parent
        if analysis_dir.exists():
            import shutil
            shutil.rmtree(analysis_dir, ignore_errors=True)
    
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
