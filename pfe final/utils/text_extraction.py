import pytesseract
import pdf2image
import re
import io
from PIL import Image
import streamlit as st
import tempfile
import os

@st.cache_data
def extract_text_from_pdf_with_tesseract(pdf_file):
    """
    Extrait le texte d'un fichier PDF en utilisant pytesseract après conversion en images.
    Retourne le texte à partir du mot "DECIDE" si présent.
    """
    try:
        # Créer un fichier temporaire pour sauvegarder le PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            temp_pdf.write(pdf_file.getvalue())
            temp_pdf_path = temp_pdf.name
            
        # Convertir les pages du PDF en images
        images = pdf2image.convert_from_path(temp_pdf_path)
        
        # Nettoyer le fichier temporaire
        os.unlink(temp_pdf_path)
        
        full_text = ""
        for img in images:
            # Utiliser pytesseract pour extraire le texte de chaque image
            text = pytesseract.image_to_string(img, lang='fra')
            full_text += text + " "
        
        # Rechercher le mot "DECIDE" et extraire tout le texte après ce mot
        decide_pattern = re.compile(r'DECIDE', re.IGNORECASE)
        decide_match = decide_pattern.search(full_text)
        
        if decide_match:
            # Extraire à partir du mot "DECIDE"
            extracted_text = full_text[decide_match.start():]
            return extracted_text.strip()
        else:
            # Si le mot "DECIDE" n'est pas trouvé, retourner tout le texte
            return full_text.strip()
    
    except Exception as e:
        st.error(f"Erreur lors de l'extraction du texte: {e}")
        return None

@st.cache_data
def extract_articles_from_text(text):
    """
    Extrait les articles structurés à partir du texte brut.
    Recherche les patterns comme "Article X :" ou "Article premier :"
    """
    if not text:
        return {}
    
    # Nettoyer le texte
    text = text.replace('\n', ' ').strip()
    
    # Pattern pour détecter les articles
    article_pattern = r'(?:Article\s+(?:premier|[0-9]+)\s*:?\s*)(.*?)(?=Article\s+(?:premier|[0-9]+)\s*:|\Z)'
    
    # Trouver tous les articles
    articles = re.findall(article_pattern, text, re.IGNORECASE | re.DOTALL)
    
    # Extraire les numéros d'articles
    article_numbers = re.findall(r'Article\s+(premier|[0-9]+)', text, re.IGNORECASE)
    
    # Créer un dictionnaire avec les articles numérotés
    articles_dict = {}
    for i, article_text in enumerate(articles):
        if i < len(article_numbers):
            number = article_numbers[i]
            if number.lower() == 'premier':
                number = '1'
            articles_dict[f"Article {number}"] = article_text.strip()
    
    return articles_dict