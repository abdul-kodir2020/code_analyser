"""
Agent IA pour suggérer des solutions aux vulnérabilités détectées
Supporte plusieurs providers : OpenAI, Claude, Ollama (local)
"""

import os
import json
from typing import List, Dict, Optional
import requests


class AIAdvisor:
    """Agent IA pour générer des suggestions de corrections de sécurité"""
    
    def __init__(self, provider: str = "auto"):
        """
        Initialise l'agent IA
        
        Args:
            provider: "openai", "claude", "ollama", ou "auto" pour détection automatique
        """
        self.provider = provider
        self.api_key = None
        self.suggestions_cache = {}
        
        # Détection automatique du provider disponible
        if provider == "auto":
            self.provider = self._detect_provider()
        
        # Configuration selon le provider
        if self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.model = "gpt-4"
        elif self.provider == "claude":
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
            self.api_url = "https://api.anthropic.com/v1/messages"
            self.model = "claude-3-5-sonnet-20241022"
        elif self.provider == "ollama":
            self.api_url = "http://localhost:11434/api/generate"
            self.model = os.getenv("OLLAMA_MODEL", "llama3.2")  # Personnalisable via variable d'environnement
            self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "180"))  # 3 minutes par défaut
        else:
            self.provider = None
            
    def _detect_provider(self) -> Optional[str]:
        """Détecte automatiquement le provider IA disponible"""
        # Vérifier OpenAI
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        
        # Vérifier Claude
        if os.getenv("ANTHROPIC_API_KEY"):
            return "claude"
        
        # Vérifier Ollama (serveur local)
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                return "ollama"
        except:
            pass
        
        return None
    
    def is_available(self) -> bool:
        """Vérifie si un provider IA est disponible"""
        return self.provider is not None
    
    def get_vulnerability_suggestion(self, vulnerability: Dict) -> Dict:
        """
        Génère une suggestion pour corriger une vulnérabilité
        
        Args:
            vulnerability: Dictionnaire avec type, severity, description, code
            
        Returns:
            Dict avec explanation, fix_code, steps
        """
        if not self.is_available():
            return {
                "explanation": "Aucun provider IA configuré. Configurez OPENAI_API_KEY ou ANTHROPIC_API_KEY, ou installez Ollama.",
                "fix_code": None,
                "steps": []
            }
        
        # Vérifier le cache
        cache_key = f"{vulnerability['type']}_{vulnerability.get('line', 0)}"
        if cache_key in self.suggestions_cache:
            return self.suggestions_cache[cache_key]
        
        # Construire le prompt
        prompt = self._build_prompt(vulnerability)
        
        # Appeler l'API selon le provider
        try:
            if self.provider == "openai":
                suggestion = self._call_openai(prompt)
            elif self.provider == "claude":
                suggestion = self._call_claude(prompt)
            elif self.provider == "ollama":
                suggestion = self._call_ollama(prompt)
            else:
                suggestion = {"explanation": "Provider non supporté", "fix_code": None, "steps": []}
            
            # Mettre en cache
            self.suggestions_cache[cache_key] = suggestion
            return suggestion
            
        except Exception as e:
            return {
                "explanation": f"Erreur lors de la génération de la suggestion : {str(e)}",
                "fix_code": None,
                "steps": []
            }
    
    def _build_prompt(self, vulnerability: Dict) -> str:
        """Construit le prompt pour l'IA"""
        vuln_type = vulnerability.get('type', 'Unknown')
        severity = vulnerability.get('severity', 'MOYEN')
        description = vulnerability.get('description', '')
        code_snippet = vulnerability.get('code', '')
        
        prompt = f"""Tu es un expert en sécurité Python. Analyse cette vulnérabilité et fournis une solution.

**Vulnérabilité détectée :**
- Type : {vuln_type}
- Sévérité : {severity}
- Description : {description}

**Code problématique :**
```python
{code_snippet}
```

Fournis une réponse au format JSON avec exactement cette structure :
{{
    "explanation": "Explication claire et concise du problème de sécurité (2-3 phrases)",
    "fix_code": "Code Python corrigé (uniquement le code, sans markdown ni backticks)",
    "steps": [
        "Étape 1 : Action à effectuer",
        "Étape 2 : Action à effectuer",
        "Étape 3 : Action à effectuer"
    ]
}}

Règles importantes :
- L'explication doit être en français, claire et technique
- Le fix_code doit être du code Python valide, prêt à copier-coller
- Les steps doivent être des actions concrètes et numérotées
- Pas de texte en dehors du JSON
- Pas de markdown, pas de backticks dans fix_code
"""
        return prompt
    
    def _call_openai(self, prompt: str) -> Dict:
        """Appelle l'API OpenAI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Tu es un expert en sécurité Python. Réponds toujours en JSON valide."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        return json.loads(content)
    
    def _call_claude(self, prompt: str) -> Dict:
        """Appelle l'API Claude"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result['content'][0]['text']
        
        # Extraire le JSON de la réponse
        try:
            return json.loads(content)
        except:
            # Si la réponse contient du markdown, extraire le JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise ValueError("Impossible d'extraire le JSON de la réponse")
    
    def _call_ollama(self, prompt: str) -> Dict:
        """Appelle Ollama (serveur local)"""
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500  # Limiter la longueur de la réponse pour être plus rapide
            }
        }
        
        response = requests.post(self.api_url, json=data, timeout=self.ollama_timeout)
        response.raise_for_status()
        
        result = response.json()
        content = result['response']
        return json.loads(content)
    
    def get_batch_suggestions(self, vulnerabilities: List[Dict]) -> Dict[str, Dict]:
        """
        Génère des suggestions pour plusieurs vulnérabilités
        
        Args:
            vulnerabilities: Liste de vulnérabilités
            
        Returns:
            Dict avec module_name comme clé et suggestion comme valeur
        """
        suggestions = {}
        
        for vuln in vulnerabilities:
            module = vuln.get('module', 'unknown')
            if module not in suggestions:
                suggestions[module] = []
            
            suggestion = self.get_vulnerability_suggestion(vuln)
            suggestions[module].append({
                "vulnerability": vuln,
                "suggestion": suggestion
            })
        
        return suggestions
    
    def get_provider_info(self) -> Dict:
        """Retourne les informations sur le provider configuré"""
        return {
            "provider": self.provider,
            "available": self.is_available(),
            "model": self.model if self.is_available() else None
        }
