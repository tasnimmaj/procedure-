import re
from collections import defaultdict
import json

def extract_actors_from_procedure_table(procedure_text):
    """
    Extrait les acteurs et leurs activités à partir d'un tableau de procédure au format Markdown
    
    Args:
        procedure_text (str): Le texte contenant le tableau de procédure généré
        
    Returns:
        list: Liste des acteurs avec leurs activités
    """
    actors_activities = defaultdict(list)
    
    if not procedure_text or not isinstance(procedure_text, str):
        return []
    
    # Nettoyer le texte et diviser en lignes
    lines = procedure_text.strip().split('\n')
    
    # Trouver les lignes du tableau (qui commencent par |)
    table_lines = [line.strip() for line in lines if line.strip().startswith('|') and '---' not in line]
    
    # Ignorer la ligne d'en-tête (première ligne du tableau)
    if len(table_lines) > 1:
        data_lines = table_lines[2:]  # Ignorer l'en-tête et la ligne de séparation
        for line in data_lines:
            columns = [col.strip() for col in line.split('|')[1:-1]]
            
            # S'assurer qu'il y a assez de colonnes
            if len(columns) >= 4:  # Au minimum: N°, Activité, Description, Acteur
                numero = columns[0].strip()
                activite = columns[1].strip()
                acteur = columns[3].strip()  # L'acteur est généralement dans la 4ème colonne                # Ignorer les lignes vides ou invalides
                if acteur and activite and numero:
                    # Pour chaque acteur listé (séparé par des virgules, points-virgules ou 'et')
                    acteurs_liste = re.split(r'[,;/]|\set\s', acteur)
                    for acteur_individuel in acteurs_liste:
                        acteur_individuel = acteur_individuel.strip()
                        if acteur_individuel:
                            # Ajouter l'activité à la liste de l'acteur
                            actors_activities[acteur_individuel].append({
                                'numero': numero,
                                'activite': activite,
                                'description': columns[2].strip() if len(columns) > 2 else ''
                            })
    
    # Convertir en liste de dictionnaires pour la réponse JSON
    result = []
    # Regrouper par acteur
    for acteur, activites in actors_activities.items():
        # Trier les activités par numéro
        activites.sort(key=lambda x: int(x['numero']) if x['numero'].isdigit() else float('inf'))
        result.append({
            'nom_acteur': acteur,
            'activites': activites,
            'nombre_activites': len(activites)
        })
    
    # Trier par nombre d'activités décroissant
    result.sort(key=lambda x: x['nombre_activites'], reverse=True)
    
    return result

def extract_actors_from_data_structure(data):
    """
    Extrait les acteurs à partir de la structure de données JSON complète
    
    Args:
        data (dict): Structure de données complète avec dossiers et procédures
        
    Returns:
        list: Liste des acteurs avec leurs activités
    """
    actors_activities = defaultdict(list)
    
    if not data or not isinstance(data, dict):
        return []
    
    dossiers = data.get('dossiers', []) if isinstance(data, dict) else data
    
    for dossier in dossiers:
        numero_dossier = dossier.get('numero', 'N/A')
        nom_dossier = dossier.get('nom', 'N/A')
        procedures = dossier.get('procedures', [])
        
        for proc in procedures:
            if isinstance(proc, dict) and 'etapes' in proc:
                for etape in proc.get('etapes', []):
                    if isinstance(etape, dict):
                        numero = etape.get('N°', 'N/A')
                        activite = etape.get('Activités', 'N/A')
                        description = etape.get('Description', 'N/A')
                        acteurs = etape.get('Acteurs', 'N/A')
                        
                        if acteurs and acteurs != "N/A":
                            # Séparer les acteurs multiples
                            acteurs_list = re.split(r'[,;/]|\set\s', acteurs)
                            
                            for acteur in acteurs_list:
                                acteur = acteur.strip()
                                if acteur and acteur != "N/A":
                                    activite_complete = {
                                        'dossier_numero': numero_dossier,
                                        'dossier_nom': nom_dossier,
                                        'etape_numero': numero,
                                        'activite': activite,
                                        'description': description
                                    }
                                    actors_activities[acteur].append(activite_complete)
    
    # Convertir en liste de dictionnaires
    result = []
    for acteur, activites in actors_activities.items():
        result.append({
            'nom_acteur': acteur,
            'nombre_activites': len(activites),
            'activites': activites
        })
    
    # Trier par nombre d'activités décroissant
    result.sort(key=lambda x: x['nombre_activites'], reverse=True)
    
    return result

def get_actors_summary(actors_data):
    """
    Génère un résumé statistique des acteurs
    
    Args:
        actors_data (list): Liste des acteurs avec leurs activités
        
    Returns:
        dict: Résumé statistique
    """
    if not actors_data:
        return {
            'total_acteurs': 0,
            'total_activites': 0,
            'acteur_plus_actif': None,
            'moyenne_activites_par_acteur': 0
        }
    
    total_acteurs = len(actors_data)
    total_activites = sum(acteur['nombre_activites'] for acteur in actors_data)
    acteur_plus_actif = actors_data[0] if actors_data else None
    moyenne = total_activites / total_acteurs if total_acteurs > 0 else 0
    
    return {
        'total_acteurs': total_acteurs,
        'total_activites': total_activites,
        'acteur_plus_actif': acteur_plus_actif,
        'moyenne_activites_par_acteur': round(moyenne, 2)
    }

# Fonction d'aide pour l'API
def process_procedure_for_actors(procedure_text):
    """
    Fonction principale pour traiter une procédure et retourner les acteurs
    Cette fonction sera appelée par votre API Flask/FastAPI
    """
    try:
        actors = extract_actors_from_procedure_table(procedure_text)
        summary = get_actors_summary(actors)
        
        return {
            'success': True,
            'data': {
                'acteurs': actors,
                'resume': summary
            },
            'message': f"{summary['total_acteurs']} acteurs trouvés avec {summary['total_activites']} activités au total"
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f"Erreur lors de l'extraction des acteurs: {str(e)}"
        }