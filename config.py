import os
import logging

# --- Import google.colab.userdata to explicitly get secrets ---
try:
    from google.colab import userdata
    _IS_COLAB = True
except ImportError:
    _IS_COLAB = False

# Helper function to get secrets securely
def _get_secret(key: str, default_value: str) -> str:
    if _IS_COLAB:
        try:
            secret = userdata.get(key)
            if secret:
                return secret
        except Exception:
            pass # Fallback to os.environ if userdata.get fails
    return os.environ.get(key, default_value)


# --- GLOBAL CONFIGURATION DICTIONARY ---
GLOBAL_CONFIG = {
    'paths': {
        'base_dir': '/tmp/tiktok_project_runtime', # Local Colab runtime temp directory
        'video_downloads_dir': 'video_downloads',
        'audio_dir': 'audio',
        'images_dir': 'images',
        'output_dir': 'output',
        'temp_files_dir': 'temp_files',
        'logs_dir': 'logs'
    },

    'api_keys': {
        'google_api_key': _get_secret('GOOGLE_API_KEY', 'YOUR_GOOGLE_API_KEY_PLACEHOLDER'),
        'pexels_api_key': _get_secret('PEXELS_API_KEY', 'YOUR_PEXELS_API_KEY_PLACEHOLDER'),
        'pixabay_api_key': _get_secret('PIXABAY_API_KEY', 'YOUR_PIXABAY_API_KEY_PLACEHOLDER'),
        'azure_speech_key': _get_secret('AZURE_SPEECH_KEY', 'YOUR_AZURE_SPEECH_KEY_PLACEHOLDER'),
        'azure_speech_region': _get_secret('AZURE_SPEECH_REGION', 'YOUR_AZURE_SPEECH_REGION_PLACEHOLDER'),
        'stability_ai_api_key': _get_secret('STABILITY_AI_API_KEY', 'YOUR_STABILITY_AI_API_KEY_PLACEHOLDER'),
        'openai_api_key': _get_secret('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_PLACEHOLDER'),
    },

    'gcp': {
        'project_id': _get_secret('GCP_PROJECT_ID', 'your-gcp-project-id'),
        'service_account_key_path': os.path.join(os.path.expanduser('~'), '.config', 'gcloud', 'application_default_credentials.json'), # Default path for Colab
        'gcs_bucket_name': _get_secret('GCS_BUCKET_NAME', 'your-gcs-bucket-name'),
    },

    'video_settings': {
        'default_video_source_type': 'Stock Footage (Pexels/Pixabay)',
        'default_concat_mode': 'Random Concatenation (Recommended)',
        'default_transition_mode': 'Fade',
        'default_transition_duration': 0.5,
        'default_video_language': 'English',
    },

    'audio_settings': {
        'default_narration_voice': 'en-US-Wavenet-C',
        'default_background_music_query': 'upbeat cinematic',
        'default_background_music_volume': -15
    },

    'subtitle_settings': {
        'default_enable_subtitles': True,
        'default_font': 'Roboto',
        'default_position': 'Bottom Center',
        'default_font_size': 50,
        'default_color': 'white',
        'default_outline_color': 'black',
        'default_outline_width': 2
    },

    'gemini_settings': {
        'video_analysis_model': 'gemini-1.5-pro-latest',
        'text_generation_model': 'gemini-1.5-pro-latest',
        'video_analysis_max_file_size_mb': 200
    },
    'api_timeouts': {
        'speech_to_text_timeout_s': 300 # Timeout for long-running STT operations
    }
}

def setup_runtime_directories():
    """Ensures local runtime directories as defined in GLOBAL_CONFIG exist."""
    base_dir = GLOBAL_CONFIG['paths']['base_dir']
    for key, path in GLOBAL_CONFIG['paths'].items():
        if key.endswith('_dir'): # Only process directory paths
            full_path = os.path.join(base_dir if key != 'base_dir' else '', path)
            os.makedirs(full_path, exist_ok=True)
            logging.getLogger(__name__).info(f"Ensured runtime directory: {full_path}")
