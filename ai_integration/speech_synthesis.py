import logging
import os
import uuid
from typing import Optional, List, Dict, Any, Tuple

from google.cloud import texttospeech
import azure.cognitiveservices.speech as speechsdk

from config import GLOBAL_CONFIG
from utils.shell_utils import run_shell_command
from utils.audio_utils import get_audio_duration_ffprobe

logger = logging.getLogger(__name__)

# --- Google Text-to-Speech Setup ---
def get_google_tts_client():
    google_api_key = GLOBAL_CONFIG['api_keys']['google_api_key']
    if not google_api_key or google_api_key == 'YOUR_GOOGLE_API_KEY_PLACEHOLDER':
        logging.getLogger(__name__).error("Google API key (GOOGLE_API_KEY) is not configured in Colab Secrets. Google TTS calls will fail.")
        return None
    
    service_account_path = GLOBAL_CONFIG['gcp']['service_account_key_path']
    if os.path.exists(service_account_path) and os.path.isfile(service_account_path):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_path
        logging.getLogger(__name__).info(f"Google Text-to-Speech client initialized using service account key: {service_account_path}.")
        return texttospeech.TextToSpeechClient()
    else:
        logging.getLogger(__name__).warning(f"Service account key not found at {service_account_path}. Google Text-to-Speech client may default to environment variable API key.")
        return texttospeech.TextToSpeechClient()


# --- Azure Text-to-Speech Setup ---
def get_azure_tts_client_config():
    speech_key = GLOBAL_CONFIG['api_keys']['azure_speech_key']
    service_region = GLOBAL_CONFIG['api_keys']['azure_speech_region']
    
    if not speech_key or speech_key == 'YOUR_AZURE_SPEECH_KEY_PLACEHOLDER':
        logging.getLogger(__name__).error("Azure Speech Key is not configured. Azure TTS calls will fail.")
        return None
    if not service_region or service_region == 'YOUR_AZURE_SPEECH_REGION_PLACEHOLDER':
        logging.getLogger(__name__).error("Azure Speech Region is not configured. Azure TTS calls will fail.")
        return None
        
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoMp3)
    logging.getLogger(__name__).info(f"Azure Speech client configured for region: {service_region}.")
    return speech_config


def synthesize_speech_google(text: str, voice_name: str, output_filepath: str) -> Optional[str]:
    """
    Synthesizes speech from text using Google Text-to-Speech.
    """
    client = get_google_tts_client()
    if not client:
        return None

    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        if '-' in voice_name:
            lang_code = "-".join(voice_name.split('-')[:2])
        else:
            lang_code = "en-US"

        voice_selection = texttospeech.VoiceSelectionParams(
            language_code=lang_code,
            name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        logging.getLogger(__name__).info(f"Google TTS: Synthesizing speech with voice '{voice_name}'...")
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_selection,
            audio_config=audio_config,
        )

        with open(output_filepath, "wb") as out:
            out.write(response.audio_content)
        logging.getLogger(__name__).info(f"Google TTS: Audio content written to file: {output_filepath}")
        return output_filepath
    except Exception as e:
        logging.getLogger(__name__).error(f"Google Text-to-Speech synthesis failed: {e}", exc_info=True)
        return None


def synthesize_speech_azure(text: str, voice_name: str, output_filepath: str) -> Optional[str]:
    """
    Synthesizes speech from text using Azure Text-to-Speech.
    """
    speech_config = get_azure_tts_client_config()
    if not speech_config:
        return None

    try:
        actual_voice = voice_name.split('(')[0].strip()
        speech_config.speech_synthesis_voice_name = actual_voice

        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filepath)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        logging.getLogger(__name__).info(f"Azure TTS: Synthesizing speech with voice '{actual_voice}'...")
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logging.getLogger(__name__).info(f"Azure TTS: Speech synthesized for text and saved to {output_filepath}")
            return output_filepath
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logging.getLogger(__name__).error(f"Azure TTS: Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logging.getLogger(__name__).error(f"Azure TTS: Cancellation error details: {cancellation_details.error_details}")
                logging.getLogger(__name__).error("Azure TTS: Did you set the speech resource key and region?")
            return None
    except Exception as e:
        logging.getLogger(__name__).error(f"Azure Text-to-Speech synthesis failed: {e}", exc_info=True)
        return None
