"""
Module de génération de logigrammes AMÉLIORÉ avec design professionnel
Structure PRÉSERVÉE : Document (GAUCHE) ← Étape (CENTRE) → Acteur (DROITE)
Palette moderne, typographie élégante, connexions subtiles
LISIBILITÉ AMÉLIORÉE : Texte plus grand et plus contrasté
"""

from graphviz import Digraph
import base64
from io import BytesIO

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

def extract_steps_from_procedure(markdown_text: str) -> list:
    """
    Extrait les étapes d'une procédure à partir d'un tableau Markdown
    """
    if not markdown_text:
        return []
        
    lines = [line.strip() for line in markdown_text.split('\n') if '|' in line]
    if len(lines) < 3:
        return []
    
    headers = [h.strip().lower() for h in lines[0].split('|')[1:-1]]
    data_rows = lines[2:]
    
    steps = []
    for row in data_rows:
        cols = [col.strip() for col in row.split('|')[1:-1]]
        if len(cols) >= len(headers):
            step = {}
            for i, header in enumerate(headers):
                if i < len(cols):
                    value = cols[i]
                    if 'n°' in header or 'numero' in header:
                        step['number'] = value
                    elif 'acteur' in header:
                        step['actor'] = value
                    elif 'activité' in header or 'activite' in header:
                        step['activity'] = value
                    elif 'document' in header:
                        step['document'] = value
            if step:
                steps.append(step)
    
    return steps

def generate_flowchart_improved(procedure_text: str, title: str = "Logigramme de procédure") -> tuple:
    """
    Génère un logigramme avec DESIGN PROFESSIONNEL et LISIBILITÉ AMÉLIORÉE
    Texte plus grand, meilleur contraste, police plus lisible
    """
    try:
        steps = extract_steps_from_procedure(procedure_text)
        
        if not steps:
            return None, "Aucune étape n'a pu être extraite de la procédure"
        
        # Configuration du graphe avec design moderne et lisibilité améliorée
        dot = Digraph(
            comment=title,
            engine='dot',
            graph_attr={
                'rankdir': 'TB',
                'splines': 'ortho',
                'nodesep': '3.0',              # Espacement horizontal optimisé
                'ranksep': '2.5',              # Espacement vertical optimisé
                'compound': 'true',
                'bgcolor': COLORS['background'],
                'pad': '1.0',                  # Padding augmenté
                'dpi': '200',                  # Résolution optimisée
                'fontname': 'Arial Bold',      # Police plus lisible
                'style': 'rounded',
                'size': '50,50!'               # Taille max contrôlée
            },
            node_attr={
                'fontname': 'Arial Black',     # Police la plus grasse possible
                'fontsize': '48',              # TAILLE ÉNORME !!!
                'style': 'filled,rounded',
                'penwidth': '3',               # Bordures très épaisses
                'margin': '0.5'                # Marge interne très augmentée
            },
            edge_attr={
                'arrowsize': '1.5',            # Flèches plus grandes
                'fontname': 'Arial Bold',
                'fontsize': '28',              # Taille TRÈS augmentée
                'penwidth': '3'                # Traits plus épais
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
        
        # DÉBUT avec style moderne et lisible
        dot.node('debut', 'DÉBUT', 
                shape='ellipse',
                fillcolor=COLORS['start'],
                fontcolor='white',
                fontsize='56',                 # Taille ÉNORME
                fontweight='bold',
                penwidth='3',
                width='4.0', height='2.5')     # Taille ÉNORME
        
        previous_step = 'debut'
        
        # Traitement de chaque étape avec design amélioré et plus lisible
        for i, step in enumerate(steps):
            step_id = f"step_{i}"
            
            # Détection des décisions
            is_decision = any(keyword in step['activity'].lower() 
                           for keyword in ['décision', 'vérification', '?', 'si ', 'conditionnel', 'choix'])
            
            # Formatage du texte avec retours à la ligne pour améliorer la lisibilité
            step_text = step['activity']
            if len(step_text) > 25:  # Si le texte est long, on le divise
                words = step_text.split()
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
                step_text = '\\n'.join(lines)
            
            step_label = f"{step['number']}\\n{step_text}"
            
            # ÉTAPE CENTRALE avec style professionnel et plus lisible
            if is_decision:
                dot.node(step_id, step_label, 
                        shape='diamond',
                        fillcolor=COLORS['steps'],
                        fontcolor=COLORS['steps_text'],
                        fontweight='bold',
                        fontsize='44',             # Taille ÉNORME
                        penwidth='3',
                        width='8.0', height='5.0') # Taille ÉNORME
            else:
                dot.node(step_id, step_label, 
                        shape='box',
                        fillcolor=COLORS['steps'],
                        fontcolor=COLORS['steps_text'],
                        fontsize='48',             # Taille ÉNORME
                        penwidth='3',
                        width='8.0', height='3.5') # Taille ÉNORME
            
            # Connexion verticale principale avec style élégant
            dot.edge(previous_step, step_id, 
                    color=COLORS['flow_main'],
                    penwidth='3',              # Trait plus épais
                    arrowsize='1.2')
            
            # IDs pour document et acteur
            doc_id = f"doc_{i}" if step.get('document') and step['document'].strip() else None
            actor_id = f"actor_{i}" if step.get('actor') and step['actor'].strip() else None
            
            # Ancres invisibles pour alignement parfait
            left_anchor = f"left_anchor_{i}"
            right_anchor = f"right_anchor_{i}"
            
            dot.node(left_anchor, '', style='invis', width='0.1', height='0.1')
            dot.node(right_anchor, '', style='invis', width='0.1', height='0.1')
            
            # DOCUMENT À GAUCHE avec style carte élégante et plus lisible
            if doc_id:
                doc_text = step['document']
                if len(doc_text) > 20:  # Retours à la ligne pour les longs textes
                    words = doc_text.split()
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
                    doc_text = '\\n'.join(lines)
                
                dot.node(doc_id, doc_text, 
                        shape='note',
                        fillcolor=COLORS['documents'],
                        fontcolor=COLORS['documents_text'],
                        penwidth='3',
                        color=COLORS['documents_border'],
                        fontsize='40',             # Taille ÉNORME
                        width='6.0', height='3.0') # Taille ÉNORME
            
            # ACTEUR À DROITE avec style personnalisé et plus lisible
            if actor_id:
                actor_text = step['actor']
                if len(actor_text) > 15:  # Retours à la ligne pour les longs noms
                    words = actor_text.split()
                    lines = []
                    current_line = []
                    for word in words:
                        if len(' '.join(current_line + [word])) > 15:
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
                        penwidth='3',
                        color=COLORS['actors_border'],
                        fontsize='40',             # Taille ÉNORME
                        width='6.0', height='3.0') # Taille ÉNORME
            
            # ALIGNEMENT HORIZONTAL FORCÉ (structure préservée)
            with dot.subgraph() as align:
                align.attr(rank='same')
                
                align.node(left_anchor, '', style='invis', width='0.1', height='0.1')
                
                if doc_id:
                    align.node(doc_id, doc_text, 
                              shape='note', fillcolor=COLORS['documents'],
                              fontcolor=COLORS['documents_text'],
                              penwidth='3', color=COLORS['documents_border'],
                              width='6.0', height='3.0', fontsize='40')
                
                align.node(step_id, step_label, 
                          shape='diamond' if is_decision else 'box', 
                          fillcolor=COLORS['steps'],
                          fontcolor=COLORS['steps_text'],
                          penwidth='3',
                          width='8.0' if is_decision else '8.0', 
                          height='5.0' if is_decision else '3.5',
                          fontsize='44' if is_decision else '48')
                
                if actor_id:
                    align.node(actor_id, actor_text, 
                              shape='ellipse', fillcolor=COLORS['actors'],
                              fontcolor=COLORS['actors_text'],
                              penwidth='3', color=COLORS['actors_border'],
                              width='6.0', height='3.0', fontsize='40')
                
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
                        penwidth='2',              # Trait plus épais
                        style='solid')
                        
            if actor_id:
                dot.edge(step_id, actor_id, 
                        constraint='false',
                        color=COLORS['flow_connect'],
                        arrowhead='none',
                        penwidth='2',              # Trait plus épais
                        style='solid')
            
            previous_step = step_id
        
        # FIN avec style moderne et lisible
        dot.node('fin', 'FIN', 
                shape='ellipse',
                fillcolor=COLORS['end'],
                fontcolor='white',
                fontsize='56',                 # Taille ÉNORME
                fontweight='bold',
                penwidth='3',
                width='4.0', height='2.5')     # Taille ÉNORME
        dot.edge(previous_step, 'fin', 
                color=COLORS['flow_main'],
                penwidth='3',                  # Trait plus épais
                arrowsize='1.2')
        
        # Génération de l'image haute qualité
        img_bytes = dot.pipe(format='png')
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return img_base64, None
    
    except Exception as e:
        return None, f"Erreur lors de la génération du logigramme: {str(e)}"

# Fonction de remplacement pour votre code existant
def generate_flowchart(procedure_text: str, title: str = "Logigramme de procédure") -> tuple:
    """
    Fonction de remplacement avec le nouveau design et lisibilité améliorée
    Compatible avec votre code existant
    """
    return generate_flowchart_improved(procedure_text, title)