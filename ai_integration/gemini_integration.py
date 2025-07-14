import google.generativeai as genai
import logging
import time
from typing import Optional, List, Dict, Any, Tuple

from config import GLOBAL_CONFIG
from google.colab import userdata # For getting secrets directly

logger = logging.getLogger(__name__)

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

def generate_script_with_gemini(
    video_subject: str,
    keywords: List[str] = [],
    num_paragraphs: int = 5,
    style: str = "engaging and informative",
    max_retries: int = 3,
    retry_delay_s: int = 5
) -> Optional[str]:
    """
    Generates a script for a short-form video using Google Gemini Pro.

    Args:
        video_subject (str): The main topic of the video.
        keywords (List[str]): Additional keywords to include in the script.
        num_paragraphs (int): Desired number of paragraphs for the script.
        style (str): The writing style for the script (e.g., "humorous", "educational").
        max_retries (int): Maximum number of retries for API call.
        retry_delay_s (int): Delay between retries in seconds.

    Returns:
        Optional[str]: The generated script as a string, or None if generation fails.
    """
    if not configure_gemini():
        return None

    model = genai.GenerativeModel(GLOBAL_CONFIG['gemini_settings']['text_generation_model'])
    
    prompt = f"""
    Generate an {style} script for a short-form video (e.g., TikTok, YouTube Shorts) about: "{video_subject}".
    
    Include the following details/keywords if relevant: {', '.join(keywords)}.
    
    The script should be approximately {num_paragraphs} paragraphs long.
    Focus on being concise and impactful, suitable for a fast-paced video.
    """
    
    logger.info(f"Attempting to generate script with Gemini for subject: '{video_subject}'")

    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            script_content = response.text.strip()
            logger.info("Script generated successfully with Gemini.")
            return script_content
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to generate script with Gemini: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay_s)
            else:
                logger.error(f"All {max_retries} attempts failed to generate script with Gemini.", exc_info=True)
                return None

def analyze_video_with_gemini_vision(video_path: str, question: str) -> Optional[str]:
    """
    Analyzes a video file using Gemini 1.5 Pro's multimodal capabilities.

    Args:
        video_path (str): The local path to the video file.
        question (str): The question to ask about the video.

    Returns:
        Optional[str]: The AI's answer, or None if analysis fails.
    """
    if not configure_gemini():
        return None

    if not os.path.exists(video_path):
        logger.error(f"Video file not found for Gemini Vision analysis: {video_path}")
        return None

    model = genai.GenerativeModel(GLOBAL_CONFIG['gemini_settings']['video_analysis_model'])

    # Prepare the video file for upload to Gemini
    # For large files, Gemini API might require a different upload mechanism or local processing.
    # The current genai.upload_file handles it for reasonably sized files.
    
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
        
        # Give some time for file processing on the API side (optional, but good practice)
        # In a real application, you'd poll for status if needed, but generate_content handles it.
        # time.sleep(10) 

        contents = [video_file_obj, question]
        response = model.generate_content(contents)
        result = response.text.strip()
        logger.info("Gemini Vision analysis completed.")
        return result

    except Exception as e:
        logger.error(f"Gemini Vision analysis failed for {video_path}: {e}", exc_info=True)
        return None
    finally:
        # Clean up the uploaded file from Gemini's temporary storage
        if video_file_obj:
            try:
                genai.delete_file(video_file_obj.name)
                logger.info(f"Cleaned up uploaded file {video_file_obj.name} from Gemini.")
            except Exception as e:
                logger.warning(f"Failed to delete uploaded file {video_file_obj.name} from Gemini: {e}")
