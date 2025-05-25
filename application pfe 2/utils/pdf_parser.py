"""
Module pour extraire du texte des fichiers PDF.
Ce module fournit des fonctions pour le traitement des documents PDF
et l'extraction de leur contenu textuel.
"""

import os
import re
import io
import logging
from pathlib import Path
from typing import Union, Optional, List, Dict

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import PyPDF2
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    from pdfminer.layout import LAParams
    HAS_PDF_LIBS = True
except ImportError:
    logger.warning("Les bibliothèques PDF (PyPDF2, pdfminer.six) ne sont pas installées. "
                 "L'extraction de texte des PDFs sera limitée.")
    HAS_PDF_LIBS = False

def extract_text_from_pdf(pdf_path: Union[str, Path], 
                         use_pdfminer: bool = True, 
                         clean_text: bool = True) -> str:
    """
    Extrait le texte d'un fichier PDF en utilisant PyPDF2 ou pdfminer.six.
    
    Args:
        pdf_path (Union[str, Path]): Chemin vers le fichier PDF.
        use_pdfminer (bool, optional): Utiliser pdfminer.six pour l'extraction. Defaults to True.
        clean_text (bool, optional): Nettoyer le texte extrait. Defaults to True.
        
    Returns:
        str: Le texte extrait du PDF.
        
    Raises:
        FileNotFoundError: Si le fichier PDF n'existe pas.
        ValueError: Si le format du fichier n'est pas valide.
        Exception: Pour les autres erreurs.
    """
    if not HAS_PDF_LIBS:
        raise ImportError("Les bibliothèques PDF (PyPDF2, pdfminer.six) ne sont pas installées. "
                         "Veuillez les installer avec 'pip install PyPDF2 pdfminer.six'")
    
    # Conversion du chemin en objet Path
    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)
    
    # Vérification de l'existence du fichier
    if not pdf_path.exists():
        raise FileNotFoundError(f"Le fichier {pdf_path} n'existe pas.")
    
    # Vérification de l'extension du fichier
    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError(f"Le fichier {pdf_path} n'est pas un fichier PDF.")
    
    try:
        extracted_text = ""
        
        # Extraction avec pdfminer.six (meilleure qualité mais plus lent)
        if use_pdfminer:
            laparams = LAParams(
                line_margin=0.5,
                word_margin=0.1,
                char_margin=2.0,
                all_texts=True
            )
            extracted_text = pdfminer_extract_text(
                str(pdf_path), 
                laparams=laparams
            )
        
        # Si pdfminer échoue ou n'est pas utilisé, fallback sur PyPDF2
        if not extracted_text or not use_pdfminer:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                # Extraction du texte page par page
                page_texts = []
                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        page_texts.append(page_text)
                
                extracted_text = "\n\n".join(page_texts)
        
        # Nettoyage du texte si demandé
        if clean_text:
            extracted_text = clean_extracted_text(extracted_text)
        
        return extracted_text
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte du PDF {pdf_path}: {str(e)}")
        raise
    
def clean_extracted_text(text: str) -> str:
    """
    Nettoie le texte extrait d'un PDF.
    
    Args:
        text (str): Le texte à nettoyer.
        
    Returns:
        str: Le texte nettoyé.
    """
    if not text:
        return ""
    
    # Conversion des sauts de ligne multiples en un seul
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Suppression des espaces multiples
    text = re.sub(r' {2,}', ' ', text)
    
    # Suppression des caractères non imprimables
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    # Normalisation des tirets et guillemets
    text = text.replace('–', '-').replace('—', '-').replace(''', "'").replace(''', "'")
    text = text.replace('"', '"').replace('"', '"')
    
    # Suppression des lignes vides en début et fin de texte
    text = text.strip()
    
    return text

def extract_sections_from_text(text: str, section_patterns: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Extrait des sections spécifiques du texte en fonction des motifs de section fournis.
    
    Args:
        text (str): Le texte à analyser.
        section_patterns (Optional[List[str]], optional): Liste des motifs regex pour identifier les sections.
            Defaults to None.
        
    Returns:
        Dict[str, str]: Dictionnaire avec les noms de section comme clés et le contenu comme valeurs.
    """
    if not text:
        return {}
    
    # Patterns par défaut pour les sections courantes dans les notes circulaires
    if section_patterns is None:
        section_patterns = [
            r'(?i)(?:objet|sujet)\s*:\s*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)(?:référence[s]?)\s*:\s*(.*?)(?=\n\n|\n[A-Z]|$)',
            r'(?i)(?:contexte|introduction)\s*:?\s*(.*?)(?=\n\n\d+\.|\n\n[A-Z]|$)',
            r'(?i)(?:procédure|processus)\s*:?\s*(.*?)(?=\n\n\d+\.|\n\n[A-Z]|$)'
        ]
    
    sections = {}
    
    # Extraction des sections selon les motifs
    for pattern in section_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            # Déterminer le nom de la section en fonction du motif
            section_name = re.search(r'(?i)(\w+)\s*:', pattern).group(1).capitalize()
            sections[section_name] = match.group(1).strip()
    
    # Si aucune section n'a été trouvée, utiliser le texte entier comme "Contenu"
    if not sections:
        sections["Contenu"] = text
    
    return sections

def extract_metadata_from_pdf(pdf_path: Union[str, Path]) -> Dict[str, str]:
    """
    Extrait les métadonnées d'un fichier PDF.
    
    Args:
        pdf_path (Union[str, Path]): Chemin vers le fichier PDF.
        
    Returns:
        Dict[str, str]: Dictionnaire des métadonnées du PDF.
    """
    if not HAS_PDF_LIBS:
        return {"error": "Les bibliothèques PDF ne sont pas installées."}
    
    # Conversion du chemin en objet Path
    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)
    
    # Vérification de l'existence du fichier
    if not pdf_path.exists():
        return {"error": f"Le fichier {pdf_path} n'existe pas."}
    
    try:
        metadata = {}
        
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if reader.metadata:
                # Extraction des métadonnées standard
                for key, value in reader.metadata.items():
                    if key.startswith('/'):
                        key = key[1:]  # Supprimer le '/' initial
                    metadata[key] = str(value)
            
            # Ajout d'informations supplémentaires
            metadata["PageCount"] = len(reader.pages)
            
        return metadata
    
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des métadonnées du PDF {pdf_path}: {str(e)}")
        return {"error": str(e)}