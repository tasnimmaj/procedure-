
import json
import os
import re
from pathlib import Path

class CirculaireQABot:
    """
    Classe pour gérer un chatbot de questions-réponses basé sur des notes circulaires et procédures.
    """
    
    def __init__(self, data_path="data/donnees.json"):
        """
        Initialise le chatbot avec les données des notes circulaires et procédures.
        
        Args:
            data_path (str): Chemin vers le fichier JSON contenant les données
        """
        self.data_path = data_path
        self.data = self._load_data()
        self.current_context = None
    
    def _load_data(self):
        """Charge les données depuis le fichier JSON"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"circulaires": [], "procedures": []}
        except Exception as e:
            print(f"Erreur lors du chargement des données: {e}")
            return {"circulaires": [], "procedures": []}
    
    def save_data(self):
        """Sauvegarde les données dans le fichier JSON"""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")
    
    def set_context(self, circulaire_id=None, procedure_id=None):
        """
        Définit le contexte actuel pour les questions
        
        Args:
            circulaire_id (str): ID de la note circulaire
            procedure_id (str): ID de la procédure
        """
        context = {}
        
        if circulaire_id:
            for circ in self.data.get("circulaires", []):
                if circ.get("id") == circulaire_id:
                    context["circulaire"] = circ
                    break
        
        if procedure_id:
            for proc in self.data.get("procedures", []):
                if proc.get("id") == procedure_id:
                    context["procedure"] = proc
                    break
        
        self.current_context = context if context else None
        return bool(self.current_context)
    
    def get_available_documents(self):
        """
        Renvoie la liste des documents disponibles (circulaires et procédures)
        
        Returns:
            dict: Liste des documents disponibles
        """
        circulaires = [{"id": c.get("id"), "titre": c.get("titre")} 
                      for c in self.data.get("circulaires", [])]
        
        procedures = [{"id": p.get("id"), "titre": p.get("titre")} 
                     for p in self.data.get("procedures", [])]
        
        return {
            "circulaires": circulaires,
            "procedures": procedures
        }
    
    def _search_keywords(self, text, keywords):
        """
        Recherche des mots-clés dans un texte
        
        Args:
            text (str): Texte à analyser
            keywords (list): Liste des mots-clés à rechercher
            
        Returns:
            bool: True si au moins un mot-clé est trouvé
        """
        if not text or not keywords:
            return False
            
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
    
    def _find_relevant_sections(self, question):
        """
        Trouve les sections pertinentes dans le contexte actuel
        
        Args:
            question (str): Question posée
            
        Returns:
            list: Liste des sections pertinentes
        """
        if not self.current_context:
            return []
            
        # Extraire les mots-clés de la question (mots de plus de 3 lettres)
        keywords = [word for word in re.findall(r'\b\w+\b', question.lower()) 
                   if len(word) > 3 and word not in {"quoi", "comment", "pourquoi", "quel", "quelle", "quels", "quelles"}]
        
        relevant_sections = []
        
        # Rechercher dans la circulaire
        if "circulaire" in self.current_context:
            circulaire = self.current_context["circulaire"]
            content = circulaire.get("contenu", "")
            
            # Division en sections (paragraphes)
            sections = [s.strip() for s in content.split('\n\n') if s.strip()]
            
            for section in sections:
                if self._search_keywords(section, keywords):
                    relevant_sections.append({
                        "source": "circulaire",
                        "titre": circulaire.get("titre", ""),
                        "contenu": section
                    })
        
        # Rechercher dans la procédure
        if "procedure" in self.current_context:
            procedure = self.current_context["procedure"]
            
            # Rechercher dans les étapes
            for etape in procedure.get("etapes", []):
                if self._search_keywords(etape.get("description", ""), keywords):
                    relevant_sections.append({
                        "source": "procedure",
                        "titre": procedure.get("titre", ""),
                        "contenu": etape.get("description", "")
                    })
        
        return relevant_sections
    
    def answer_question(self, question):
        """
        Répond à une question basée sur le contexte actuel
        
        Args:
            question (str): Question posée
            
        Returns:
            dict: Réponse avec source et contenu
        """
        if not question.strip():
            return {
                "reponse": "Veuillez poser une question.",
                "sources": []
            }
        
        if not self.current_context:
            return {
                "reponse": "Aucun contexte sélectionné. Veuillez choisir une note circulaire ou une procédure.",
                "sources": []
            }
        
        relevant_sections = self._find_relevant_sections(question)
        
        if not relevant_sections:
            return {
                "reponse": "Je n'ai pas trouvé d'information pertinente pour votre question dans le contexte actuel.",
                "sources": []
            }
        
        # Construction de la réponse à partir des sections pertinentes
        combined_answer = ""
        sources = []
        
        for section in relevant_sections:
            combined_answer += section["contenu"] + " "
            sources.append({
                "type": section["source"],
                "titre": section["titre"]
            })
        
        return {
            "reponse": combined_answer.strip(),
            "sources": sources
        }
    
    def add_circulaire(self, titre, contenu):
        """
        Ajoute une nouvelle note circulaire à la base de données
        
        Args:
            titre (str): Titre de la note circulaire
            contenu (str): Contenu de la note circulaire
            
        Returns:
            str: ID de la note circulaire ajoutée
        """
        circulaire_id = f"circ_{len(self.data.get('circulaires', []))}"
        
        circulaire = {
            "id": circulaire_id,
            "titre": titre,
            "contenu": contenu
        }
        
        if "circulaires" not in self.data:
            self.data["circulaires"] = []
            
        self.data["circulaires"].append(circulaire)
        self.save_data()
        
        return circulaire_id
    
    def add_procedure(self, titre, description, etapes):
        """
        Ajoute une nouvelle procédure à la base de données
        
        Args:
            titre (str): Titre de la procédure
            description (str): Description de la procédure
            etapes (list): Liste des étapes de la procédure
            
        Returns:
            str: ID de la procédure ajoutée
        """
        procedure_id = f"proc_{len(self.data.get('procedures', []))}"
        
        procedure = {
            "id": procedure_id,
            "titre": titre,
            "description": description,
            "etapes": etapes
        }
        
        if "procedures" not in self.data:
            self.data["procedures"] = []
            
        self.data["procedures"].append(procedure)
        self.save_data()
        
        return procedure_id