import logging
import os
import uuid
import time
from typing import Optional, Tuple

from google.cloud import texttospeech
from azure.cognitiveservices.speech import SpeechSynthesizer, SpeechConfig, AudioConfig, ResultReason
from gtts import gTTS

from config import GLOBAL_CONFIG
from models import SpeechSynthesisVoice

logger = logging.getLogger(__name__)

def synthesize_speech_google(text: str, output_filepath: str, voice_name: str = "en-US-Wavenet-C") -> Optional[str]:
    """
    Synthesizes speech using Google Cloud Text-to-Speech.
    """
    api_key = GLOBAL_CONFIG['api_keys']['google_api_key']
    if not api_key or api_key == 'YOUR_GOOGLE_API_KEY_PLACEHOLDER':
        logger.error("Google API key is not configured. Cannot use Google TTS.")
        return None

    try:
        client = texttospeech.TextToSpeechClient() # No API key needed here, uses GOOGLE_APPLICATION_CREDENTIALS or default ADC
        
        # Check if voice_name contains "Wavenet" or "Standard" and strip "(Google)"
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

        # The response's audio_content is binary.
        with open(output_filepath, "wb") as out:
            out.write(response.audio_content)
            logger.info(f"Google TTS audio content written to file: {output_filepath}")
        return output_filepath
    except Exception as e:
        logger.error(f"Google TTS synthesis failed: {e}", exc_info=True)
        return None


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
        # Check if voice_name contains "Azure" and strip it
        if "(Azure)" in voice_name:
            voice_name = voice_name.replace(" (Azure)", "")

        speech_config = SpeechConfig(subscription=speech_key, region=service_region)
        audio_config = AudioConfig(filename=output_filepath)

        # The language of the voice that speaks.
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
            return None
    except Exception as e:
        logger.error(f"Azure TTS synthesis failed: {e}", exc_info=True)
        return None

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
        return None

def synthesize_narration(text: str, audio_output_dir: str, voice_type: SpeechSynthesisVoice) -> Optional[str]:
    """
    Synthesizes narration audio based on the chosen voice type.
    """
    os.makedirs(audio_output_dir, exist_ok=True)
    audio_filename = f"narration_{uuid.uuid4().hex}.mp3"
    audio_filepath = os.path.join(audio_output_dir, audio_filename)

    if voice_type == SpeechSynthesisVoice.GTTS_DEFAULT:
        # gTTS only supports language code, not voice names
        return synthesize_speech_gtts(text, audio_filepath)
    elif "Google" in voice_type.value:
        # Extract voice name from enum value (e.g., "en-US-Wavenet-C (Google)" -> "en-US-Wavenet-C")
        google_voice_name = voice_type.value.replace(" (Google)", "")
        return synthesize_speech_google(text, audio_filepath, google_voice_name)
    elif "Azure" in voice_type.value:
        # Extract voice name from enum value (e.g., "en-US-AvaMultilingualNeural (Azure)" -> "en-US-AvaMultilingualNeural")
        azure_voice_name = voice_type.value.replace(" (Azure)", "")
        return synthesize_speech_azure(text, audio_filepath, azure_voice_name)
    else:
        logger.error(f"Unsupported speech synthesis voice type: {voice_type}")
        return None
