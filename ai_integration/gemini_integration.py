import logging
import json
import re
from typing import List, Optional, Tuple, Dict, Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import GLOBAL_CONFIG

logger = logging.getLogger(__name__)

# --- Gemini API Configuration ---
def _configure_gemini_api():
    api_key = GLOBAL_CONFIG['api_keys']['google_api_key']
    if not api_key or api_key == 'YOUR_GOOGLE_API_KEY_PLACEHOLDER':
        logger.error("Google API key (GOOGLE_API_KEY) is not configured in Colab Secrets. Gemini API calls will fail.")
        return False
    genai.configure(api_key=api_key)
    logger.info("Google Gemini API configured.")
    return True

_safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def get_gemini_model(model_name: str):
    if not _configure_gemini_api():
        return None
    return genai.GenerativeModel(model_name=model_name, safety_settings=_safety_settings)

def generate_text_content(prompt: str, model_name: str = 'gemini-1.5-pro-latest') -> Optional[str]:
    """
    Generates text content using the specified Gemini model.
    """
    model = get_gemini_model(model_name)
    if not model:
        return None
    
    logger.info(f"Generating text content with model {model_name} for prompt: {prompt[:100]}...")
    try:
        response = model.generate_content(prompt)
        if response and response.text:
            logger.info("Text content generated successfully.")
            return response.text
        elif response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    generated_text = "".join([part.text for part in candidate.content.parts])
                    logger.info("Text content generated successfully (from candidate parts).")
                    return generated_text
            logger.warning("Gemini API generated no text content from candidates.")
            return None
        else:
            logger.warning("Gemini API generated no text content.")
            return None
    except Exception as e:
        logger.error(f"Failed to generate text content from Gemini API: {e}", exc_info=True)
        return None

def generate_video_script(video_subject: str, video_language: str, final_video_duration_s: int) -> Optional[List[str]]:
    """
    Generates a video script based on the subject and language.
    """
    prompt = (
        f"Generate a short (approx. {final_video_duration_s} seconds) engaging video script about '{video_subject}' in {video_language}. "
        "Include a captivating hook, a few main points, and a strong call to action. "
        "Each sentence should be a separate element in a JSON list. "
        "Ensure the entire output is a valid JSON list of strings, with each string being a complete sentence. "
        "Example: [\"Sentence one.\", \"Sentence two.\", \"Sentence three.\"]"
    )
    
    script_raw = generate_text_content(prompt, GLOBAL_CONFIG['gemini_settings']['text_generation_model'])
    
    if not script_raw:
        logger.error("Failed to generate raw script text from Gemini.")
        return None

    try:
        script_list = json.loads(script_raw)
        if not isinstance(script_list, list) or not all(isinstance(s, str) for s in script_list):
            raise ValueError("Parsed JSON is not a list of strings.")
        logger.info("Script parsed successfully as strict JSON list.")
        return script_list
    except json.JSONDecodeError as e:
        logger.warning(f"Could not parse script as strict JSON list ({e}). Attempting robust fallback: extracting sentences. Raw script: {script_raw}")
        sentences = re.split(r'(?<=[.!?])\s*(?=\S)', script_raw)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences and sentences[0].startswith("```json"):
            sentences[0] = sentences[0][len("```json"):].strip()
        if sentences and sentences[-1].endswith("```"):
            sentences[-1] = sentences[-1][:-len("```")].strip()
            
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            logger.error("Robust fallback failed to extract any sentences from the script.")
            return None
        
        logger.info(f"Script generated with {len(sentences)} segments (robust fallback parse).")
        return sentences
    except Exception as e:
        logger.error(f"An unexpected error occurred during script parsing: {e}", exc_info=True)
        return None

def analyze_video_content(video_path: str, prompt: str, model_name: str = 'gemini-1.5-pro-latest') -> Optional[str]:
    """
    Analyzes video content using a multi-modal Gemini model.
    """
    model = get_gemini_model(model_name)
    if not model:
        logger.error("Gemini model not initialized for video analysis.")
        return None

    if not os.path.exists(video_path):
        logger.error(f"Video file not found for analysis: {video_path}")
        return None
    
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    max_file_size_mb = GLOBAL_CONFIG['gemini_settings']['video_analysis_max_file_size_mb']
    if file_size_mb > max_file_size_mb:
        logger.error(f"Video file size ({file_size_mb:.2f}MB) exceeds Gemini's current limit ({max_file_size_mb}MB). Cannot analyze.")
        logger.error("Consider reducing video duration or resolution for analysis, or using a local ASR model for transcription.")
        return None

    mime_type = "video/mp4"
    
    logger.info(f"Analyzing video content for {video_path} with prompt: {prompt[:100]}...")
    try:
        video_file_data = genai.upload_file(video_path, mime_type=mime_type)
        logger.info(f"Uploaded video to Gemini: {video_file_data.uri}")
        
        contents = [
            prompt,
            video_file_data
        ]

        response = model.generate_content(contents)
        
        genai.delete_file(video_file_data.name)
        logger.info(f"Deleted temporary video file from Gemini storage: {video_file_data.uri}")

        if response and response.text:
            analysis_result = response.text
            logger.info("Video analysis successful.")
            return analysis_result
        elif response.candidates:
            for candidate in response.candidates:
                if candidate.content and candidate.content.parts:
                    analysis_result = "".join([part.text for part in candidate.content.parts])
                    logger.info("Video analysis successful (from candidate parts).")
                    return analysis_result
            logger.warning("Gemini video analysis returned no content from candidates.")
            return None
        else:
            logger.warning("Gemini video analysis returned no content.")
            return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during video analysis: {e}", exc_info=True)
        return None
