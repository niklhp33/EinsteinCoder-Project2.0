import logging
import os
import uuid
import time
import shutil
from typing import Optional, Tuple
import requests
import functools

from google.cloud import texttospeech
from azure.cognitiveservices.speech import SpeechSynthesizer, SpeechConfig, AudioConfig, ResultReason 

from gtts import gTTS

from config import GLOBAL_CONFIG
from models import SpeechSynthesisVoice

from new_features.advanced_tts_controls import apply_emotional_tone, adjust_speech_rate_and_pitch, insert_pauses, perform_voice_cloning

logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, delay_seconds: int = 2, catch_errors: Tuple[type,...] = (requests.exceptions.RequestException,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except catch_errors as e:
                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {type(e).__name__} - {e}")
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}. Last error: {type(e).__name__} - {e}")
                        raise
                except Exception as e:
                    logger.warning(f"Attempt {attempt}/{max_attempts} caught unexpected error for {func.__name__}: {type(e).__name__} - {e}")
                    if attempt < max_attempts:
                        time.sleep(delay_seconds)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}. Last unexpected error: {type(e).__name__} - {e}", exc_info=True)
                        raise
            return wrapper
        return wrapper
    return decorator


@retry(max_attempts=3, delay_seconds=3)
def synthesize_speech_google(text: str, output_filepath: str, voice_name: str = "en-US-Wavenet-C") -> Optional[str]:
    """
    Synthesizes speech using Google Cloud Text-to-Speech.
    Relies on GOOGLE_CLOUD_PROJECT env variable or gcloud config for project ID.
    """
    try:
        client = texttospeech.TextToSpeechClient() 

        if "(Google)" in voice_name:
            voice_name = voice_name.replace(" (Google)", "")

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="-".join(voice_name.split('-')[:2]),
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open(output_filepath, "wb") as out:
            out.write(response.audio_content)
            logger.info(f"Google TTS audio content written to file: {output_filepath}")
        return output_filepath
    except Exception as e:
        logger.error(f"Google TTS synthesis failed: {e}", exc_info=True)
        raise

@retry(max_attempts=3, delay_seconds=3)
def synthesize_speech_azure(text: str, output_filepath: str, voice_name: str = "en-US-AvaMultilingualNeural") -> Optional[str]:
    """
    Synthesizes speech using Azure Cognitive Services Speech.
    """
    speech_key = GLOBAL_CONFIG['api_keys']['azure_speech_key']
    service_region = GLOBAL_CONFIG['api_keys']['azure_speech_region']

    if not speech_key or speech_key == 'YOUR_AZURE_SPEECH_KEY_PLACEHOLDER' or \
       not service_region or service_region == 'YOUR_AZURE_SPEECH_REGION_PLACEHOLDER':
        logger.error("Azure Speech key or region is not configured. Cannot use Azure TTS.")
        return None

    try:
        if "(Azure)" in voice_name:
            voice_name = voice_name.replace(" (Azure)", "")

        speech_config = SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = AudioConfig(filename=output_filepath)

        speech_config.speech_synthesis_voice_name = voice_name

        speech_synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == ResultReason.SynthesizingAudioCompleted:
            logger.info(f"Azure TTS speech synthesized to: {output_filepath}")
            return output_filepath
        elif result.reason == ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.error(f"Azure TTS speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.error_details:
                logger.error(f"Azure TTS error details: {cancellation_details.error_details}")
            raise requests.exceptions.RequestException(f"Azure TTS Canceled: {cancellation_details.reason}")
    except Exception as e:
        logger.error(f"Azure TTS synthesis failed: {e}", exc_info=True)
        raise

@retry(max_attempts=3, delay_seconds=2)
def synthesize_speech_gtts(text: str, output_filepath: str, lang: str = 'en') -> Optional[str]:
    """
    Synthesizes speech using gTTS (Google Text-to-Speech unofficial API).
    """
    logger.info(f"Using gTTS for speech synthesis (lang={lang})...")
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_filepath)
        logger.info(f"gTTS audio content written to file: {output_filepath}")
        return output_filepath
    except Exception as e:
        logger.error(f"gTTS synthesis failed: {e}", exc_info=True)
        raise

def synthesize_narration(
    text: str,
    audio_output_dir: str,
    voice_type: SpeechSynthesisVoice,
    emotional_tone: Optional[str] = None,
    speech_rate_percent: float = 100.0,
    pitch_semitones: float = 0.0,
    insert_pause_ms: Optional[int] = None,
    voice_clone_audio_path: Optional[str] = None
) -> Optional[str]:
    """
    Synthesizes narration audio based on the chosen voice type,
    incorporating advanced TTS controls conceptually.
    Prioritizes gTTS if selected, otherwise attempts Google/Azure.
    """
    os.makedirs(audio_output_dir, exist_ok=True)
    audio_filename = f"narration_{uuid.uuid4().hex}.mp3"
    audio_filepath = os.path.join(audio_output_dir, audio_filename)

    processed_text = text
    if emotional_tone:
        processed_text = apply_emotional_tone(processed_text, emotional_tone)
    if speech_rate_percent != 100.0 or pitch_semitones != 0.0:
        processed_text = adjust_speech_rate_and_pitch(processed_text, speech_rate_percent, pitch_semitones)
    if insert_pause_ms:
        processed_text = insert_pauses(processed_text, insert_pause_ms)

    if voice_clone_audio_path and os.path.exists(voice_clone_audio_path):
        logger.info(f"Attempting voice cloning using {voice_clone_audio_path} for narration.")
        cloned_audio = perform_voice_cloning(voice_clone_audio_path, processed_text)
        if cloned_audio:
            shutil.copy(cloned_audio, audio_filepath)
            logger.info(f"Narration synthesized via voice cloning to: {audio_filepath}")
            return audio_filepath
        else:
            logger.warning("Voice cloning failed, falling back to standard synthesis.")

    # --- FIX: Prioritize gTTS if selected ---
    if voice_type == SpeechSynthesisVoice.GTTS_DEFAULT:
        return synthesize_speech_gtts(processed_text, audio_filepath)
    elif "Google" in voice_type.value:
        try:
            google_voice_name = voice_type.value.replace(" (Google)", "")
            return synthesize_speech_google(processed_text, audio_filepath, google_voice_name)
        except Exception as e:
            logger.error(f"Google TTS failed, falling back to gTTS: {e}", exc_info=True)
            return synthesize_speech_gtts(processed_text, audio_filepath) # Fallback
    elif "Azure" in voice_type.value:
        try:
            azure_voice_name = voice_type.value.replace(" (Azure)", "")
            return synthesize_speech_azure(processed_text, audio_filepath, azure_voice_name)
        except Exception as e:
            logger.error(f"Azure TTS failed, falling back to gTTS: {e}", exc_info=True)
            return synthesize_speech_gtts(processed_text, audio_filepath) # Fallback
    else:
        logger.error(f"Unsupported speech synthesis voice type: {voice_type}. Falling back to gTTS.")
        return synthesize_speech_gtts(processed_text, audio_filepath)
