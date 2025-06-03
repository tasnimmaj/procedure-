from typing import List

def extract_steps_from_procedure(procedure_text: str) -> List[dict]:
    """
    Extrait les étapes d'une procédure formatée en texte Markdown
    MODIFIÉ : Extrait aussi le début et la fin depuis la première et dernière étape
    """
    if not procedure_text:
        return []
        
    steps = []
    lines = procedure_text.strip().split('\n')
    
    # Rechercher le début du tableau
    table_start = -1
    for i, line in enumerate(lines):
        if '|' in line and ('#' in line.lower() or 'numéro' in line.lower() or 'étape' in line.lower() or 'n°' in line.lower()):
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
                step_number = columns[0].strip()
                activity = columns[1].strip()
                
                # Détecter les acteurs selon le nombre de colonnes
                if len(columns) >= 6:  # Format avec 6 colonnes
                    actor = columns[3].strip()  # Colonne "Acteurs"
                    document = columns[4].strip()  # Colonne "Documents"
                elif len(columns) >= 3:  # Format avec 3 colonnes
                    actor = columns[2].strip()
                    document = ""
                else:
                    actor = "N/A"
                    document = ""
                
                # Vérifier la validité des données
                if all([step_number, activity, actor]):
                    steps.append({
                        'number': step_number,
                        'activity': activity,
                        'actor': actor,
                        'document': document if document else "N/A"
                    })
            except IndexError:
                pass
                
        current_line += 1
    
    # AJOUT : Insérer le début et la fin automatiquement
    if steps:
        # Créer l'étape de début basée sur la première activité
        first_activity = steps[0]['activity']
        debut_step = {
            'number': '0',
            'activity': f"Début: {first_activity}",
            'actor': steps[0]['actor'],
            'document': "N/A"
        }
        
        # Créer l'étape de fin basée sur la dernière activité
        last_activity = steps[-1]['activity']
        fin_step = {
            'number': str(len(steps) + 1),
            'activity': f"Fin: {last_activity}",
            'actor': steps[-1]['actor'],
            'document': "N/A"
        }
        
        # Insérer au début et à la fin
        steps.insert(0, debut_step)
        steps.append(fin_step)
    
    return steps