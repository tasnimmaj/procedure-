"""
Page 4: Analyse des Acteurs
"""
import streamlit as st
import pandas as pd
from io import BytesIO
from utils.actors_extractor import extract_actors_from_procedure_table, get_actors_summary
from utils.styles import apply_green_theme

# Configuration de la page
st.set_page_config(
    page_title="Analyse des Acteurs",
    page_icon="👥",
    layout="wide"
)

# Appliquer le thème vert
apply_green_theme()

def main():
    # Affichage de l'état dans la sidebar
    if st.session_state.get("note_circulaire") and st.session_state.get("note_title"):
        st.sidebar.success(f"✅ Note circulaire présente: {st.session_state.note_title}")
    else:
        st.sidebar.warning("❌ Aucune note circulaire")
        
    if st.session_state.get("procedure_generee"):
        st.sidebar.success("✅ Procédure générée")
    else:
        st.sidebar.warning("❌ Aucune procédure générée")

    st.title("👥 Analyse des Acteurs")
    
    # Récupérer la procédure générée depuis la session
    procedure_generee = st.session_state.get('procedure_generee', {})
    procedure_text = procedure_generee.get('procedure', '') if isinstance(procedure_generee, dict) else procedure_generee
    
    if procedure_text:
        try:
            # Extraire les acteurs et leurs activités
            actors_data = extract_actors_from_procedure_table(procedure_text)
            
            if actors_data:
                # Afficher le résumé des statistiques
                summary = get_actors_summary(actors_data)
                
                # Créer trois colonnes pour les statistiques
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total des Acteurs", summary['total_acteurs'])
                
                with col2:
                    st.metric("Total des Activités", summary['total_activites'])
                
                with col3:
                    if summary['acteur_plus_actif']:
                        st.metric("Acteur le Plus Actif", 
                                f"{summary['acteur_plus_actif']['nom_acteur']} ({summary['acteur_plus_actif']['nombre_activites']} activités)")
                
                # Créer un DataFrame avec toutes les activités des acteurs pour l'export
                all_activities = []
                for actor in actors_data:
                    actor_name = actor['nom_acteur']
                    for activity in actor['activites']:
                        activity_row = {
                            'Acteur': actor_name,
                            'N°': activity['numero'],
                            'Activité': activity['activite'],
                            'Description': activity['description']
                        }
                        all_activities.append(activity_row)
                
                df_activities = pd.DataFrame(all_activities)
                
                # Affichage des acteurs et leurs activités dans un tableau Markdown
                st.markdown("### 📋 Tableau des Acteurs et leurs Activités")
                
                # En-tête du tableau
                table_md = "| Acteur | Activités |\n|--------|------------|\n"
                
                # Créer le tableau avec les activités groupées par acteur
                for actor_info in actors_data:
                    actor_name = actor_info['nom_acteur']
                    activities = actor_info['activites']  # Les activités sont déjà triées par numéro
                    
                    # Formatter toutes les activités de l'acteur avec retour à la ligne
                    activities_text = "<br>".join([f"Étape {act['numero']}: {act['activite']}" for act in activities])
                    
                    # Ajouter la ligne au tableau
                    table_md += f"| {actor_name} | {activities_text} |\n"
                
                # Afficher le tableau
                st.markdown(table_md, unsafe_allow_html=True)
                
                # Statistiques globales
                st.markdown("### 📊 Statistiques")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Nombre total d'acteurs", len(actors_data))
                with col2:
                    total_activities = sum(len(actor['activites']) for actor in actors_data)
                    st.metric("Nombre total d'activités", total_activities)
                with col3:
                    avg_activities = round(total_activities / len(actors_data), 2) if actors_data else 0
                    st.metric("Moyenne d'activités par acteur", avg_activities)
                
                # Section d'export des données
                st.header("💾 Export des Données")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Export CSV
                    csv_data = df_activities.to_csv(index=False, encoding='utf-8')
                    st.download_button(
                        label="📊 Télécharger CSV",
                        data=csv_data,
                        file_name="acteurs_activites.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Export Excel
                    excel_buffer = BytesIO()
                    df_activities.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_data = excel_buffer.getvalue()
                    st.download_button(
                        label="📑 Télécharger Excel",
                        data=excel_data,
                        file_name="acteurs_activites.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
            else:
                st.warning("⚠️ Aucun acteur trouvé dans le tableau. Vérifiez le format de votre tableau.")
                
        except Exception as e:
            st.error(f"❌ Erreur lors de l'analyse : {str(e)}")
    else:
        st.info("ℹ️ Veuillez d'abord générer une procédure dans l'onglet 'Tableau Procédures'.")
    
    

if __name__ == "__main__":
    main()