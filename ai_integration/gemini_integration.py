import google.generativeai as genai
import logging
import time
from typing import Optional, List, Dict, Any, Tuple
import requests # Needed for retry decorator

from config import GLOBAL_CONFIG
from google.colab import userdata # For getting secrets directly

logger = logging.getLogger(__name__)

# Basic retry decorator for API calls
def retry(max_attempts=3, delay_seconds=2, catch_errors=(requests.exceptions.RequestException, genai.types.BlockedPromptException, genai.types.APIError)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except catch_errors as e:
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}.")
                        raise
        return wrapper
    return decorator

def configure_gemini():
    """Configures the Gemini API client using the API key from GLOBAL_CONFIG."""
    api_key = GLOBAL_CONFIG['api_keys']['google_api_key']
    if not api_key or api_key == 'YOUR_GOOGLE_API_KEY_PLACEHOLDER':
        logger.error("Google API key is not configured in GLOBAL_CONFIG. Cannot configure Gemini.")
        return False
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {e}", exc_info=True)
        return False

@retry(max_attempts=3, delay_seconds=5) # Apply retry decorator
def generate_script_with_gemini(
    video_subject: str,
    keywords: List[str] = [],
    num_paragraphs: int = 5,
    style: str = "engaging and informative",
) -> Optional[str]:
    """
    Generates a script for a short-form video using Google Gemini Pro.
    Includes a refined prompt.

    Args:
        video_subject (str): The main topic of the video.
        keywords (List[str]): Additional keywords to include in the script.
        num_paragraphs (int): Desired number of paragraphs for the script.
        style (str): The writing style for the script (e.g., "humorous", "educational").

    Returns:
        Optional[str]: The generated script as a string, or None if generation fails.
    """
    if not configure_gemini():
        return None

    model = genai.GenerativeModel(GLOBAL_CONFIG['gemini_settings']['text_generation_model'])
    
    keywords_str = f"Include these keywords: {', '.join(keywords)}." if keywords else ""
    prompt = f"""
    You are an expert short-form video content creator.
    Generate a highly **{style}** and **concise** script for a social media video (e.g., TikTok, YouTube Shorts).

    The video is about: **"{video_subject}"**.
    {keywords_str}
    
    The script should be approximately {num_paragraphs} paragraphs long.
    Each paragraph should be short, punchy, and suitable for quick cuts in a video.
    Focus on hooks, clear explanations, and a strong call to action (if applicable).
    Ensure the language is appropriate for a broad audience.
    """
    
    logger.info(f"Attempting to generate script with Gemini for subject: '{video_subject}' and style: '{style}'")

    try:
        response = model.generate_content(prompt)
        script_content = response.text.strip()
        logger.info("Script generated successfully with Gemini.")
        return script_content
    except genai.types.BlockedPromptException as e:
        logger.error(f"Gemini script generation blocked due to safety concerns: {e}")
        raise # Re-raise to trigger retry decorator, or handle specifically
    except genai.types.APIError as e:
        logger.error(f"Gemini API error during script generation: {e}")
        raise # Re-raise to trigger retry decorator
    except Exception as e:
        logger.error(f"An unexpected error occurred during script generation: {e}", exc_info=True)
        return None

@retry(max_attempts=3, delay_seconds=10) # Longer delay for vision API
def analyze_video_with_gemini_vision(video_path: str, question: str) -> Optional[str]:
    """
    Analyzes a video file using Gemini 1.5 Pro's multimodal capabilities.
    Includes retry logic.
    """
    if not configure_gemini():
        return None

    if not os.path.exists(video_path):
        logger.error(f"Video file not found for Gemini Vision analysis: {video_path}")
        return None

    model = genai.GenerativeModel(GLOBAL_CONFIG['gemini_settings']['video_analysis_model'])

    max_file_size_mb = GLOBAL_CONFIG['gemini_settings']['video_analysis_max_file_size_mb']
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    if file_size_mb > max_file_size_mb:
        logger.error(f"Video file size ({file_size_mb:.2f}MB) exceeds Gemini Vision limit ({max_file_size_mb}MB). Skipping analysis.")
        return None

    logger.info(f"Uploading video {video_path} for Gemini Vision analysis...")
    video_file_obj = None
    try:
        video_file_obj = genai.upload_file(video_path)
        logger.info(f"Video {video_path} uploaded successfully to Gemini.")
        
        contents = [video_file_obj, question]
        response = model.generate_content(contents)
        result = response.text.strip()
        logger.info("Gemini Vision analysis completed.")
        return result

    except genai.types.BlockedPromptException as e:
        logger.error(f"Gemini video analysis blocked due to safety concerns: {e}")
        raise
    except genai.types.APIError as e:
        logger.error(f"Gemini API error during video analysis: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during video analysis for {video_path}: {e}", exc_info=True)
        return None
    finally:
        if video_file_obj:
            try:
                genai.delete_file(video_file_obj.name)
                logger.info(f"Cleaned up uploaded file {video_file_obj.name} from Gemini.")
            except Exception as e:
                logger.warning(f"Failed to delete uploaded file {video_file_obj.name} from Gemini: {e}")
