import logging
import os
import uuid
import time
from typing import Optional, Tuple
import requests # Needed for retry decorator

from google.cloud import texttospeech
from azure.cognitiveservices.speech import SpeechSynthesizer, SpeechConfig, AudioConfig, ResultReason

# gTTS is a separate library, no explicit API key needed but rate limits may apply
from gtts import gTTS

from config import GLOBAL_CONFIG
from models import SpeechSynthesisVoice

# Import advanced TTS features (these are still conceptual/placeholder implementations)
from new_features.advanced_tts_controls import apply_emotional_tone, adjust_speech_rate_and_pitch, insert_pauses, perform_voice_cloning

logger = logging.getLogger(__name__)

# Basic retry decorator for API calls
def retry(max_attempts=3, delay_seconds=2, catch_errors=(requests.exceptions.RequestException,)):
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


@retry(max_attempts=3, delay_seconds=3) # Apply retry decorator
def synthesize_speech_google(text: str, output_filepath: str, voice_name: str = "en-US-Wavenet-C") -> Optional[str]:
    """
    Synthesizes speech using Google Cloud Text-to-Speech.
    """
    # Google Cloud TTS client typically uses GOOGLE_APPLICATION_CREDENTIALS
    # or Application Default Credentials. The api_key is for other Google services.
    # So, api_key check here is more for conceptual completeness.
    # if not GLOBAL_CONFIG['api_keys']['google_api_key'] or GLOBAL_CONFIG['api_keys']['google_api_key'] == 'YOUR_GOOGLE_API_KEY_PLACEHOLDER':
    #     logger.warning("Google API key is not configured. Google TTS might still work if ADC is set up.")

    try:
        client = texttospeech.TextToSpeechClient()
        
        if "(Google)" in voice_name:
            voice_name = voice_name.replace(" (Google)", "")

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="-".join(voice_name.split('-')[:2]), # e.g., "en-US"
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL # Can be customized
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
        raise # Re-raise to trigger retry decorator

@retry(max_attempts=3, delay_seconds=3) # Apply retry decorator
def synthesize_speech_azure(text: str, output_filepath: str, voice_name: str = "en-US-AvaMultilingualNeural") -> Optional[str]:
    """
    Synthesizes speech using Azure Cognitive Services Speech.
    """
    speech_key = GLOBAL_CONFIG['api_keys']['azure_speech_key']
    service_region = GLOBAL_CONFIG['api_keys']['azure_speech_region']

    if not speech_key or speech_key == 'YOUR_AZURE_SPEECH_KEY_PLACEHOLDER' or \
       not service_region or service_region == 'YOUR_AZURE_SPEECH_REGION_PLACEHOLDER':
        logger.error("Azure Speech key or region is not configured. Cannot use Azure TTS.")
        return None # Do not raise, as it's a config issue, not transient API error

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
            raise requests.exceptions.RequestException(f"Azure TTS Canceled: {cancellation_details.reason}") # Treat as retriable
    except Exception as e:
        logger.error(f"Azure TTS synthesis failed: {e}", exc_info=True)
        raise # Re-raise to trigger retry decorator

@retry(max_attempts=3, delay_seconds=2) # Apply retry decorator (gTTS is less API-like, but still good to have)
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
        raise # Re-raise to trigger retry decorator

def synthesize_narration(
    text: str,
    audio_output_dir: str,
    voice_type: SpeechSynthesisVoice,
    # New parameters for advanced controls (conceptual use)
    emotional_tone: Optional[str] = None,
    speech_rate_percent: float = 100.0,
    pitch_semitones: float = 0.0,
    insert_pause_ms: Optional[int] = None,
    voice_clone_audio_path: Optional[str] = None # For voice cloning
) -> Optional[str]:
    """
    Synthesizes narration audio based on the chosen voice type,
    incorporating advanced TTS controls conceptually.
    """
    os.makedirs(audio_output_dir, exist_ok=True)
    audio_filename = f"narration_{uuid.uuid4().hex}.mp3"
    audio_filepath = os.path.join(audio_output_dir, audio_filename)

    # --- Apply advanced TTS controls conceptually (if provided) ---
    processed_text = text
    if emotional_tone:
        processed_text = apply_emotional_tone(processed_text, emotional_tone)
    if speech_rate_percent != 100.0 or pitch_semitones != 0.0:
        processed_text = adjust_speech_rate_and_pitch(processed_text, speech_rate_percent, pitch_semitones)
    if insert_pause_ms:
        processed_text = insert_pauses(processed_text, insert_pause_ms)
    
    # If voice cloning is enabled, this would take precedence or be part of a specific TTS engine.
    if voice_clone_audio_path and os.path.exists(voice_clone_audio_path):
        logger.info(f"Attempting voice cloning using {voice_clone_audio_path} for narration.")
        cloned_audio = perform_voice_cloning(voice_clone_audio_path, processed_text)
        if cloned_audio:
            # Assuming perform_voice_cloning returns the path directly usable
            shutil.copy(cloned_audio, audio_filepath) # Copy the dummy output to final path
            logger.info(f"Narration synthesized via voice cloning to: {audio_filepath}")
            return audio_filepath
        else:
            logger.warning("Voice cloning failed, falling back to standard synthesis.")

    # --- Standard TTS synthesis ---
    if voice_type == SpeechSynthesisVoice.GTTS_DEFAULT:
        # gTTS only supports language code, not voice names
        return synthesize_speech_gtts(processed_text, audio_filepath)
    elif "Google" in voice_type.value:
        google_voice_name = voice_type.value.replace(" (Google)", "")
        return synthesize_speech_google(processed_text, audio_filepath, google_voice_name)
    elif "Azure" in voice_type.value:
        azure_voice_name = voice_type.value.replace(" (Azure)", "")
        return synthesize_speech_azure(processed_text, audio_filepath, azure_voice_name)
    else:
        logger.error(f"Unsupported speech synthesis voice type: {voice_type}")
        return None
