"""
Translation utilities for the University Website Information Collector
"""

try:
    import streamlit as st
except ImportError:
    st = None

try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False
    Translator = None

import time
from typing import Dict, List, Optional

class TranslationManager:
    def __init__(self):
        self.cache = {}
        if GOOGLETRANS_AVAILABLE:
            self.translator = Translator()
        else:
            self.translator = None
            print("⚠️ Google Translate not available. Using fallback translation method.")
        
    def detect_language(self, text: str) -> str:
        """Detect the language of the given text"""
        try:
            if len(text.strip()) < 3:
                return 'en'
            
            # Check cache first
            cache_key = f"detect_{hash(text[:100])}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            if self.translator:
                detection = self.translator.detect(text)
                language = detection.lang
            else:
                # Fallback: simple heuristic detection
                language = self._simple_language_detection(text)
            
            # Cache the result
            self.cache[cache_key] = language
            return language
            
        except Exception as e:
            print(f"Language detection failed: {e}")
            return 'en'  # Default to English
    
    def _simple_language_detection(self, text: str) -> str:
        """Simple heuristic language detection as fallback"""
        text_lower = text.lower()
        
        # Common language patterns
        if any(word in text_lower for word in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']):
            return 'en'
        elif any(word in text_lower for word in ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'uno', 'esta', 'este', 'esta', 'estos', 'estas']):
            return 'es'
        elif any(word in text_lower for word in ['le', 'de', 'et', 'à', 'un', 'il', 'que', 'ne', 'se', 'pas', 'pour', 'par', 'sur', 'avec', 'une', 'des', 'du', 'la', 'les', 'en', 'ce', 'son', 'sa', 'ses', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'notre', 'nos', 'votre', 'vos', 'leur', 'leurs']):
            return 'fr'
        elif any(word in text_lower for word in ['der', 'die', 'das', 'und', 'oder', 'aber', 'in', 'auf', 'an', 'zu', 'für', 'von', 'mit', 'durch', 'über', 'unter', 'zwischen', 'während', 'nach', 'vor', 'bei', 'seit', 'bis', 'ohne', 'gegen', 'um', 'entlang', 'trotz', 'wegen', 'statt', 'anstatt']):
            return 'de'
        else:
            return 'en'  # Default to English
    
    def translate_text(self, text: str, target_lang: str = 'en', source_lang: str = None) -> str:
        """Translate text to target language"""
        try:
            if not text or len(text.strip()) < 3:
                return text
            
            # Check cache first
            cache_key = f"translate_{hash(text[:100])}_{target_lang}_{source_lang or 'auto'}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            if self.translator:
                # Use Google Translate
                result = self.translator.translate(
                    text, 
                    dest=target_lang, 
                    src=source_lang
                )
                translated_text = result.text
            else:
                # Fallback: return original text with translation notice
                if target_lang != 'en':
                    translated_text = f"[{target_lang.upper()}] {text}"
                else:
                    translated_text = text
            
            # Cache the result
            self.cache[cache_key] = translated_text
            return translated_text
            
        except Exception as e:
            print(f"Translation failed: {e}")
            return text  # Return original text if translation fails
    
    def translate_page_content(self, page: Dict, target_lang: str = 'en') -> Dict:
        """Translate all text content in a page"""
        translated_page = page.copy()
        
        # Translate title
        if 'title' in page and page['title']:
            translated_page['title'] = self.translate_text(page['title'], target_lang)
        
        # Translate content
        if 'content' in page and page['content']:
            translated_page['content'] = self.translate_text(page['content'], target_lang)
        
        # Translate meta description
        if 'meta_description' in page and page['meta_description']:
            translated_page['meta_description'] = self.translate_text(page['meta_description'], target_lang)
        
        return translated_page
    
    def translate_section_analysis(self, section_analysis: Dict, target_lang: str = 'en', progress_callback=None) -> Dict:
        """Translate section analysis results with optional progress callback"""
        translated_analysis = section_analysis.copy()
        
        total_items = 0
        current_item = 0
        
        # Count total items to translate
        for section in translated_analysis.get('sections', []):
            total_items += 2  # section name and definition
            for subsection in section.get('subsections', []):
                total_items += 2  # subsection name and definition
                total_items += len(subsection.get('relevant_pages', [])) * 2  # page title and content
        
        for section in translated_analysis.get('sections', []):
            # Translate section name and definition
            section['section_name'] = self.translate_text(section.get('section_name', ''), target_lang)
            current_item += 1
            if progress_callback:
                progress_callback(current_item, total_items, f"Translating section: {section.get('section_name', '')}")
            
            section['section_definition'] = self.translate_text(section.get('section_definition', ''), target_lang)
            current_item += 1
            if progress_callback:
                progress_callback(current_item, total_items, f"Translating section definition...")
            
            for subsection in section.get('subsections', []):
                # Translate subsection name and definition
                subsection['subsection_name'] = self.translate_text(subsection.get('subsection_name', ''), target_lang)
                current_item += 1
                if progress_callback:
                    progress_callback(current_item, total_items, f"Translating subsection: {subsection.get('subsection_name', '')}")
                
                subsection['subsection_definition'] = self.translate_text(subsection.get('subsection_definition', ''), target_lang)
                current_item += 1
                if progress_callback:
                    progress_callback(current_item, total_items, f"Translating subsection definition...")
                
                # Translate relevant pages
                for page in subsection.get('relevant_pages', []):
                    page['page_title'] = self.translate_text(page.get('page_title', ''), target_lang)
                    current_item += 1
                    if progress_callback:
                        progress_callback(current_item, total_items, f"Translating page: {page.get('page_title', '')}")
                    
                    page['content'] = self.translate_text(page.get('content', ''), target_lang)
                    current_item += 1
                    if progress_callback:
                        progress_callback(current_item, total_items, f"Translating page content...")
        
        return translated_analysis

# Language options for the UI
LANGUAGE_OPTIONS = {
    'English': 'en',
    'Spanish': 'es',
    'French': 'fr',
    'German': 'de',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Chinese (Simplified)': 'zh-cn',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Arabic': 'ar',
    'Hindi': 'hi',
    'Dutch': 'nl',
    'Swedish': 'sv',
    'Norwegian': 'no',
    'Danish': 'da',
    'Finnish': 'fi',
    'Polish': 'pl',
    'Czech': 'cs',
    'Hungarian': 'hu',
    'Greek': 'el',
    'Turkish': 'tr',
    'Hebrew': 'he',
    'Thai': 'th',
    'Vietnamese': 'vi',
    'Indonesian': 'id',
    'Malay': 'ms',
    'Filipino': 'tl',
    'Ukrainian': 'uk',
    'Bulgarian': 'bg',
    'Croatian': 'hr',
    'Romanian': 'ro',
    'Slovak': 'sk',
    'Slovenian': 'sl',
    'Estonian': 'et',
    'Latvian': 'lv',
    'Lithuanian': 'lt'
}

def get_language_name(lang_code: str) -> str:
    """Get language name from language code"""
    for name, code in LANGUAGE_OPTIONS.items():
        if code == lang_code:
            return name
    return lang_code
