"""
Gestionnaire Git - Clone automatique de dépôts pour analyse
Utilise git clone shallow (sans historique) pour optimiser la vitesse
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


class GitManager:
    """Gère le clonage automatique de dépôts Git"""
    
    def __init__(self, base_dir: str = "input_data"):
        """
        Initialise le gestionnaire Git
        
        Args:
            base_dir: Dossier de base où cloner les repos
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def clone_repository(self, repo_url: str, destination: Optional[str] = None) -> Path:
        """
        Clone un dépôt Git (shallow clone - sans historique)
        
        Args:
            repo_url: URL du dépôt (https://github.com/user/repo.git)
            destination: Nom du dossier de destination (auto si None)
            
        Returns:
            Path du dossier cloné
        """
        # Générer nom de destination si non fourni
        if destination is None:
            repo_name = repo_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            destination = repo_name
        
        dest_path = self.base_dir / destination
        
        # Supprimer si existe déjà
        if dest_path.exists():
            print(f"🗑️  Suppression de l'ancien dossier : {dest_path}")
            shutil.rmtree(dest_path)
        
        # Clone shallow (--depth 1 = sans historique)
        print(f"📥 Clonage de {repo_url}...")
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, str(dest_path)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"✅ Dépôt cloné : {dest_path}")
            return dest_path
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors du clonage : {e.stderr}")
            raise
    
    def clone_multiple(self, repo_urls: list) -> list:
        """
        Clone plusieurs dépôts
        
        Args:
            repo_urls: Liste d'URLs de dépôts
            
        Returns:
            Liste des chemins clonés
        """
        cloned_paths = []
        
        for url in repo_urls:
            try:
                path = self.clone_repository(url)
                cloned_paths.append(path)
            except Exception as e:
                print(f"⚠️  Impossible de cloner {url} : {e}")
        
        return cloned_paths
    
    def cleanup(self, repo_name: str):
        """
        Supprime un dépôt cloné
        
        Args:
            repo_name: Nom du dossier à supprimer
        """
        repo_path = self.base_dir / repo_name
        
        if repo_path.exists():
            shutil.rmtree(repo_path)
            print(f"🗑️  Dépôt supprimé : {repo_path}")
        else:
            print(f"⚠️  Dépôt introuvable : {repo_path}")
