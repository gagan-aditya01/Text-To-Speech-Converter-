"""
translation_service.py
----------------------
Service layer for text translation using deep-translator.
"""

import logging
from typing import Optional
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

def translate_text(text: str, target_lang_code: str) -> str:
    """
    Translates input text from its auto-detected language to the target language.
    
    Args:
        text: The text to translate.
        target_lang_code: BCP-47 language code (e.g. 'fr', 'hi', 'zh-CN') of the target language.
        
    Returns:
        The translated text. If translation fails, falls back to the original text.
    """
    if not text.strip():
        return text
    
    # Optional performance optimization: if target is English and we suspect it's English,
    # or just trust GoogleTranslator source='auto' and target='en'.
    # Note: BCP-47 codes mostly map 1:1, but deep-translator uses standard ISO 639-1.
    # Google Translator handles 'zh-CN', 'hi', 'es' perfectly fine.
    
    # We slice regional variances like 'en-US' -> 'en' for translation if GoogleTranslator rejects them, 
    # but Google usually handles region codes gracefully.
    try:
        # Some TTS codes are not natively recognized by GoogleTranslate in exact format,
        # so taking the first two letters usually works as a fallback if the exact code fails.
        # But deep-translator and google translate are very robust.
        
        translator = GoogleTranslator(source='auto', target=target_lang_code)
        translated = translator.translate(text)
        
        if translated:
            return translated
        return text
    except Exception as e:
        # Fallback to original code if 'auto' or target fails
        try:
            # Fallback to base language code (e.g. 'zh-CN' -> 'zh')
            base_code = target_lang_code.split('-')[0]
            if base_code != target_lang_code:
                translator = GoogleTranslator(source='auto', target=base_code)
                translated = translator.translate(text)
                if translated:
                    return translated
        except Exception as inner_e:
            logger.error("Translation fallback failed for text='%s', target='%s': %s", text, target_lang_code, inner_e)
            
        logger.error("Translation primary failed for text='%s', target='%s': %s", text, target_lang_code, e)
        return text
