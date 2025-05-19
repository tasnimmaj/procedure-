"""
Module de génération de logigrammes à partir de procédures textuelles structurées (tableaux Markdown)
"""

import re
import graphviz
import matplotlib.pyplot as plt
import networkx as nx
import textwrap
from matplotlib.patches import Ellipse, Rectangle

sizing = {
    'node_width': 1.5,
    'node_height': 0.8,
    'io_width': 2.0,
    'io_height': 1.0,
    'x_activity': 0,
    'x_actor': 4,
}

def extract_activities_and_actors(procedure_text):
    activities, actors = [], []
    lines = procedure_text.split('\n')
    data_lines = [l for l in lines if re.match(r"^\|\s*\d+\s*\|", l)]
    for line in data_lines:
        cols = line.strip().split('|')
        if len(cols) >= 6:
            act = cols[2].strip().strip('*')
            actr = cols[4].split(',')[0].strip().strip('*')
            activities.append(act)
            actors.append(actr)
    return activities, actors

def draw_flowchart_matplotlib(activities, actors):
    n = len(activities)
    G = nx.DiGraph()
    for i in range(1, n+1):
        G.add_edge(f"A{i}", f"P{i}")
        if i == 1:
            G.add_edge("Entrée", f"A{i}")
        else:
            G.add_edge(f"A{i-1}", f"A{i}")
        if i == n:
            G.add_edge(f"A{i}", "Sortie")
    pos = {}
    for i in range(1, n+1):
        y = n + 1 - i
        pos[f"A{i}"] = (sizing['x_activity'], y)
        pos[f"P{i}"] = (sizing['x_actor'], y)
    pos['Entrée'] = (sizing['x_activity'], n+1)
    pos['Sortie'] = (sizing['x_activity'], 0)
    fig, ax = plt.subplots(figsize=(8, n * 1.5 + 3))
    ax.set_xlim(sizing['x_activity'] - sizing['node_width'] - 1,
                sizing['x_actor'] + sizing['node_width'] + 1)
    ax.set_ylim(-1, n+2)
    for label in ['Entrée', 'Sortie']:
        x, y = pos[label]
        rect = Rectangle((x - sizing['io_width']/2, y - sizing['io_height']/2),
                         sizing['io_width'], sizing['io_height'], facecolor='#aed6f1')
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=10)
    for i, act in enumerate(activities, start=1):
        x, y = pos[f"A{i}"]
        e = Ellipse((x, y), width=sizing['node_width'], height=sizing['node_height'],
                    facecolor='#5dade2', alpha=0.9)
        ax.add_patch(e)
        wrapped = textwrap.fill(act, width=20)
        ax.text(x, y, wrapped, ha='center', va='center', fontsize=9)
    for i, actr in enumerate(actors, start=1):
        x, y = pos[f"P{i}"]
        rect = Rectangle((x - sizing['node_width']/2, y - sizing['node_height']/2),
                         sizing['node_width'], sizing['node_height'], facecolor='#52be80', alpha=0.9)
        ax.add_patch(rect)
        wrapped = textwrap.fill(actr, width=20)
        ax.text(x, y, wrapped, ha='center', va='center', fontsize=9)
    for u, v in G.edges():
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=1.2, color='gray'))
    ax.axis('off')
    plt.tight_layout()
    return fig

# Optionnel : pour compatibilité avec l'ancien code

def extract_steps_from_procedure(procedure_text):
    activities, actors = extract_activities_and_actors(procedure_text)
    steps = []
    for i, (act, actr) in enumerate(zip(activities, actors), 1):
        steps.append({
            "id": i,
            "content": act,
            "actor": actr,
            "type": "action",
            "next": i+1 if i < len(activities) else None
        })
    return steps

def generate_flowchart(steps):
    graph = graphviz.Digraph(format='svg')
    graph.attr(rankdir='TB', size='8,11', dpi='300')
    graph.node('start', 'Début', shape='oval', style='filled', fillcolor='lightgrey')
    graph.node('end', 'Fin', shape='oval', style='filled', fillcolor='lightgrey')
    if steps:
        graph.edge('start', f"step_{steps[0]['id']}")
    for step in steps:
        node_id = f"step_{step['id']}"
        label = f"Étape {step['id']}\n{step['content']}\nActeur: {step['actor']}"
        graph.node(node_id, label, shape='box', style='filled', fillcolor='lightblue')
        if step["next"]:
            graph.edge(node_id, f"step_{step['next']}")
        else:
            graph.edge(node_id, 'end')
    return graph

def get_flowchart_from_text(procedure_text):
    """
    Fonction principale pour générer un logigramme à partir d'un texte de procédure
    
    Args:
        procedure_text (str): Le texte de la procédure
        
    Returns:
        graphviz.Digraph: Le logigramme généré
    """
    steps = extract_steps_from_procedure(procedure_text)
    flowchart = generate_flowchart(steps)
    return flowchart