"""
Module d'extraction des procédures à partir du format Markdown
"""

from typing import List, Dict, Tuple

def extract_steps_from_procedure(procedure_text: str) -> List[dict]:
    """
    Extrait les étapes d'une procédure formatée en texte Markdown
    
    Args:
        procedure_text (str): Le texte de la procédure au format Markdown
        
    Returns:
        List[dict]: Liste des étapes avec leurs propriétés (number, activity, actor)
    """
    if not procedure_text:
        return []
        
    steps = []
    lines = procedure_text.strip().split('\n')
    
    # Rechercher le début du tableau
    table_start = -1
    for i, line in enumerate(lines):
        if '|' in line and ('#' in line.lower() or 'numéro' in line.lower() or 'étape' in line.lower()):
            table_start = i
            break
    
    if table_start == -1:
        return []
        
    # Ignorer l'en-tête et la ligne de séparation
    current_line = table_start + 2
    
    # Parser chaque ligne du tableau
    while current_line < len(lines):
        line = lines[current_line].strip()
        if not line or '|' not in line:
            break
        
        # Extraire et nettoyer les colonnes
        columns = [col.strip() for col in line.split('|')[1:-1]]
        if len(columns) >= 3:
            try:
                # Vérifier que nous avons un numéro d'étape valide
                step_number = columns[0].strip()
                activity = columns[1].strip()
                actor = columns[2].strip()
                
                # Vérifier la validité des données
                if all([step_number, activity, actor]):
                    steps.append({
                        'number': step_number,
                        'activity': activity,
                        'actor': actor
                    })
            except IndexError:
                pass  # Ignorer les lignes mal formatées
                
        current_line += 1
    
    return steps

def format_steps_to_markdown(steps: List[dict]) -> str:
    """
    Convertit une liste d'étapes en tableau Markdown formaté
    
    Args:
        steps (List[dict]): Liste des étapes avec leurs propriétés
        
    Returns:
        str: Table au format Markdown
    """
    if not steps:
        return "Aucune étape trouvée."
        
    # En-tête du tableau avec alignement
    markdown_lines = [
        "| N° | Activité | Acteur |",
        "|:---|:---------|:--------|"
    ]
    
    # Ajouter chaque étape
    for step in steps:
        if isinstance(step, dict) and all(k in step for k in ['number', 'activity', 'actor']):
            # Nettoyer et formater les valeurs
            number = str(step['number']).strip()
            activity = step['activity'].replace('|', '\\|').strip()  # Échapper les | dans le texte
            actor = step['actor'].replace('|', '\\|').strip()
            
            # Ajouter la ligne au tableau
            markdown_lines.append(f"| {number} | {activity} | {actor} |")
    
    return "\n".join(markdown_lines)

def extract_activities_and_actors(procedure_text: str) -> Tuple[List[str], List[str]]:
    """
    Extrait les activités et les acteurs d'une procédure
    
    Args:
        procedure_text (str): Le texte de la procédure au format Markdown
        
    Returns:
        Tuple[List[str], List[str]]: Tuple contenant la liste des activités et la liste des acteurs
    """
    steps = extract_steps_from_procedure(procedure_text)
    activities = [step['activity'] for step in steps]
    actors = [step['actor'] for step in steps]
    return activities, actors
