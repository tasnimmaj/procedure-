"""
Module de génération de logigrammes AMÉLIORÉ avec design professionnel
Structure PRÉSERVÉE : Document (GAUCHE) ← Étape (CENTRE) → Acteur (DROITE)
Palette moderne, typographie élégante, connexions subtiles
LISIBILITÉ OPTIMISÉE : Tailles et espacements ajustés pour une meilleure lisibilité
ENTRÉE/SORTIE DYNAMIQUES : Basées sur le tableau I/O généré par le LLM
CORRECTION MAJEURE : Extraction robuste des étapes compatible avec tous les modèles LLM
"""

from graphviz import Digraph
import base64
from io import BytesIO
import re

# Palette de couleurs professionnelle avec meilleur contraste
COLORS = {
    'steps': '#2C5282',         # Bleu plus foncé pour meilleur contraste
    'steps_text': 'white',      # Texte blanc sur bleu foncé
    'documents': '#E8F4FD',     # Bleu très clair
    'documents_border': '#2C5282', # Bordure bleu foncé pour meilleur contraste
    'documents_text': '#1A202C', # Texte gris très foncé
    'actors': '#FFF2CC',        # Jaune pastel
    'actors_border': '#B7791F', # Bordure dorée plus foncée
    'actors_text': '#744210',   # Texte brun plus foncé
    'start': '#22543D',         # Vert plus foncé
    'end': '#9B2C2C',           # Rouge plus foncé
    'flow_main': '#1A202C',     # Gris anthracite très foncé
    'flow_connect': '#4A5568',  # Gris moyen plus foncé
    'background': '#FAFBFC'     # Fond gris très clair
}

def extract_io_events(io_table_text: str) -> dict:
    """
    Extrait les événements d'entrée et de sortie du tableau I/O généré par le LLM
    VERSION CORRIGÉE : Prend la 2ème colonne (activité) comme vous le souhaitez
    """
    if not io_table_text or not io_table_text.strip():
        return {'entree': 'Début', 'sortie': 'Fin'}
    
    print(f"🔍 Analyse du tableau I/O: {io_table_text[:200]}...")
    
    # Nettoyer le texte et diviser en lignes
    lines = [line.strip() for line in io_table_text.strip().split('\n') if line.strip()]
    
    # Filtrer les lignes qui contiennent des données (avec des |)
    data_lines = []
    for line in lines:
        if '|' in line and not re.match(r'^\s*\|[\s\-:]+\|', line):  # Exclure les séparateurs
            data_lines.append(line)
    
    if len(data_lines) < 2:
        return {'entree': 'Début', 'sortie': 'Fin'}
    
    # Afficher l'en-tête pour debug
    header_line = data_lines[0]
    print(f"📋 En-tête du tableau I/O: {header_line}")
    
    # Ignorer la ligne d'en-tête (première ligne)
    data_rows = data_lines[1:]  # Toutes les lignes sauf l'en-tête
    
    # Trouver l'entrée et la sortie
    entree = None
    sortie = None
    
    for row in data_rows:
        print(f"🔍 Analyse ligne I/O: {row}")
        
        # Nettoyage plus robuste des colonnes
        cols = [col.strip() for col in row.split('|') if col.strip()]
        print(f"📊 Colonnes extraites: {cols}")
        
        if len(cols) >= 2:
            type_io = cols[0].lower()
            # CORRECTION : Prendre la 2ème colonne (index 1) comme activité
            activite = cols[1]  # C'est ça que vous voulez !
            
            print(f"🎯 Type: '{type_io}', Activité: '{activite}'")
            
            if any(keyword in type_io for keyword in ['entrée', 'entree', 'input', 'début', 'debut']):
                entree = activite
                print(f"✅ Entrée trouvée: {entree}")
            elif any(keyword in type_io for keyword in ['sortie', 'output', 'fin']):
                sortie = activite
                print(f"✅ Sortie trouvée: {sortie}")
    
    result = {
        'entree': entree if entree else 'Début',
        'sortie': sortie if sortie else 'Fin'
    }
    
    print(f"🎯 Résultat final I/O: {result}")
    return result

def extract_steps_from_procedure(markdown_text: str) -> list:
    """
    Extrait les étapes d'une procédure à partir d'un tableau Markdown
    VERSION CORRIGÉE : Extraction robuste compatible avec tous les modèles LLM
    CORRECTION : Prend maintenant la colonne "Activités" au lieu de "Description"
    """
    if not markdown_text:
        return []
    
    print(f"🔍 Analyse de la procédure: {markdown_text[:300]}...")
    
    # Nettoyer et diviser en lignes
    lines = [line.strip() for line in markdown_text.split('\n') if line.strip()]
    
    # Trouver toutes les lignes contenant des pipes (|)
    table_lines = []
    for line in lines:
        if '|' in line:
            table_lines.append(line)
    
    if len(table_lines) < 2:
        print("❌ Pas assez de lignes de tableau trouvées")
        return []
    
    print(f"📋 {len(table_lines)} lignes de tableau trouvées")
    
    # Identifier l'en-tête de manière plus robuste
    header_line = None
    separator_indices = []
    
    for i, line in enumerate(table_lines):
        # Détecter les lignes de séparation (contiennent des tirets)
        if re.search(r'[\-:]+', line) and '---' in line:
            separator_indices.append(i)
        # Si pas encore d'en-tête trouvé et que ce n'est pas une ligne de séparation
        elif header_line is None and not re.search(r'^\s*\|[\s\-:]+\|', line):
            header_line = line
            header_index = i
    
    if header_line is None:
        print("❌ En-tête non trouvé")
        return []
    
    print(f"📝 En-tête trouvé: {header_line}")
    
    # Extraire les noms des colonnes de l'en-tête
    headers = []
    header_parts = [part.strip() for part in header_line.split('|') if part.strip()]
    for part in header_parts:
        headers.append(part.lower())
    
    print(f"🏷️ Colonnes détectées: {headers}")
    
    # Trouver les lignes de données (après l'en-tête et les séparateurs)
    data_start_index = header_index + 1
    
    # Passer les lignes de séparation
    while data_start_index < len(table_lines):
        line = table_lines[data_start_index]
        if re.search(r'^\s*\|[\s\-:]+\|', line) or '---' in line:
            data_start_index += 1
        else:
            break
    
    data_rows = table_lines[data_start_index:]
    print(f"📊 {len(data_rows)} lignes de données à traiter")
    
    steps = []
    for i, row in enumerate(data_rows):
        print(f"🔍 Traitement ligne {i+1}: {row}")
        
        # Nettoyage plus robuste des colonnes
        cols = []
        parts = row.split('|')
        for part in parts:
            cleaned = part.strip()
            if cleaned:  # Ignorer les parties vides
                cols.append(cleaned)
        
        if len(cols) >= len(headers):
            step = {}
            for j, header in enumerate(headers):
                if j < len(cols):
                    value = cols[j].strip()
                    if value:  # Ignorer les valeurs vides
                        # CORRECTION ICI : Identification des colonnes plus précise
                        if any(keyword in header for keyword in ['n°', 'numero', 'étape', 'step', 'num']):
                            step['number'] = value
                        elif any(keyword in header for keyword in ['acteur', 'actor', 'responsable', 'qui']):
                            step['actor'] = value
                        # CORRECTION PRINCIPALE : Prioriser "Activités" sur "Description"  
                        elif any(keyword in header for keyword in ['activités', 'activite', 'activity']):
                            step['activity'] = value
                        # Garder description en fallback mais avec priorité plus faible
                        elif any(keyword in header for keyword in ['description', 'action', 'tâche', 'tache', 'quoi']) and 'activity' not in step:
                            step['activity'] = value
                        elif any(keyword in header for keyword in ['document', 'doc', 'support', 'formulaire']):
                            step['document'] = value
            
            # Validation : une étape doit avoir au minimum un numéro et une activité
            if step.get('number') and step.get('activity'):
                steps.append(step)
                print(f"✅ Étape ajoutée: {step['number']} - {step['activity'][:50]}...")
            else:
                print(f"⚠️ Étape ignorée (manque numéro ou activité): {step}")
    
    print(f"🎯 Total des étapes extraites: {len(steps)}")
    return steps

def generate_flowchart_improved(procedure_text: str, io_table_text: str = None, title: str = "Logigramme de procédure") -> tuple:
    """
    Génère un logigramme avec DESIGN PROFESSIONNEL et LISIBILITÉ OPTIMISÉE
    VERSION CORRIGÉE : Extraction robuste compatible avec tous les modèles LLM
    """
    try:
        print("🚀 Début de la génération du logigramme...")
        
        steps = extract_steps_from_procedure(procedure_text)
        
        if not steps:
            return None, "Aucune étape n'a pu être extraite de la procédure"
        
        print(f"📋 {len(steps)} étapes détectées")
        
        # CORRIGÉ : Extraction des événements d'entrée/sortie dynamiques
        io_events = extract_io_events(io_table_text)
        start_text = io_events['entree']
        end_text = io_events['sortie']
        
        print(f"🎯 Événements extraits → Début: '{start_text}', Fin: '{end_text}'")
        
        # Configuration du graphe avec design moderne et lisibilité optimisée
        dot = Digraph(
            comment=title,
            engine='dot',
            graph_attr={
                'rankdir': 'TB',
                'splines': 'ortho',
                'nodesep': '1.2',              # Espacement horizontal compact
                'ranksep': '1.0',              # Espacement vertical compact
                'compound': 'true',
                'bgcolor': COLORS['background'],
                'pad': '0.5',                  # Padding minimal
                'dpi': '150',                  # Résolution optimisée
                'fontname': 'Arial Bold',      # Police plus lisible
                'style': 'rounded',
                'size': '30,30!'               # Taille max optimisée
            },
            node_attr={
                'fontname': 'Arial Black',     # Police la plus grasse possible
                'fontsize': '24',              # Taille optimisée pour lisibilité
                'style': 'filled,rounded',
                'penwidth': '1.5',             # Bordures fines
                'margin': '0.2'                # Marge interne compacte
            },
            edge_attr={
                'arrowsize': '0.8',            # Flèches compactes
                'fontname': 'Arial Bold',
                'fontsize': '16',              # Taille compacte
                'penwidth': '1.5'              # Traits fins
            }
        )
        
        # Colonnes invisibles pour l'alignement (structure préservée)
        with dot.subgraph(name='cluster_docs') as docs:
            docs.attr(style='invis')
            docs.node('col_left', '', style='invis', width='0.1', height='0.1')
            
        with dot.subgraph(name='cluster_steps') as steps_graph:
            steps_graph.attr(style='invis')
            steps_graph.node('col_center', '', style='invis', width='0.1', height='0.1')
            
        with dot.subgraph(name='cluster_actors') as actors:
            actors.attr(style='invis')
            actors.node('col_right', '', style='invis', width='0.1', height='0.1')
        
        # Alignement forcé des colonnes
        dot.edge('col_left', 'col_center', style='invis')
        dot.edge('col_center', 'col_right', style='invis')
        
        # DÉBUT DYNAMIQUE avec style moderne et taille optimisée
        start_formatted = start_text
        if len(start_text) > 25:
            words = start_text.split()
            lines = []
            current_line = []
            for word in words:
                if len(' '.join(current_line + [word])) > 25:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
                else:
                    current_line.append(word)
            if current_line:
                lines.append(' '.join(current_line))
            start_formatted = '\\n'.join(lines)
        
        dot.node('debut', start_formatted, 
                shape='ellipse',
                fillcolor=COLORS['start'],
                fontcolor='white',
                fontsize='26',                 # Taille optimisée
                fontweight='bold',
                penwidth='1.5',
                width='2.2', height='1.2')     # Taille compacte
        
        previous_step = 'debut'
        
        # Traitement de chaque étape avec design amélioré et taille optimisée
        for i, step in enumerate(steps):
            step_id = f"step_{i}"
            
            print(f"🔄 Traitement étape {i+1}: {step.get('number', 'N/A')} - {step.get('activity', 'N/A')[:30]}...")
            
            # Détection des décisions
            is_decision = any(keyword in step['activity'].lower() 
                           for keyword in ['décision', 'vérification', '?', 'si ', 'conditionnel', 'choix'])
            
            # Formatage du texte avec retours à la ligne pour améliorer la lisibilité
            step_text = step['activity']
            if len(step_text) > 20:  # Seuil réduit pour meilleure lisibilité
                words = step_text.split()
                lines = []
                current_line = []
                for word in words:
                    if len(' '.join(current_line + [word])) > 20:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            lines.append(word)
                    else:
                        current_line.append(word)
                if current_line:
                    lines.append(' '.join(current_line))
                step_text = '\\n'.join(lines)
            
            step_label = f"{step['number']}\\n{step_text}"
            
            # ÉTAPE CENTRALE avec style professionnel et taille optimisée
            if is_decision:
                dot.node(step_id, step_label, 
                        shape='diamond',
                        fillcolor=COLORS['steps'],
                        fontcolor=COLORS['steps_text'],
                        fontweight='bold',
                        fontsize='22',             # Taille optimisée
                        penwidth='1.5',
                        width='3.2', height='2.2') # Taille compacte
            else:
                dot.node(step_id, step_label, 
                        shape='box',
                        fillcolor=COLORS['steps'],
                        fontcolor=COLORS['steps_text'],
                        fontsize='24',             # Taille optimisée
                        penwidth='1.5',
                        width='3.2', height='1.6') # Taille compacte
            
            # Connexion verticale principale avec style élégant
            dot.edge(previous_step, step_id, 
                    color=COLORS['flow_main'],
                    penwidth='1.5',              # Trait fin
                    arrowsize='0.8')
            
            # IDs pour document et acteur
            doc_id = f"doc_{i}" if step.get('document') and step['document'].strip() else None
            actor_id = f"actor_{i}" if step.get('actor') and step['actor'].strip() else None
            
            # Ancres invisibles pour alignement parfait
            left_anchor = f"left_anchor_{i}"
            right_anchor = f"right_anchor_{i}"
            
            dot.node(left_anchor, '', style='invis', width='0.1', height='0.1')
            dot.node(right_anchor, '', style='invis', width='0.1', height='0.1')
            
            # DOCUMENT À GAUCHE avec style carte élégante et taille optimisée
            if doc_id:
                doc_text = step['document']
                if len(doc_text) > 18:  # Retours à la ligne pour les longs textes
                    words = doc_text.split()
                    lines = []
                    current_line = []
                    for word in words:
                        if len(' '.join(current_line + [word])) > 18:
                            if current_line:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                            else:
                                lines.append(word)
                        else:
                            current_line.append(word)
                    if current_line:
                        lines.append(' '.join(current_line))
                    doc_text = '\\n'.join(lines)
                
                dot.node(doc_id, doc_text, 
                        shape='note',
                        fillcolor=COLORS['documents'],
                        fontcolor=COLORS['documents_text'],
                        penwidth='1.5',
                        color=COLORS['documents_border'],
                        fontsize='20',             # Taille optimisée
                        width='2.6', height='1.4') # Taille compacte
            
            # ACTEUR À DROITE avec style personnalisé et taille optimisée
            if actor_id:
                actor_text = step['actor']
                if len(actor_text) > 12:  # Retours à la ligne pour les longs noms
                    words = actor_text.split()
                    lines = []
                    current_line = []
                    for word in words:
                        if len(' '.join(current_line + [word])) > 12:
                            if current_line:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                            else:
                                lines.append(word)
                        else:
                            current_line.append(word)
                    if current_line:
                        lines.append(' '.join(current_line))
                    actor_text = '\\n'.join(lines)
                
                dot.node(actor_id, actor_text, 
                        shape='ellipse',
                        fillcolor=COLORS['actors'],
                        fontcolor=COLORS['actors_text'],
                        penwidth='1.5',
                        color=COLORS['actors_border'],
                        fontsize='20',             # Taille optimisée
                        width='2.6', height='1.4') # Taille compacte
            
            # ALIGNEMENT HORIZONTAL FORCÉ (structure préservée)
            with dot.subgraph() as align:
                align.attr(rank='same')
                
                align.node(left_anchor, '', style='invis', width='0.1', height='0.1')
                
                if doc_id:
                    align.node(doc_id, doc_text, 
                              shape='note', fillcolor=COLORS['documents'],
                              fontcolor=COLORS['documents_text'],
                              penwidth='1.5', color=COLORS['documents_border'],
                              width='2.6', height='1.4', fontsize='20')
                
                align.node(step_id, step_label, 
                          shape='diamond' if is_decision else 'box', 
                          fillcolor=COLORS['steps'],
                          fontcolor=COLORS['steps_text'],
                          penwidth='1.5',
                          width='3.2' if is_decision else '3.2', 
                          height='2.2' if is_decision else '1.6',
                          fontsize='22' if is_decision else '24')
                
                if actor_id:
                    align.node(actor_id, actor_text, 
                              shape='ellipse', fillcolor=COLORS['actors'],
                              fontcolor=COLORS['actors_text'],
                              penwidth='1.5', color=COLORS['actors_border'],
                              width='2.6', height='1.4', fontsize='20')
                
                align.node(right_anchor, '', style='invis', width='0.1', height='0.1')
            
            # Connexions invisibles pour espacement
            dot.edge(left_anchor, step_id, style='invis')
            dot.edge(step_id, right_anchor, style='invis')
            
            # CONNEXIONS VISIBLES subtiles et élégantes
            if doc_id:
                dot.edge(doc_id, step_id, 
                        constraint='false',
                        color=COLORS['flow_connect'],
                        arrowhead='none',
                        penwidth='1.2',            # Trait fin
                        style='solid')
                        
            if actor_id:
                dot.edge(step_id, actor_id, 
                        constraint='false',
                        color=COLORS['flow_connect'],
                        arrowhead='none',
                        penwidth='1.2',            # Trait fin
                        style='solid')
            
            previous_step = step_id
        
        # FIN DYNAMIQUE avec style moderne et taille optimisée
        end_formatted = end_text
        if len(end_text) > 25:
            words = end_text.split()
            lines = []
            current_line = []
            for word in words:
                if len(' '.join(current_line + [word])) > 25:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
                else:
                    current_line.append(word)
            if current_line:
                lines.append(' '.join(current_line))
            end_formatted = '\\n'.join(lines)
        
        dot.node('fin', end_formatted, 
                shape='ellipse',
                fillcolor=COLORS['end'],
                fontcolor='white',
                fontsize='26',                 # Taille optimisée
                fontweight='bold',
                penwidth='1.5',
                width='2.2', height='1.2')     # Taille compacte
        dot.edge(previous_step, 'fin', 
                color=COLORS['flow_main'],
                penwidth='1.5',                # Trait fin
                arrowsize='0.8')
        
        # Génération de l'image haute qualité
        print("🎨 Génération de l'image...")
        img_bytes = dot.pipe(format='png')
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        print("✅ Logigramme généré avec succès !")
        return img_base64, None
    
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None, f"Erreur lors de la génération du logigramme: {str(e)}"

# Fonction de remplacement pour votre code existant (SIGNATURE INCHANGÉE)
def generate_flowchart(procedure_text: str, title: str = "Logigramme de procédure", io_table_text: str = None) -> tuple:
    """
    Génère un logigramme à partir d'une procédure au format Markdown
    VERSION CORRIGÉE avec extraction robuste
    """
    return generate_flowchart_improved(procedure_text, io_table_text, title)