import asyncio
import logging
import random
from deep_translator import GoogleTranslator, MyMemoryTranslator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def translate_with_retry(service_func, text, source_lang, target_lang, max_retries=3):
    """Retry translation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            result = await service_func(text, source_lang, target_lang)
            if result and result.strip():
                return result
        except Exception as e:
            logger.warning(f"Translation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 0.5 + random.random() * 2  # 1-3 seconds
                logger.info(f"⌛ Waiting {wait_time:.2f}s before retry...")
                await asyncio.sleep(wait_time)
    return None

async def google_translate(text, source_lang, target_lang):
    """Google Translate using deep_translator"""
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang, timeout=10)
        return translator.translate(text)
    except Exception as e:
        logger.warning(f"Google translation via deep_translator failed: {e}")
        raise

async def mymemory_translate(text, source_lang, target_lang):
    """MyMemory translation service with chunking for 500-character limit"""
    try:
        # Map language codes to MyMemory format
        lang_map = {
            'hi': 'hi-IN',
            'en': 'en-GB',
            # Add more mappings as needed
        }
        source_lang = lang_map.get(source_lang, source_lang)
        target_lang = lang_map.get(target_lang, target_lang)
        
        # Check if text exceeds MyMemory's 500-character limit
        if len(text) <= 450:  # Use 450 to be safe
            return MyMemoryTranslator(source=source_lang, target=target_lang, timeout=10).translate(text)
        else:
            # Split text into chunks for long texts
            return await chunk_translate_mymemory(text, source_lang, target_lang)
            
    except Exception as e:
        logger.warning(f"MyMemory translation failed: {e}")
        raise

async def chunk_translate_mymemory(text, source_lang, target_lang):
    """Split text into chunks for MyMemory 500-character limit"""
    logger.info(f"📝 Text too long ({len(text)} chars), splitting into chunks for MyMemory")
    
    # Split text into sentences first to avoid breaking mid-sentence
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed limit, start new chunk
        if len(current_chunk + sentence + '. ') > 450:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
            else:
                # Single sentence is too long, force split
                chunks.append(sentence[:450])
                current_chunk = sentence[450:] + '. ' if len(sentence) > 450 else ""
        else:
            current_chunk += sentence + '. '
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    logger.info(f"📋 Split into {len(chunks)} chunks")
    
    # Translate each chunk
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        try:
            logger.info(f"🔄 Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            translator = MyMemoryTranslator(source=source_lang, target=target_lang, timeout=10)
            translated_chunk = translator.translate(chunk)
            translated_chunks.append(translated_chunk)
            
            # Small delay between chunks to avoid rate limiting
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)
                
        except Exception as e:
            logger.warning(f"❌ Chunk {i+1} translation failed: {e}")
            # If chunk translation fails, use original chunk
            translated_chunks.append(chunk)
    
    # Join translated chunks
    result = " ".join(translated_chunks)
    logger.info(f"✅ Chunked translation completed ({len(result)} chars)")
    return result

async def robust_translate(text, source_lang, target_lang, max_attempts=3):
    """Robust translation with multiple services and retries"""
    services = [
        ("Googletrans", google_translate),
        ("MyMemory", mymemory_translate)
    ]
    
    for attempt in range(max_attempts):
        logger.info(f"🔄 Translation attempt {attempt + 1}/{max_attempts}: {source_lang} → {target_lang}")
        
        for service_name, service_func in services:
            logger.info(f"Trying {service_name} translation service")
            try:
                result = await translate_with_retry(service_func, text, source_lang, target_lang)
                if result and result.strip():
                    return result
            except Exception as e:
                logger.warning(f"{service_name} translation failed: {e}")
                continue
        
        logger.error(f"❌ Translation error (attempt {attempt + 1}/{max_attempts}): All translation services failed")
        if attempt < max_attempts - 1:
            wait_time = 1 + random.random() * 2
            logger.info(f"⌛ Waiting {wait_time:.2f}s before retry...")
            await asyncio.sleep(wait_time)
    
    logger.warning("⚠️ All translation attempts failed. Returning original text")
    return text

async def translate_to_english(text, source_lang):
    """Translate text to English"""
    if source_lang == 'en':
        return text
    return await robust_translate(text, source_lang, 'en')

async def translate_from_english(text, target_lang):
    """Translate text from English to target language"""
    if target_lang == 'en':
        return text
    return await robust_translate(text, 'en', target_lang)

def has_hindi_characters(text):
    """Check if text contains Hindi characters"""
    hindi_range = range(0x0900, 0x097F)  # Devanagari block
    return any(ord(char) in hindi_range for char in text)
