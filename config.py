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
        'openai_api_key': _get_secret('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY_PLACEHOLDER'),
        'stability_ai_api_key': _get_secret('STABILITY_AI_API_KEY', 'YOUR_STABILITY_AI_API_KEY_PLACEHOLDER'),
    },

    'gcp': {
        'service_account_key_path': '/content/drive/MyDrive/EinsteinCoderProject/service_account.json',
        'gcs_bucket_name': 'nikzary-tiktok-juice-videos-2025', # <--- ENSURE THIS IS YOUR ACTUAL BUCKET NAME
    },

    'video_settings': {
        'default_aspect_ratio': 'Portrait 9:16 (TikTok/Reels)',
        'default_max_clip_duration_s': 25,
        'default_num_videos_to_source': 5,
        'default_final_video_duration_s': 60,
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
    for key, path in GLOBAL_CONFIG['paths'].items():
        if key.endswith('_dir'):
            full_path = os.path.join(GLOBAL_CONFIG['paths']['base_dir'], path)
            os.makedirs(full_path, exist_ok=True)
        elif key == 'base_dir':
            os.makedirs(GLOBAL_CONFIG['paths']['base_dir'], exist_ok=True)
