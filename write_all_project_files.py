import os
import logging
import textwrap

logger = logging.getLogger(__name__)

# This function will be called from the main Colab notebook to update all files
def write_all_files(project_root_dir: str):
    logger.info(f"Starting batch update of all .py files in {project_root_dir}...")

    # Define content for each file as multi-line strings
    # IMPORTANT: Keep this file updated with the LATEST content of ALL your .py files.

    # config.py content
    config_py_content = textwrap.dedent("""\
    import os
    import logging

    try:
        from google.colab import userdata
        _IS_COLAB = True
    except ImportError:
        _IS_COLAB = False

    def _get_secret(key: str, default_value: str) -> str:
        if _IS_COLAB:
            try:
                secret = userdata.get(key)
                if secret:
                    return secret
            except Exception:
                pass
        return os.environ.get(key, default_value)

    GLOBAL_CONFIG = {
        'paths': {
            'base_dir': '/tmp/tiktok_project_runtime',
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
            'service_account_key_path': os.path.join(os.path.expanduser('~'), '.config', 'gcloud', 'application_default_credentials.json'),
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
            'speech_to_text_timeout_s': 300
        }
    }

    def setup_runtime_directories():
        _logger = logging.getLogger(__name__) # Use local logger
        base_dir = GLOBAL_CONFIG['paths']['base_dir']
        for key, path in GLOBAL_CONFIG['paths'].items():
            if key.endswith('_dir'):
                full_path = os.path.join(base_dir if key != 'base_dir' else '', path)
                os.makedirs(full_path, exist_ok=True)
                _logger.info(f"Ensured runtime directory: {full_path}")
    """)

    # models.py content
    models_py_content = textwrap.dedent("""\
    from enum import Enum
    from dataclasses import dataclass
    from typing import Optional, List, Dict, Any

    class VideoLanguage(str, Enum):
        ENGLISH = "English"
        SPANISH = "Spanish"
        FRENCH = "French"
        GERMAN = "German"
        PORTUGUESE = "Portuguese"
        CHINESE = "Chinese"
        JAPANESE = "Japanese"
        KOREAN = "Korean"

    class VideoSourceType(str, Enum):
        STOCK_FOOTAGE_PEXELS_PIXABAY = "Stock Footage (Pexels/Pixabay)"
        STOCK_FOOTAGE_PEXELS_ONLY = "Stock Footage (Pexels Only)"
        STOCK_FOOTAGE_PIXABAY_ONLY = "Stock Footage (Pixabay Only)"
        AI_GENERATED_IMAGES = "AI-Generated Images (DALL-E 3, Stable Diffusion)"
        AI_GENERATED_VIDEOS = "AI-Generated Videos (Google Text-to-Video)"

    class VideoConcatMode(str, Enum):
        RANDOM_CONCATENATION = "Random Concatenation (Recommended)"
        SEQUENTIAL_CONCATENATION = "Sequential Concatenation"

    class VideoTransitionMode(str, Enum):
        FADE = "Fade"
        CROSSFADE = "Crossfade"
        SLIDE = "Slide"
        NONE = "None"

    class VideoAspect(str, Enum):
        PORTRAIT_9_16 = "Portrait 9:16 (TikTok/Reels)"
        LANDSCAPE_16_9 = "Landscape 16:9 (YouTube)"
        SQUARE_1_1 = "Square 1:1 (Instagram)"

    class SpeechSynthesisVoice(str, Enum):
        EN_US_WAVENET_A = "en-US-Wavenet-A (Google)"
        EN_US_WAVENET_B = "en-US-Wavenet-B (Google)"
        EN_US_WAVENET_C = "en-US-Wavenet-C (Google)"
        EN_US_WAVENET_D = "en-US-WAVENET-D (Google)"
        EN_US_WAVENET_E = "en-US-WAVENET-E (Google)"
        EN_US_WAVENET_F = "en-US-WAVENET-F (Google)"
        EN_US_WAVENET_G = "en-US-WAVENET-G (Google)"
        EN_US_WAVENET_H = "en-US-WAVENET-H (Google)"
        EN_US_WAVENET_I = "en-US-WAVENET-I (Google)"
        EN_US_WAVENET_J = "en-US-WAVENET-J (Google)"
        EN_US_AVA_MULTILINGUAL = "en-US-AvaMultilingualNeural (Azure)"
        EN_US_GUY_MULTILINGUAL = "en-US-GuyMultilingualNeural (Azure)"
        EN_US_NANCY_MULTILINGUAL = "en-US-NancyMultilingualNeural (Azure)"
        GTTS_DEFAULT = "gTTS (Basic)"

    class SubtitleFont(str, Enum):
        ROBOTO = "Roboto"
        ARIAL = "Arial"
        VERDANA = "Verdana"
        TIMES_NEW_ROMAN = "Times New Roman"
        IMPACT = "Impact"
        COMIC_SANS_MS = "Comic Sans MS"
        MONTSERRAT = "Montserrat"
        OPEN_SANS = "Open Sans"
        LATO = "Lato"
        OSWALD = "Oswald"
        POPPINS = "Poppins"
        SOURCE_SANS_PRO = "Source Sans Pro"
        ANTON = "Anton"
        BASHKIR = "Bashkir"

    class SubtitlePosition(str, Enum):
        BOTTOM_LEFT = "Bottom Left"
        BOTTOM_CENTER = "Bottom Center"
        BOTTOM_RIGHT = "Bottom Right"
        MIDDLE_LEFT = "Middle Left"
        MIDDLE_CENTER = "Middle Center"
        MIDDLE_RIGHT = "Middle Right"
        TOP_LEFT = "Top Left"
        TOP_CENTER = "Top Center"
        TOP_RIGHT = "Top Right"

        def to_ffmpeg_ass_position(self) -> int:
            if self == SubtitlePosition.BOTTOM_LEFT: return 1
            if self == SubtitlePosition.BOTTOM_CENTER: return 2
            if self == SubtitlePosition.BOTTOM_RIGHT: return 3
            if self == SubtitlePosition.MIDDLE_LEFT: return 4
            if self == SubtitlePosition.MIDDLE_CENTER: return 5
            if self == SubtitlePosition.MIDDLE_RIGHT: return 6
            if self == SubtitlePosition.TOP_LEFT: return 7
            if self == SubtitlePosition.TOP_CENTER: return 8
            if self == SubtitlePosition.TOP_RIGHT: return 9
            return 2

    @dataclass
    class SubtitleEntry:
        text: str
        start_time_s: float
        end_time_s: float

    @dataclass
    class ImagePrompt:
        text_prompt: str
        image_style: Optional[str] = None
        aspect_ratio: Optional[str] = None

    @dataclass
    class VideoParams:
        video_subject: str
        video_language: VideoLanguage = VideoLanguage.ENGLISH
        video_source_type: VideoSourceType = VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY
        image_prompt_suffix: Optional[str] = None
        video_concat_mode: VideoConcatMode = VideoConcatMode.RANDOM_CONCATENATION
        video_transition_mode: VideoTransitionMode = VideoTransitionMode.FADE
        video_aspect_ratio: VideoAspect = VideoAspect.PORTRAIT_9_16
        max_clip_duration_s: int = 25
        num_videos_to_source_or_generate: int = 5
        final_video_duration_s: int = 60

        speech_synthesis_voice: SpeechSynthesisVoice = SpeechSynthesisVoice.EN_US_WAVENET_C
        enable_subtitles: bool = True
        subtitle_font: SubtitleFont = SubtitleFont.ROBOTO
        subtitle_position: SubtitlePosition = SubtitlePosition.BOTTOM_CENTER
        subtitle_font_size: int = 50
        subtitle_color: str = "white"
        subtitle_outline_color: str = "black"
        subtitle_outline_width: int = 2

        def dict(self):
            return {k: v.value if isinstance(v, Enum) else v for k, v in self.__dict__.items()}
    """)

    # pipeline.py content
    pipeline_py_content = textwrap.dedent("""\
    import logging
    import os
    import time
    import shutil
    from typing import Optional, List, Tuple

    from config import GLOBAL_CONFIG
    from models import VideoParams, SubtitleEntry, SubtitleFont, SubtitlePosition, VideoAspect
    from utils.cleanup import cleanup_runtime_files, setup_runtime_directories
    from utils.gcs_utils import upload_to_gcs # Conceptual GCS upload, main output goes to Drive mount
    from utils.video_utils import get_video_duration
    from utils.audio_utils import combine_audio_tracks, download_background_music, get_audio_duration_ffprobe
    from ai_integration.gemini_integration import generate_script_with_gemini
    from ai_integration.speech_synthesis import synthesize_narration
    from media_processing.video_editor import download_source_clips, combine_and_edit_clips, generate_subtitles_file

    logger = logging.getLogger(__name__)

    RUNTIME_BASE_DIR = GLOBAL_CONFIG['paths']['base_dir']
    VIDEO_DOWNLOADS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['video_downloads_dir'])
    AUDIO_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['audio_dir'])
    IMAGES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['images_dir'])
    OUTPUT_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['output_dir'])
    TEMP_FILES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['temp_files_dir'])
    LOGS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['logs_dir'])

    def generate_video_pipeline(params: VideoParams) -> Tuple[Optional[str], Optional[str]]:
        logger.info("Starting video generation pipeline...")
        start_time = time.time()

        setup_runtime_directories()
        log_file_path = os.path.join(LOGS_DIR, f"pipeline_log_{int(start_time)}.txt")
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
        logger.info(f"Pipeline log file: {log_file_path}")

        final_video_output_path = None
        try:
            logger.info("Generating script...")
            script_text = generate_script_with_gemini(
                video_subject=params.video_subject,
                num_paragraphs=3,
                style="engaging, concise, and informative"
            )
            if not script_text:
                logger.error("Script generation failed. Aborting pipeline.")
                return None, log_file_path
            logger.info(f"Generated Script:\\n---\\n{script_text}\\n---")

            logger.info("Synthesizing narration...")
            narration_audio_path = synthesize_narration(
                text=script_text,
                audio_output_dir=AUDIO_DIR,
                voice_type=params.speech_synthesis_voice
            )
            if not narration_audio_path:
                logger.error("Narration synthesis failed. Aborting pipeline.")
                return None, log_file_path
            narration_duration = get_audio_duration_ffprobe(narration_audio_path)
            logger.info(f"Narration synthesized. Duration: {narration_duration:.2f}s")
            if narration_duration is None:
                logger.warning("Could not determine narration duration. Setting target video duration to 60s.")
                target_video_duration = 60
            else:
                target_video_duration = narration_duration
            params.final_video_duration_s = int(target_video_duration)

            logger.info(f"Sourcing/generating video clips ({params.video_source_type})...")
            downloaded_clips = download_source_clips(
                video_params=params,
                video_downloads_dir=VIDEO_DOWNLOADS_DIR,
                max_clip_duration_s=params.max_clip_duration_s
            )
            if not downloaded_clips:
                logger.error("No video clips sourced or generated. Aborting pipeline.")
                return None, log_file_path
            logger.info(f"Sourced/generated {len(downloaded_clips)} clips.")

            logger.info("Combining and editing video clips...")
            base_video_name = f"final_video_{int(time.time())}"
            base_video_path = os.path.join(TEMP_FILES_DIR, f"{base_video_name}_base.mp4")

            combined_video_path = combine_and_edit_clips(
                video_paths=downloaded_clips,
                final_video_duration_s=params.final_video_duration_s,
                video_concat_mode=params.video_concat_mode,
                video_transition_mode=params.video_transition_mode,
                video_aspect_ratio=params.video_aspect_ratio,
                temp_files_dir=TEMP_FILES_DIR,
                output_base_name=base_video_name
            )
            if not combined_video_path:
                logger.error("Video combination/editing failed. Aborting pipeline.")
                return None, log_file_path
            logger.info(f"Base video created: {combined_video_path}")

            logger.info("Downloading and integrating background music...")
            background_music_path = download_background_music(
                query=GLOBAL_CONFIG['audio_settings']['default_background_music_query'],
                output_dir=AUDIO_DIR
            )
            if not background_music_path:
                logger.warning("Background music download failed. Proceeding without background music.")
                final_audio_path = narration_audio_path
            else:
                final_audio_path = os.path.join(AUDIO_DIR, f"{base_video_name}_final_audio.mp3")
                combined_audio_result = combine_audio_tracks(
                    track1_path=narration_audio_path,
                    track2_path=background_music_path,
                    output_path=final_audio_path,
                    track1_volume_db=0.0,
                    track2_volume_db=GLOBAL_CONFIG['audio_settings']['default_background_music_volume']
                )
                if not combined_audio_result:
                    logger.error("Failed to combine narration and background music. Aborting pipeline.")
                    return None, log_file_path
                final_audio_path = combined_audio_result
            logger.info(f"Final audio track prepared: {final_audio_path}")

            video_with_audio_path = os.path.join(TEMP_FILES_DIR, f"{base_video_name}_with_audio.mp4")
            audio_added_result = add_audio_to_video(
                video_path=combined_video_path,
                audio_path=final_audio_path,
                output_path=video_with_audio_path
            )
            if not audio_added_result:
                logger.error("Failed to add audio to video. Aborting pipeline.")
                return None, log_file_path
            final_video_output_path = video_with_audio_path
            logger.info(f"Video with audio created: {final_video_output_path}")

            if params.enable_subtitles:
                logger.info("Generating and burning subtitles...")
                dummy_subtitle_entries: List[SubtitleEntry] = []
                words = script_text.split()
                word_duration = narration_duration / len(words) if narration_duration else 0.5
                current_time = 0.0
                segment_length = 5
                for i in range(0, len(words), segment_length):
                    segment_words = words[i:i+segment_length]
                    segment_text = " ".join(segment_words)
                    start_s = current_time
                    end_s = current_time + (len(segment_words) * word_duration)
                    dummy_subtitle_entries.append(SubtitleEntry(text=segment_text, start_time_s=start_s, end_time_s=end_s))
                    current_time = end_s

                subtitle_file_path = os.path.join(TEMP_FILES_DIR, f"{base_video_name}_subtitles.ass")
                font_path_map = {
                    SubtitleFont.ROBOTO: os.path.join(os.path.expanduser('~'), '.fonts', 'Roboto-Regular.ttf'),
                }
                default_font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                chosen_font_path = font_path_map.get(params.subtitle_font, default_font_path)

                ass_file_created = generate_subtitles_file(
                    subtitle_entries=dummy_subtitle_entries,
                    output_filepath=subtitle_file_path,
                    font=params.subtitle_font,
                    font_size=params.subtitle_font_size,
                    color=params.subtitle_color,
                    outline_color=params.subtitle_outline_color,
                    outline_width=params.subtitle_outline_width,
                    position=params.subtitle_position
                )

                if ass_file_created:
                    video_with_subtitles_path = os.path.join(OUTPUT_DIR, f"{base_video_name}_final.mp4")
                    subtitles_burnt = add_subtitles_to_video(
                        video_path=final_video_output_path,
                        subtitle_file_path=ass_file_created,
                        output_path=video_with_subtitles_path,
                        font_path=chosen_font_path,
                        font_size=params.subtitle_font_size,
                        font_color=params.subtitle_color,
                        outline_color=params.subtitle_outline_color,
                        outline_width=params.subtitle_outline_width,
                        position=params.subtitle_position.to_ffmpeg_ass_position()
                    )
                    if subtitles_burnt:
                        final_video_output_path = video_with_subtitles_path
                    else:
                        logger.error("Failed to burn subtitles. Final video will be without subtitles.")
                else:
                    logger.warning("Failed to generate subtitle ASS file. Skipping subtitle burning.")
            else:
                logger.info("Subtitles disabled as per parameters.")

            logger.info(f"Final video generated: {final_video_output_path}")

            drive_output_path = os.path.join(PROJECT_ROOT_DIR, 'output_videos', os.path.basename(final_video_output_path))
            os.makedirs(os.path.dirname(drive_output_path), exist_ok=True)
            
            try:
                shutil.copy(final_video_output_path, drive_output_path)
                logger.info(f"Final video copied to Google Drive: {drive_output_path}")
                drive_log_path = os.path.join(PROJECT_ROOT_DIR, 'logs', os.path.basename(log_file_path))
                os.makedirs(os.path.dirname(drive_log_path), exist_ok=True)
                shutil.copy(log_file_path, drive_log_path)
                logger.info(f"Log file copied to Google Drive: {drive_log_path}")
            except Exception as e:
                logger.error(f"Failed to copy final video or log to Google Drive: {e}", exc_info=True)

            end_time = time.time()
            logger.info(f"Pipeline completed in {end_time - start_time:.2f} seconds.")

            return final_video_output_path, log_file_path

        except Exception as e:
            logger.critical(f"An unhandled error occurred in the pipeline: {e}", exc_info=True)
            return None, log_file_path
        finally:
            logger.info("Cleaning up runtime files...")
            cleanup_runtime_files()
            if file_handler in logging.getLogger().handlers: # Check if handler still exists
                logging.getLogger().removeHandler(file_handler)
    """)

    # ui_pipeline.py content
    ui_pipeline_py_content = textwrap.dedent("""\
    import gradio as gr
    import logging
    import os
    import shutil
    import time

    from config import GLOBAL_CONFIG
    from models import VideoParams, VideoLanguage, VideoSourceType, VideoConcatMode, VideoTransitionMode, VideoAspect, SpeechSynthesisVoice, SubtitleFont, SubtitlePosition
    from pipeline import generate_video_pipeline

    logger = logging.getLogger(__name__)

    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def run_pipeline_ui(
        video_subject: str,
        video_language: str,
        video_source_type: str,
        image_prompt_suffix: str,
        video_concat_mode: str,
        video_transition_mode: str,
        video_aspect_ratio: str,
        max_clip_duration_s: int,
        num_videos_to_source_or_generate: int,
        final_video_duration_s: int,
        speech_synthesis_voice: str,
        enable_subtitles: bool,
        subtitle_font: str,
        subtitle_position: str,
        subtitle_font_size: int,
        subtitle_color: str,
        subtitle_outline_color: str,
        subtitle_outline_width: int
    ):
        logger.info("Gradio UI: Video generation started.")
        
        try:
            params = VideoParams(
                video_subject=video_subject,
                video_language=VideoLanguage(video_language),
                video_source_type=VideoSourceType(video_source_type),
                image_prompt_suffix=image_prompt_suffix if image_prompt_suffix else None,
                video_concat_mode=VideoConcatMode(video_concat_mode),
                video_transition_mode=VideoTransitionMode(video_transition_mode),
                video_aspect_ratio=VideoAspect(video_aspect_ratio),
                max_clip_duration_s=max_clip_duration_s,
                num_videos_to_source_or_generate=num_videos_to_source_or_generate,
                final_video_duration_s=final_video_duration_s,
                speech_synthesis_voice=SpeechSynthesisVoice(speech_synthesis_voice),
                enable_subtitles=enable_subtitles,
                subtitle_font=SubtitleFont(subtitle_font),
                subtitle_position=SubtitlePosition(subtitle_position),
                subtitle_font_size=subtitle_font_size,
                subtitle_color=subtitle_color,
                subtitle_outline_color=subtitle_outline_color,
                subtitle_outline_width=subtitle_outline_width
            )
        except ValueError as e:
            logger.error(f"Gradio UI: Invalid input parameter: {e}")
            return None, None, f"Error: Invalid input parameter: {e}. Please check your selections."

        status_message = "Video generation in progress... Check logs for details."
        
        final_video_path, log_path = generate_video_pipeline(params)

        if final_video_path and os.path.exists(final_video_path):
            final_status = f"Video generation completed successfully! Output: {final_video_path}"
            logger.info(final_status)
            return final_video_path, log_path, final_status
        else:
            final_status = f"Video generation failed. Check log file for errors: {log_path}"
            logger.error(final_status)
            return None, log_path, final_status

    def launch_gradio_ui():
        logger.info("Launching Gradio UI...")

        default_video_params = VideoParams(
            video_subject="default subject",
            video_source_type=VideoSourceType(GLOBAL_CONFIG['video_settings']['default_video_source_type']),
            video_concat_mode=VideoConcatMode(GLOBAL_CONFIG['video_settings']['default_concat_mode']),
            video_transition_mode=VideoTransitionMode(GLOBAL_CONFIG['video_settings']['default_transition_mode']),
            video_language=VideoLanguage(GLOBAL_CONFIG['video_settings']['default_video_language']),
            speech_synthesis_voice=SpeechSynthesisVoice(GLOBAL_CONFIG['audio_settings']['default_narration_voice']),
            enable_subtitles=GLOBAL_CONFIG['subtitle_settings']['default_enable_subtitles'],
            subtitle_font=SubtitleFont(GLOBAL_CONFIG['subtitle_settings']['default_font']),
            subtitle_position=SubtitlePosition(GLOBAL_CONFIG['subtitle_settings']['default_position']),
            subtitle_font_size=GLOBAL_CONFIG['subtitle_settings']['default_font_size'],
            subtitle_color=GLOBAL_CONFIG['subtitle_settings']['default_color'],
            subtitle_outline_color=GLOBAL_CONFIG['subtitle_settings']['default_outline_color'],
            subtitle_outline_width=GLOBAL_CONFIG['subtitle_settings']['default_outline_width']
        )

        with gr.Blocks(theme=gr.themes.Soft()) as demo:
            gr.Markdown("# 🎬 Einstein Coder - Automated Short-Form Video Generation")
            gr.Markdown("Enter your video subject and customize settings to generate a short video.")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📝 Script & Voice Settings")
                    video_subject = gr.Textbox(label="Video Subject/Topic", placeholder="e.g., 'Benefits of AI in daily life'", interactive=True)
                    video_language = gr.Dropdown(
                        label="Video Language",
                        choices=[e.value for e in VideoLanguage],
                        value=default_video_params.video_language.value,
                        interactive=True
                    )
                    speech_synthesis_voice = gr.Dropdown(
                        label="Narration Voice",
                        choices=[e.value for e in SpeechSynthesisVoice],
                        value=default_video_params.speech_synthesis_voice.value,
                        interactive=True
                    )
                with gr.Column():
                    gr.Markdown("### 🎥 Video Source & Editing")
                    video_source_type = gr.Dropdown(
                        label="Video Source Type",
                        choices=[e.value for e in VideoSourceType],
                        value=default_video_params.video_source_type.value,
                        interactive=True
                    )
                    image_prompt_suffix = gr.Textbox(
                        label="AI Image Prompt Suffix (if AI Images selected)",
                        placeholder="e.g., 'futuristic, hyperrealistic'",
                        lines=1,
                        interactive=True
                    )
                    video_aspect_ratio = gr.Radio(
                        label="Video Aspect Ratio",
                        choices=[e.value for e in VideoAspect],
                        value=default_video_params.video_aspect_ratio.value,
                        interactive=True
                    )
                    video_concat_mode = gr.Dropdown(
                        label="Video Concatenation Mode",
                        choices=[e.value for e in VideoConcatMode],
                        value=default_video_params.video_concat_mode.value,
                        interactive=True
                    )
                    video_transition_mode = gr.Dropdown(
                        label="Video Transition Mode",
                        choices=[e.value for e in VideoTransitionMode],
                        value=default_video_params.video_transition_mode.value,
                        interactive=True
                    )
                    max_clip_duration_s = gr.Slider(minimum=5, maximum=30, value=default_video_params.max_clip_duration_s, step=1, label="Max Individual Clip Duration (s)")
                    num_videos_to_source_or_generate = gr.Slider(minimum=3, maximum=15, value=default_video_params.num_videos_to_source_or_generate, step=1, label="Number of Clips to Source/Generate")
                    final_video_duration_s = gr.Slider(minimum=15, maximum=120, value=default_video_params.final_video_duration_s, step=5, label="Target Final Video Duration (s)")

                with gr.Column():
                    gr.Markdown("### 📝 Subtitle Settings")
                    enable_subtitles = gr.Checkbox(label="Enable Subtitles", value=default_video_params.enable_subtitles, interactive=True)
                    subtitle_font = gr.Dropdown(
                        label="Font",
                        choices=[e.value for e in SubtitleFont],
                        value=default_video_params.subtitle_font.value,
                        interactive=True
                    )
                    subtitle_position = gr.Dropdown(
                        label="Position",
                        choices=[e.value for e in SubtitlePosition],
                        value=default_video_params.subtitle_position.value,
                        interactive=True
                    )
                    subtitle_font_size = gr.Slider(minimum=20, maximum=100, value=default_video_params.subtitle_font_size, step=1, label="Font Size")
                    subtitle_color = gr.ColorPicker(label="Font Color", value=default_video_params.subtitle_color, interactive=True)
                    subtitle_outline_color = gr.ColorPicker(label="Outline Color", value=default_video_params.subtitle_outline_color, interactive=True)
                    subtitle_outline_width = gr.Slider(minimum=0, maximum=10, value=default_video_params.subtitle_outline_width, step=1, label="Outline Width")
            
            generate_btn = gr.Button("🚀 Generate Video", variant="primary")

            with gr.Row():
                video_output = gr.Video(label="Generated Video", interactive=False)
            with gr.Row():
                log_output = gr.File(label="Log File", interactive=False)
            with gr.Row():
                status_text = gr.Textbox(label="Status", interactive=False, lines=2)

            generate_btn.click(
                fn=run_pipeline_ui,
                inputs=[
                    video_subject,
                    video_language,
                    video_source_type,
                    image_prompt_suffix,
                    video_concat_mode,
                    video_transition_mode,
                    video_aspect_ratio,
                    max_clip_duration_s,
                    num_videos_to_source_or_generate,
                    final_video_duration_s,
                    speech_synthesis_voice,
                    enable_subtitles,
                    subtitle_font,
                    subtitle_position,
                    subtitle_font_size,
                    subtitle_color,
                    subtitle_outline_color,
                    subtitle_outline_width
                ],
                outputs=[video_output, log_output, status_text]
            )
        
        demo.launch(debug=True, share=True)

    if __name__ == "__main__":
        launch_gradio_ui()
    """)

    # utils/__init__.py content
    utils_init_py_content = textwrap.dedent("""\
    # This file makes utils a Python package.
    """)

    # ai_integration/__init__.py content
    ai_integration_init_py_content = textwrap.dedent("""\
    # This file makes ai_integration a Python package.
    """)

    # media_processing/__init__.py content
    media_processing_init_py_content = textwrap.dedent("""\
    # This file makes media_processing a Python package.
    """)

    # new_features/__init__.py content
    new_features_init_py_content = textwrap.dedent("""\
    # This file makes new_features a Python package.
    """)

    # shell_utils.py content
    shell_utils_py_content = textwrap.dedent("""\
    import subprocess
    import logging
    import shlex
    from typing import List, Tuple, Optional

    logger = logging.getLogger(__name__)

    def run_shell_command(command_args: List[str], check_error: bool = True, timeout: Optional[int] = 120) -> Tuple[str, str, int]:
        command_for_log = shlex.join(command_args)
        logger.info(f"Executing command: {command_for_log}")

        try:
            result = subprocess.run(
                command_args,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            returncode = result.returncode

            if returncode != 0:
                logger.error(f"Command failed with exit code {returncode}: {command_for_log}\\nSTDOUT: {stdout}\\nSTDERR: {stderr}")
                if check_error:
                    raise RuntimeError(f"Command failed with exit code {returncode}: {command_for_log}\\nSTDOUT: {stdout}\\nSTDERR: {stderr}")
            else:
                logger.info(f"Command executed successfully (exit code {returncode}): {command_for_log}")
                if stdout:
                    logger.info(f"STDOUT: {stdout}")
                if stderr:
                    logger.warning(f"STDERR: {stderr}")

            return stdout, stderr, returncode

        except FileNotFoundError:
            logger.critical(f"Command not found. Make sure the executable is in your PATH: {command_args[0]}")
            raise RuntimeError(f"Command not found: {command_args[0]}")
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds: {command_for_log}")
            result.kill()
            result.wait()
            raise
        except Exception as e:
            logger.critical(f"An unexpected error occurred while running command {command_for_log}: {e}", exc_info=True)
            raise
    """)

    # gcs_utils.py content
    gcs_utils_py_content = textwrap.dedent("""\
    import logging
    import os
    import io
    from typing import Optional, List, Dict, Any, Tuple
    from google.cloud import storage

    from config import GLOBAL_CONFIG

    logger = logging.getLogger(__name__)

    def get_gcs_client():
        try:
            if 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ:
                sa_key_path = GLOBAL_CONFIG['gcp']['service_account_key_path']
                if os.path.exists(sa_key_path) and os.path.isfile(sa_key_path):
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = sa_key_path
                    logger.info(f"GOOGLE_APPLICATION_CREDENTIALS set from config: {sa_key_path}")
                else:
                    logger.warning(f"Service account key not found at {sa_key_path}. GCS client might use default credentials.")

            client = storage.Client(project=GLOBAL_CONFIG['gcp']['project_id'])
            logger.info("Google Cloud Storage client initialized.")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage client: {e}", exc_info=True)
            return None

    def upload_to_gcs(source_file_name: str, destination_blob_name: str, bucket_name: Optional[str] = None) -> bool:
        client = get_gcs_client()
        if not client:
            return False

        if not os.path.exists(source_file_name):
            logger.error(f"Source file for GCS upload not found: {source_file_name}")
            return False

        bucket_name = bucket_name if bucket_name else GLOBAL_CONFIG['gcp']['gcs_bucket_name']
        if not bucket_name or bucket_name == 'your-gcs-bucket-name':
            logger.error("GCS bucket name is not configured. Cannot upload file.")
            return False

        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(source_file_name)
            logger.info(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}.")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {source_file_name} to GCS bucket {bucket_name}: {e}", exc_info=True)
            return False

    def download_from_gcs(source_blob_name: str, destination_file_name: str, bucket_name: Optional[str] = None) -> bool:
        client = get_gcs_client()
        if not client:
            return False

        bucket_name = bucket_name if bucket_name else GLOBAL_CONFIG['gcp']['gcs_bucket_name']
        if not bucket_name or bucket_name == 'your-gcs-bucket-name':
            logger.error("GCS bucket name is not configured. Cannot download file.")
            return False

        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_name)
            logger.info(f"Blob gs://{bucket_name}/{source_blob_name} downloaded to {destination_file_name}.")
            return True
        except Exception as e:
            logger.error(f"Failed to download {source_blob_name} from GCS bucket {bucket_name}: {e}", exc_info=True)
            return False

    def list_blobs(bucket_name: Optional[str] = None, prefix: Optional[str] = None) -> List[str]:
        client = get_gcs_client()
        if not client:
            return []

        bucket_name = bucket_name if bucket_name else GLOBAL_CONFIG['gcp']['gcs_bucket_name']
        if not bucket_name or bucket_name == 'your-gcs-bucket-name':
            logger.error("GCS bucket name is not configured. Cannot list blobs.")
            return []

        blobs_list = []
        try:
            bucket = client.bucket(bucket_name)
            blobs = bucket.list_blobs(prefix=prefix)
            for blob in blobs:
                blobs_list.append(blob.name)
            logger.info(f"Listed {len(blobs_list)} blobs in bucket {bucket_name} with prefix {prefix}.")
            return blobs_list
        except Exception as e:
            logger.error(f"Failed to list blobs in bucket {bucket_name} with prefix {prefix}: {e}", exc_info=True)
            return []

    def delete_blob(blob_name: str, bucket_name: Optional[str] = None) -> bool:
        client = get_gcs_client()
        if not client:
            return False

        bucket_name = bucket_name if bucket_name else GLOBAL_CONFIG['gcp']['gcs_bucket_name']
        if not bucket_name or bucket_name == 'your-gcs-bucket-name':
            logger.error("GCS bucket name is not configured. Cannot delete blob.")
            return False

        try:
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            logger.info(f"Blob gs://{bucket_name}/{blob_name} deleted.")
            return True
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name} from GCS bucket {bucket_name}: {e}", exc_info=True)
            return False
    """)

    # cleanup.py content
    cleanup_py_content = textwrap.dedent("""\
    import os
    import shutil
    import logging
    from config import GLOBAL_CONFIG

    logger = logging.getLogger(__name__)

    RUNTIME_BASE_DIR = GLOBAL_CONFIG['paths']['base_dir']
    VIDEO_DOWNLOADS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['video_downloads_dir'])
    AUDIO_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['audio_dir'])
    IMAGES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['images_dir'])
    OUTPUT_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['output_dir'])
    TEMP_FILES_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['temp_files_dir'])
    LOGS_DIR = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['logs_dir'])

    def setup_runtime_directories():
        os.makedirs(RUNTIME_BASE_DIR, exist_ok=True)
        os.makedirs(VIDEO_DOWNLOADS_DIR, exist_ok=True)
        os.makedirs(AUDIO_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(TEMP_FILES_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        logger.info(f"All runtime directories ensured under: {RUNTIME_BASE_DIR}")

    def cleanup_runtime_files():
        logger.info(f"Initiating cleanup of temporary runtime files under: {RUNTIME_BASE_DIR}")
        try:
            if os.path.exists(RUNTIME_BASE_DIR):
                for item in os.listdir(RUNTIME_BASE_DIR):
                    item_path = os.path.join(RUNTIME_BASE_DIR, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        logger.info(f"Cleaned up temporary directory: {item_path}")
                    else:
                        os.remove(item_path)
                        logger.info(f"Cleaned up temporary file: {item_path}")

                if not os.listdir(RUNTIME_BASE_DIR):
                    os.rmdir(RUNTIME_BASE_DIR)
                    logger.info(f"Removed empty base runtime directory: {RUNTIME_BASE_DIR}")
                else:
                    logger.warning(f"Runtime base directory {RUNTIME_BASE_DIR} is not empty after cleanup attempt.")
            logger.info("Temporary file cleanup complete.")
        except Exception as e:
            logger.error(f"Error during temporary file cleanup: {e}", exc_info=True)
    """)

    # ffmpeg_utils.py content
    ffmpeg_utils_py_content = textwrap.dedent("""\
    import logging
    import subprocess
    import os
    import shlex
    import math
    import random # Added for shuffle
    from typing import List, Tuple, Optional, Any
    import shutil

    from utils.shell_utils import run_shell_command
    from utils.video_utils import get_video_duration # Assuming get_video_duration is in video_utils

    logger = logging.getLogger(__name__)

    def get_video_dimensions(video_path: str) -> Optional[Tuple[int, int]]:
        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
               '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x',
               shlex.quote(video_path)]

        stdout, stderr, returncode = run_shell_command(cmd, check_error=False)

        if returncode != 0:
            logger.warning(f"ffprobe failed to get dimensions for {video_path}: {stderr}")
            return None

        try:
            dimensions_str = stdout.strip()
            width, height = map(int, dimensions_str.split('x'))
            return width, height
        except ValueError:
            logger.warning(f"Could not parse dimensions from ffprobe output for {video_path}: {stdout}")
            return None

    def concatenate_videos(
        video_paths: List[str],
        output_path: str,
        target_width: int,
        target_height: int,
        target_duration: float,
        transition: str = 'fade',
        transition_duration: float = 0.5,
        randomize_order: bool = False,
        temp_files_dir: str = '/tmp/tiktok_project_runtime/temp_files'
    ) -> Optional[str]:
        logger.info(f"Concatenating {len(video_paths)} videos to {output_path} with transition '{transition}'.")
        if not video_paths:
            logger.error("No video paths provided for concatenation.")
            return None

        os.makedirs(temp_files_dir, exist_ok=True)

        existing_video_paths = [p for p in video_paths if os.path.exists(p)]
        if len(existing_video_paths) != len(video_paths):
            logger.warning(f"Skipped {len(video_paths) - len(existing_video_paths)} non-existent video paths.")
        if not existing_video_paths:
            logger.error("No valid video paths found for concatenation after filtering.")
            return None

        if randomize_order:
            random.shuffle(existing_video_paths)
            logger.info("Video order randomized.")

        temp_scaled_videos = []
        current_total_duration = 0.0

        for i, video_path in enumerate(existing_video_paths):
            temp_output_path = os.path.join(temp_files_dir, f"scaled_clip_{i}.mp4")
            
            scale_filter = f"scale='min({target_width},iw)':'min({target_height},ih)':force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
            
            cmd = [
                'ffmpeg', '-y',
                '-i', shlex.quote(video_path),
                '-vf', scale_filter,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                temp_output_path
            ]
            stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=180)
            if returncode != 0:
                logger.error(f"Failed to scale/crop video {video_path}: {stderr}")
                continue
            temp_scaled_videos.append(temp_output_path)
            current_total_duration += get_video_duration(temp_output_path) or 0.0

        if not temp_scaled_videos:
            logger.error("No videos successfully scaled for concatenation.")
            return None

        final_clips_for_concat = list(temp_scaled_videos)
        if current_total_duration < target_duration:
            last_clip_path = final_clips_for_concat[-1]
            remaining_duration = target_duration - current_total_duration
            logger.info(f"Total clip duration ({current_total_duration:.2f}s) is less than target ({target_duration:.2f}s). Looping last clip for {remaining_duration:.2f}s.")

            temp_looped_clip_path = os.path.join(temp_files_dir, "looped_last_clip.mp4")
            
            last_clip_duration = get_video_duration(last_clip_path)
            if last_clip_duration and last_clip_duration > 0:
                num_loops = math.ceil(remaining_duration / last_clip_duration)
                
                loop_cmd = [
                    'ffmpeg', '-y',
                    '-stream_loop', str(num_loops -1),
                    '-i', shlex.quote(last_clip_path),
                    '-c', 'copy',
                    '-t', str(remaining_duration),
                    temp_looped_clip_path
                ]
                stdout, stderr, returncode = run_shell_command(loop_cmd, check_error=False, timeout=180)
                if returncode == 0 and os.path.exists(temp_looped_clip_path):
                    final_clips_for_concat.append(temp_looped_clip_path)
                    logger.info(f"Looped last clip and added to concatenation list.")
                else:
                    logger.warning(f"Failed to loop last clip: {stderr}. Proceeding without looping.")
            else:
                logger.warning("Last clip duration is zero or invalid, cannot loop.")


        concat_list_path = os.path.join(temp_files_dir, "concat_list.txt")
        with open(concat_list_path, 'w') as f:
            for clip in final_clips_for_concat:
                f.write(f"file '{clip}'\\n")

        if transition == 'none':
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list_path,
                '-c', 'copy',
                output_path
            ]
        else:
            logger.warning(f"Complex transitions like '{transition}' are not fully implemented via raw FFmpeg concat_videos. Using simple concat.")
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list_path,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                output_path
            ]

        stdout, stderr, returncode = run_shell_command(concat_cmd, check_error=False, timeout=300)

        if returncode != 0:
            logger.error(f"FFmpeg concatenation failed: {stderr}")
            return None

        logger.info(f"Videos concatenated successfully. Output: {output_path}.")

        for clip in temp_scaled_videos:
            if os.path.exists(clip):
                os.remove(clip)
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        if 'temp_looped_clip_path' in locals() and os.path.exists(temp_looped_clip_path):
            os.remove(temp_looped_clip_path)

        return output_path

    def add_audio_to_video(video_path: str, audio_path: str, output_path: str, audio_volume_db: float = 0.0) -> Optional[str]:
        logger.info(f"Adding audio from {audio_path} to {video_path} with volume {audio_volume_db}dB.")
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return None
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None

        cmd = [
            'ffmpeg', '-y',
            '-i', shlex.quote(video_path),
            '-i', shlex.quote(audio_path),
            '-map', '0:v',
            '-map', '1:a',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            '-af', f"volume={audio_volume_db}dB",
            output_path
        ]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=180)

        if returncode != 0:
            logger.error(f"FFmpeg failed to add audio: {stderr}")
            return None

        logger.info(f"Audio added to video. Output: {output_path}.")
        return output_path


    def add_subtitles_to_video(
        video_path: str,
        subtitle_file_path: str,
        output_path: str,
        font_path: str,
        font_size: int,
        font_color: str,
        outline_color: str,
        outline_width: int,
        position: int
    ) -> bool:
        logger.info(f"Adding subtitles from {subtitle_file_path} to {video_path}...")
        if not os.path.exists(video_path):
            logger.error(f"Video file not found for subtitle addition: {video_path}")
            return False
        if not os.path.exists(subtitle_file_path):
            logger.error(f"Subtitle file not found: {subtitle_file_path}")
            return False
        if not os.path.exists(font_path):
            logger.warning(f"Font file not found at {font_path}. Subtitles may not render correctly.")
            font_path = "Arial"

        escaped_subtitle_file_path = subtitle_file_path.replace('\\\\', '/').replace('\\', '/')
        
        fonts_dir = os.path.dirname(font_path) if os.path.exists(font_path) else "/usr/share/fonts/truetype/dejavu"
        
        cmd = [
            'ffmpeg', '-y',
            '-i', shlex.quote(video_path),
            '-vf', f"subtitles={shlex.quote(escaped_subtitle_file_path)}:fontsdir={shlex.quote(fonts_dir)}",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            shlex.quote(output_path)
        ]
        logger.info(f"Running FFmpeg subtitles command: {' '.join(cmd)}")
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=300)

        if returncode != 0:
            logger.error(f"FFmpeg failed to add subtitles: {stderr}")
            return False

        logger.info(f"Subtitles added to video. Output: {output_path}.")
        return True

    def escape_ffmpeg_text(text: str) -> str:
        text = text.replace('\\\\', '\\\\\\\\') # Escape existing backslashes first
        text = text.replace("'", "\\'")
        text = text.replace(':', '\\:')
        text = text.replace('\n', '\\n')
        return text
    """)

    # audio_utils.py content
    audio_utils_py_content = textwrap.dedent("""\
    import logging
    import os
    import shlex
    import requests
    import uuid
    import time
    from typing import List, Tuple, Optional, Any

    from utils.shell_utils import run_shell_command
    from config import GLOBAL_CONFIG

    logger = logging.getLogger(__name__)

    def get_audio_duration_ffprobe(audio_path: str) -> Optional[float]:
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found for duration check: {audio_path}")
            return None

        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', shlex.quote(audio_path)]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False)

        if returncode != 0:
            logger.warning(f"ffprobe failed to get audio duration for {audio_path}: {stderr}")
            return None

        try:
            duration = float(stdout.strip())
            return duration
        except ValueError:
            logger.warning(f"Could not parse duration from ffprobe output for {audio_path}: {stdout}")
            return None

    def combine_audio_tracks(
        track1_path: str,
        track2_path: str,
        output_path: str,
        track1_volume_db: float = 0.0,
        track2_volume_db: float = -15.0
    ) -> Optional[str]:
        logger.info(f"Combining audio tracks: {track1_path} (vol: {track1_volume_db}dB) and {track2_path} (vol: {track2_volume_db}dB).")
        if not os.path.exists(track1_path):
            logger.error(f"Audio track 1 not found: {track1_path}")
            return None
        if not os.path.exists(track2_path):
            logger.error(f"Audio track 2 not found: {track2_path}")
            return None

        filter_complex = f"[0:a]volume={track1_volume_db}dB[a1]; [1:a]volume={track2_volume_db}dB[a2]; [a1][a2]amix=inputs=2:duration=longest[aout]"

        cmd = [
            'ffmpeg', '-y',
            '-i', shlex.quote(track1_path),
            '-i', shlex.quote(track2_path),
            '-filter_complex', filter_complex,
            '-map', '[aout]',
            '-c:a', 'aac',
            '-b:a', '192k',
            output_path
        ]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=120)

        if returncode != 0:
            logger.error(f"FFmpeg failed to combine audio tracks: {stderr}")
            return None

        logger.info(f"Audio tracks combined. Output: {output_path}.")
        return output_path

    def download_background_music(query: str, output_dir: str, max_retries: int = 3, delay_s: int = 5) -> Optional[str]:
        logger.info(f"Simulating download of background music for query: '{query}'")
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"background_music_{uuid.uuid4().hex}.mp3")

        dummy_mp3_content = b'\\xff\\xfb\\x30\\x04' + b'\\x00' * 128 # Minimal valid MP3 header + some bytes
        try:
            with open(output_filepath, 'wb') as f:
                f.write(dummy_mp3_content)
            logger.info(f"Simulated background music downloaded to: {output_filepath}")
            return output_filepath
        except Exception as e:
            logger.error(f"Failed to create dummy background music file: {e}", exc_info=True)
            return None
    """)

    # video_utils.py content
    video_utils_py_content = textwrap.dedent("""\
    import logging
    import os
    import shlex
    import subprocess
    import requests
    from typing import Optional, Tuple, List, Dict, Any

    from utils.shell_utils import run_shell_command

    logger = logging.getLogger(__name__)

    def get_video_duration(video_path: str) -> Optional[float]:
        if not os.path.exists(video_path):
            logger.warning(f"Video file not found for duration check: {video_path}")
            return None

        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', shlex.quote(video_path)]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False)

        if returncode != 0:
            logger.warning(f"ffprobe failed to get duration for {video_path}: {stderr}")
            return None

        try:
            duration = float(stdout.strip())
            return duration
        except ValueError:
            logger.warning(f"Could not parse duration from ffprobe output for {video_path}: {stdout}")
            return None

    def get_video_resolution(video_path: str) -> Optional[Tuple[int, int]]:
        if not os.path.exists(video_path):
            logger.warning(f"Video file not found for resolution check: {video_path}")
            return None

        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
               '-of', 'csv=p=0:s=x', shlex.quote(video_path)]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False)

        if returncode != 0:
            logger.warning(f"ffprobe failed to get resolution for {video_path}: {stderr}")
            return None

        try:
            width, height = map(int, stdout.strip().split('x'))
            return width, height
        except ValueError:
            logger.warning(f"Could not parse resolution from ffprobe output for {video_path}: {stdout}")
            return None

    def download_video_clip(video_url: str, output_path: str) -> Optional[str]:
        logger.info(f"Simulating downloading video clip from {video_url} to {output_path}")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            dummy_cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi', '-i', 'color=c=black:s=640x360:d=1',
                '-vf', 'format=yuv420p',
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30',
                shlex.quote(output_path)
            ]
            stdout, stderr, returncode = run_shell_command(dummy_cmd, check_error=False, timeout=10)
            if returncode != 0:
                logger.warning(f"Failed to create dummy video, creating empty file instead: {stderr}")
                with open(output_path, 'wb') as f:
                    f.write(b'DUMMY VIDEO CONTENT')
        except Exception as e:
            logger.warning(f"Exception creating dummy video: {e}, creating empty file instead.")
            with open(output_path, 'wb') as f:
                f.write(b'DUMMY VIDEO CONTENT')

        if os.path.exists(output_path):
            logger.info(f"Simulated video download complete. Dummy file created at: {output_path}")
            return output_path
        else:
            logger.error(f"Failed to create dummy video file at {output_path}")
            return None

    def search_pexels_videos(query: str, api_key: str, orientation: str = 'portrait', per_page: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Simulating Pexels video search for '{query}', orientation: '{orientation}'")
        dummy_videos = []
        for i in range(min(per_page, 3)):
            dummy_videos.append({
                "id": f"pexels_dummy_{i}",
                "url": f"https://www.pexels.com/video/dummy-video-{i}/",
                "image": "https://images.pexels.com/videos/pixels-dummy.jpeg",
                "duration": 15 + i*5,
                "video_files": [
                    {"link": f"http://example.com/dummy_pexels_video_{i}.mp4", "quality": "hd", "width": 1080, "height": 1920, "fps": 30},
                    {"link": f"http://example.com/dummy_pexels_video_sd_{i}.mp4", "quality": "sd", "width": 720, "height": 1280, "fps": 30}
                ]
            })
        logger.info(f"Simulated Pexels search returned {len(dummy_videos)} results.")
        return dummy_videos

    def search_pixabay_videos(query: str, api_key: str, editors_choice: bool = True, per_page: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Simulating Pixabay video search for '{query}', editors_choice: {editors_choice}")
        dummy_videos = []
        for i in range(min(per_page, 3)):
            dummy_videos.append({
                "id": f"pixabay_dummy_{i}",
                "pageURL": f"https://pixabay.com/videos/dummy-video-{i}/",
                "picture_id": f"dummy_{i}",
                "duration": 20 + i*3,
                "videos": {
                    "tiny": {"url": f"http://example.com/dummy_pixabay_tiny_video_{i}.mp4"},
                    "small": {"url": f"http://example.com/dummy_pixabay_small_video_{i}.mp4"},
                    "medium": {"url": f"http://example.com/dummy_pixabay_medium_video_{i}.mp4"},
                    "large": {"url": f"http://example.com/dummy_pixabay_large_video_{i}.mp4"}
                }
            })
        logger.info(f"Simulated Pixabay search returned {len(dummy_videos)} results.")
        return dummy_videos
    """)

    # speech_synthesis.py content
    speech_synthesis_py_content = textwrap.dedent("""\
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
        api_key = GLOBAL_CONFIG['api_keys']['google_api_key']
        if not api_key or api_key == 'YOUR_GOOGLE_API_KEY_PLACEHOLDER':
            logger.error("Google API key is not configured. Cannot use Google TTS.")
            return None

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
            return None


    def synthesize_speech_azure(text: str, output_filepath: str, voice_name: str = "en-US-AvaMultilingualNeural") -> Optional[str]:
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
                return None
        except Exception as e:
            logger.error(f"Azure TTS synthesis failed: {e}", exc_info=True)
            return None

    def synthesize_speech_gtts(text: str, output_filepath: str, lang: str = 'en') -> Optional[str]:
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
        os.makedirs(audio_output_dir, exist_ok=True)
        audio_filename = f"narration_{uuid.uuid4().hex}.mp3"
        audio_filepath = os.path.join(audio_output_dir, audio_filename)

        if voice_type == SpeechSynthesisVoice.GTTS_DEFAULT:
            return synthesize_speech_gtts(text, audio_filepath)
        elif "Google" in voice_type.value:
            google_voice_name = voice_type.value.replace(" (Google)", "")
            return synthesize_speech_google(text, audio_filepath, google_voice_name)
        elif "Azure" in voice_type.value:
            azure_voice_name = voice_type.value.replace(" (Azure)", "")
            return synthesize_speech_azure(text, audio_filepath, azure_voice_name)
        else:
            logger.error(f"Unsupported speech synthesis voice type: {voice_type}")
            return None
    """)

    # image_video_generation.py content (UPDATED from previous turn)
    image_video_generation_py_content = textwrap.dedent("""\
    import logging
    import os
    import shutil # Added for dummy file creation

    logger = logging.getLogger(__name__)

    def generate_image_with_imagen(prompt: str, image_style: str = "photorealistic", aspect_ratio: str = "1:1") -> str:
        logger.info(f"Simulating AI image generation with Imagen for prompt: '{prompt}', style: '{image_style}', aspect_ratio: '{aspect_ratio}'")
        
        placeholder_image_name = f"ai_generated_image_{hash(prompt) % 1000}.png"
        temp_dir = os.path.join(os.getcwd(), "temp_ai_assets")
        os.makedirs(temp_dir, exist_ok=True)
        placeholder_image_path = os.path.join(temp_dir, placeholder_image_name)
        
        # Create a dummy file to simulate existence
        with open(placeholder_image_path, 'w') as f:
            f.write("DUMMY IMAGE CONTENT")

        logger.info(f"Placeholder image saved to: {placeholder_image_path}")
        return placeholder_image_path

    def generate_video_with_ttv_api(script_segment: str, video_style: str = "cinematic", duration_seconds: int = 5) -> str:
        logger.info(f"Simulating AI video generation with TTV API for segment: '{script_segment[:50]}...', style: '{video_style}', duration: {duration_seconds}s")

        placeholder_video_name = f"ai_generated_video_{hash(script_segment) % 1000}.mp4"
        temp_dir = os.path.join(os.getcwd(), "temp_ai_assets")
        os.makedirs(temp_dir, exist_ok=True)
        placeholder_video_path = os.path.join(temp_dir, placeholder_video_name)

        # Create a dummy file to simulate existence
        with open(placeholder_video_path, 'w') as f:
            f.write("DUMMY VIDEO CONTENT")

        logger.info(f"Placeholder video saved to: {placeholder_video_path}")
        return placeholder_video_path

    def combine_ai_visuals_with_stock_footage(ai_visual_path: str, stock_footage_paths: list[str], output_path: str) -> str:
        logger.info(f"Simulating combination of AI visual '{ai_visual_path}' with {len(stock_footage_paths)} stock clips into '{output_path}'")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        # Create a dummy file to simulate existence
        with open(output_path, 'w') as f:
            f.write("DUMMY COMBINED VIDEO CONTENT")
            
        logger.info(f"Placeholder combined video saved to: {output_path}")
        return output_path
    """)

    # video_editor.py content
    video_editor_py_content = textwrap.dedent("""\
    import os
    import logging
    import random
    import shlex # Added for shlex.quote
    import shutil # Added for shutil.copyfile if needed
    from typing import List, Optional, Tuple, Any

    from utils.ffmpeg_utils import concatenate_videos, add_audio_to_video, add_subtitles_to_video
    from utils.video_utils import get_video_duration, search_pexels_videos, search_pixabay_videos, download_video_clip
    from ai_integration.image_video_generation import generate_image_with_imagen, generate_video_with_ttv_api
    from config import GLOBAL_CONFIG
    from models import VideoTransitionMode, VideoSourceType, VideoAspect, VideoConcatMode, SubtitleEntry, SubtitleFont, SubtitlePosition

    logger = logging.getLogger(__name__)

    def generate_subtitles_file(
        subtitle_entries: List[SubtitleEntry],
        output_filepath: str,
        font: SubtitleFont,
        font_size: int,
        color: str,
        outline_color: str,
        outline_width: int,
        position: SubtitlePosition
    ) -> Optional[str]:
        logger.info(f"Generating ASS subtitle file: {output_filepath}")

        ass_content = f\"\"\"[Script Info]
    ScriptType: v4.00+
    Collisions: Normal
    PlayResX: 1920
    PlayResY: 1080

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
    Style: Default,{font.value},{font_size},{color},{color},{outline_color},{outline_color},0,0,0,0,100,100,0,0,1,{outline_width},0,{position.to_ffmpeg_ass_position()},0,0,0,1
    \"\"\"
        for entry in subtitle_entries:
            start_time = time.strftime('%H:%M:%S', time.gmtime(entry.start_time_s)) + f".{int((entry.start_time_s % 1) * 100):02d}"
            end_time = time.strftime('%H:%M:%S', time.gmtime(entry.end_time_s)) + f".{int((entry.end_time_s % 1) * 100):02d}"
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{entry.text}\\n"

        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            logger.info(f"Subtitle file created successfully: {output_filepath}")
            return output_filepath
        except Exception as e:
            logger.error(f"Failed to write subtitle file: {e}", exc_info=True)
            return None

    def download_source_clips(video_params: Any, video_downloads_dir: str, max_clip_duration_s: int) -> List[str]:
        downloaded_clip_paths = []
        
        target_width = 1080
        target_height = 1920

        if video_params.video_aspect_ratio == VideoAspect.PORTRAIT_9_16:
            target_width, target_height = 1080, 1920
        elif video_params.video_aspect_ratio == VideoAspect.LANDSCAPE_16_9:
            target_width, target_height = 1920, 1080
        elif video_params.video_aspect_ratio == VideoAspect.SQUARE_1_1:
            target_width, target_height = 1080, 1080
            
        os.makedirs(video_downloads_dir, exist_ok=True)

        if video_params.video_source_type in [VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY, VideoSourceType.STOCK_FOOTAGE_PEXELS_ONLY]:
            logger.info(f"Sourcing videos from Pexels for query: {video_params.video_subject}")
            pexels_api_key = GLOBAL_CONFIG['api_keys']['pexels_api_key']
            pexels_videos = search_pexels_videos(
                query=video_params.video_subject,
                api_key=pexels_api_key,
                orientation='portrait' if video_params.video_aspect_ratio == VideoAspect.PORTRAIT_9_16 else 'landscape',
                per_page=video_params.num_videos_to_source_or_generate
            )
            for i, video_data in enumerate(pexels_videos):
                best_video_url = None
                for v_file in video_data.get('video_files', []):
                    if v_file.get('quality') in ['hd', 'sd'] and \\
                       ((video_params.video_aspect_ratio == VideoAspect.PORTRAIT_9_16 and v_file.get('height',0) > v_file.get('width',0)) or \\
                        (video_params.video_aspect_ratio == VideoAspect.LANDSCAPE_16_9 and v_file.get('width',0) > v_file.get('height',0)) or \\
                        (video_params.video_aspect_ratio == VideoAspect.SQUARE_1_1 and v_file.get('width',0) == v_file.get('height',0) and v_file.get('width',0) > 0)):
                        best_video_url = v_file['link']
                        break
                
                if best_video_url:
                    output_filepath = os.path.join(video_downloads_dir, f"pexels_clip_{i}.mp4")
                    downloaded_path = download_video_clip(best_video_url, output_filepath)
                    if downloaded_path:
                        downloaded_clip_paths.append(downloaded_path)
                        if len(downloaded_clip_paths) >= video_params.num_videos_to_source_or_generate:
                            break
                else:
                    logger.warning(f"No suitable Pexels video link found for clip {i} for query '{video_params.video_subject}'")

        if video_params.video_source_type in [VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY, VideoSourceType.STOCK_FOOTAGE_PIXABAY_ONLY]:
            logger.info(f"Sourcing videos from Pixabay for query: {video_params.video_subject}")
            pixabay_api_key = GLOBAL_CONFIG['api_keys']['pixabay_api_key']
            pixabay_videos = search_pixabay_videos(
                query=video_params.video_subject,
                api_key=pixabay_api_key,
                per_page=video_params.num_videos_to_source_or_generate
            )
            for i, video_data in enumerate(pixabay_videos):
                video_url = video_data.get('videos', {}).get('medium', {}).get('url')
                if video_url:
                    output_filepath = os.path.join(video_downloads_dir, f"pixabay_clip_{i}.mp4")
                    downloaded_path = download_video_clip(video_url, output_filepath)
                    if downloaded_path:
                        downloaded_clip_paths.append(downloaded_path)
                        if len(downloaded_clip_paths) >= video_params.num_videos_to_source_or_generate:
                            break
                else:
                    logger.warning(f"No suitable Pixabay video link found for clip {i} for query '{video_params.video_subject}'")

        if video_params.video_source_type == VideoSourceType.AI_GENERATED_IMAGES:
            logger.info(f"Generating AI images for video: {video_params.video_subject}")
            for i in range(video_params.num_videos_to_source_or_generate):
                prompt = video_params.video_subject
                if video_params.image_prompt_suffix:
                    prompt += f", {video_params.image_prompt_suffix}"
                
                img_aspect_ratio = video_params.video_aspect_ratio.value.split(' ')[1]
                
                image_path = generate_image_with_imagen(
                    prompt=prompt,
                    image_style="photorealistic",
                    aspect_ratio=img_aspect_ratio
                )
                if image_path:
                    image_video_path = os.path.join(video_downloads_dir, f"ai_image_clip_{i}.mp4")
                    
                    from utils.shell_utils import run_shell_command # Import here to avoid circular dependency
                    cmd = [
                        'ffmpeg', '-y',
                        '-loop', '1',
                        '-i', shlex.quote(image_path),
                        '-t', str(video_params.max_clip_duration_s),
                        '-vf', f"scale={target_width}:{target_height}:force_original_aspect_ratio=increase,crop={target_width}:{target_height},setsar=1",
                        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p',
                        shlex.quote(image_video_path)
                    ]
                    stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=60)
                    if returncode == 0:
                        downloaded_clip_paths.append(image_video_path)
                    else:
                        logger.error(f"Failed to convert AI image {image_path} to video: {stderr}")

        if video_params.video_source_type == VideoSourceType.AI_GENERATED_VIDEOS:
            logger.info(f"Generating AI videos for topic: {video_params.video_subject}")
            for i in range(video_params.num_videos_to_source_or_generate):
                prompt = video_params.video_subject
                video_path = generate_video_with_ttv_api(
                    script_segment=prompt,
                    duration_seconds=video_params.max_clip_duration_s,
                    video_style="cinematic"
                )
                if video_path:
                    downloaded_clip_paths.append(video_path)

        logger.info(f"Finished sourcing/generating clips. Total clips: {len(downloaded_clip_paths)}")
        return downloaded_clip_paths


    def combine_and_edit_clips(
        video_paths: List[str],
        final_video_duration_s: int,
        video_concat_mode: VideoConcatMode,
        video_transition_mode: VideoTransitionMode,
        video_aspect_ratio: VideoAspect,
        temp_files_dir: str,
        output_base_name: str
    ) -> Optional[str]:
        logger.info(f"Starting combine and edit clips process.")

        if not video_paths:
            logger.error("No video paths provided to combine and edit.")
            return None

        target_width, target_height = 0, 0
        if video_aspect_ratio == VideoAspect.PORTRAIT_9_16:
            target_width, target_height = 1080, 1920
        elif video_aspect_ratio == VideoAspect.LANDSCAPE_16_9:
            target_width, target_height = 1920, 1080
        elif video_aspect_ratio == VideoAspect.SQUARE_1_1:
            target_width, target_height = 1080, 1080
        else:
            logger.error(f"Unsupported video aspect ratio: {video_aspect_ratio}. Defaulting to 9:16.")
            target_width, target_height = 1080, 1920

        if video_concat_mode == VideoConcatMode.RANDOM_CONCATENATION:
            random.shuffle(video_paths)
            logger.info("Video concatenation order randomized.")
        elif video_concat_mode == VideoConcatMode.SEQUENTIAL_CONCATENATION:
            logger.info("Video concatenation order is sequential.")

        final_concat_output = os.path.join(temp_files_dir, f"{output_base_name}_concatenated.mp4")

        concatenated_video_path = concatenate_videos(
            video_paths=video_paths,
            output_path=final_concat_output,
            target_width=target_width,
            target_height=target_height,
            target_duration=float(final_video_duration_s),
            transition=video_transition_mode.value.lower(),
            temp_files_dir=temp_files_dir
        )

        if not concatenated_video_path:
            logger.error("Failed to concatenate videos.")
            return None

        logger.info(f"Video clips combined into: {concatenated_video_path}")
        return concatenated_video_path
    """)

    # new_features/advanced_tts_controls.py content
    advanced_tts_controls_py_content = textwrap.dedent("""\
    import logging
    from typing import Optional, Dict, Any

    logger = logging.getLogger(__name__)

    def apply_emotional_tone(text: str, emotion: str) -> str:
        logger.info(f"Applying '{emotion}' tone to text: '{text[:50]}...'")
        return f"<voice_emotion_tag emotion='{emotion}'>{text}</voice_emotion_tag>"

    def adjust_speech_rate_and_pitch(text: str, rate_percent: float = 100.0, pitch_semitones: float = 0.0) -> str:
        logger.info(f"Adjusting speech rate to {rate_percent}% and pitch to {pitch_semitones} semitones for text: '{text[:50]}...'")
        return f"<prosody rate='{rate_percent}%' pitch='{pitch_semitones}st'>{text}</prosody>"

    def insert_pauses(text: str, pause_duration_ms: int = 500) -> str:
        logger.info(f"Inserting {pause_duration_ms}ms pauses into text: '{text[:50]}...'")
        return text.replace(".", f". <break time='{pause_duration_ms}ms'/>").replace(",", f", <break time='{pause_duration_ms}ms'/>")

    def perform_voice_cloning(input_audio_path: str, text_to_synthesize: str) -> Optional[str]:
        logger.info(f"Simulating voice cloning from {input_audio_path} for text: '{text_to_synthesize[:50]}...'")
        
        output_path = f"/tmp/tiktok_project_runtime/audio/cloned_voice_{hash(text_to_synthesize)}.mp3"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("DUMMY CLONED VOICE AUDIO")
        logger.info(f"Placeholder voice clone audio created at: {output_path}")
        return output_path
    """)

    # new_features/cost_analyzer.py content
    cost_analyzer_py_content = textwrap.dedent("""\
    import logging
    from collections import defaultdict
    from datetime import datetime
    from typing import Dict, Union, Any

    logger = logging.getLogger(__name__)

    class CostAnalyzer:
        def __init__(self):
            self.usage_metrics = defaultdict(lambda: defaultdict(float))
            self.cost_metrics = defaultdict(float)

            self.cost_rates = {
                'gemini_text_char_k': 0.0001,
                'gemini_vision_sec': 0.002,
                'google_tts_char_k': 0.004,
                'azure_tts_char_k': 0.003,
                'gtts_requests': 0.0,
                'pexels_video_search_requests': 0.001,
                'pixabay_video_search_requests': 0.001,
                'ai_image_gen_image': 0.02,
                'ai_video_gen_sec': 0.05
            }

        def record_usage(self, service: str, unit: str, value: Union[int, float]):
            self.usage_metrics[service][unit] += value
            logger.debug(f"Recorded usage: {service}, {unit}, {value}. Total: {self.usage_metrics[service][unit]}")
            self._recalculate_cost(service)

        def _recalculate_cost(self, service: str):
            total_service_cost = 0.0
            if service == 'gemini_text':
                total_service_cost += (self.usage_metrics[service]['characters'] / 1000) * self.cost_rates['gemini_text_char_k']
            elif service == 'gemini_vision':
                total_service_cost += self.usage_metrics[service]['seconds'] * self.cost_rates['gemini_vision_sec']
            elif service == 'google_tts':
                total_service_cost += (self.usage_metrics[service]['characters'] / 1000) * self.cost_rates['google_tts_char_k']
            elif service == 'azure_tts':
                total_service_cost += (self.usage_metrics[service]['characters'] / 1000) * self.cost_rates['azure_tts_char_k']
            elif service == 'gtts':
                total_service_cost += self.usage_metrics[service]['requests'] * self.cost_rates['gtts_requests']
            elif service == 'pexels_video_search':
                total_service_cost += self.usage_metrics[service]['requests'] * self.cost_rates['pexels_video_search_requests']
            elif service == 'pixabay_video_search':
                total_service_cost += self.usage_metrics[service]['requests'] * self.cost_rates['pixabay_video_search_requests']
            elif service == 'ai_image_gen':
                total_service_cost += self.usage_metrics[service]['images'] * self.cost_rates['ai_image_gen_image']
            elif service == 'ai_video_gen':
                total_service_cost += self.usage_metrics[service]['seconds'] * self.cost_rates['ai_video_gen_sec']

            self.cost_metrics[service] = total_service_cost

        def get_total_cost(self) -> float:
            return sum(self.cost_metrics.values())

        def get_detailed_report(self) -> Dict[str, Any]:
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_estimated_cost": self.get_total_cost(),
                "service_breakdown": {}
            }
            for service, units in self.usage_metrics.items():
                report['service_breakdown'][service] = {
                    "usage": dict(units),
                    "estimated_cost": self.cost_metrics.get(service, 0.0)
                }
            logger.info("Generated cost analysis report.")
            return report

        def reset(self):
            self.usage_metrics = defaultdict(lambda: defaultdict(float))
            self.cost_metrics = defaultdict(float)
            logger.info("CostAnalyzer metrics reset.")

    cost_analyzer = CostAnalyzer()
    """)

    # new_features/dynamic_visual_cues.py content (NEW FILE)
    dynamic_visual_cues_py_content = textwrap.dedent("""\
    import logging
    import os
    import shutil
    import shlex
    from typing import List, Optional, Dict, Any

    from utils.shell_utils import run_shell_command
    from utils.video_utils import get_video_duration # Re-import for get_video_duration
    from utils.ffmpeg_utils import escape_ffmpeg_text # Re-import for text escaping

    logger = logging.getLogger(__name__)

    def apply_smart_cropping_reframing(video_path: str, output_path: str, target_aspect_ratio: str = "9:16") -> Optional[str]:
        logger.info(f"Simulating smart cropping/re-framing of {video_path} to {target_aspect_ratio}...")

        width, height = 0, 0
        if target_aspect_ratio == "9:16":
            width, height = 1080, 1920
        elif target_aspect_ratio == "16:9":
            width, height = 1920, 1080
        elif target_aspect_ratio == "1:1":
            width, height = 1080, 1080
        else:
            logger.warning(f"Unsupported target aspect ratio for smart cropping: {target_aspect_ratio}. Using 9:16.")
            width, height = 1080, 1920

        if not os.path.exists(video_path):
            logger.error(f"Input video for smart cropping not found: {video_path}")
            return None
            
        cmd = [
            'ffmpeg', '-y',
            '-i', shlex.quote(video_path),
            '-vf', f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            shlex.quote(output_path)
        ]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=120)

        if returncode != 0:
            logger.error(f"FFmpeg failed to simulate smart cropping: {stderr}")
            return None

        logger.info(f"Simulated smart cropping/re-framing complete. Output: {output_path}")
        return output_path

    def generate_call_to_action_overlay(video_path: str, output_path: str, cta_text: str = "Learn More!", position: str = "bottom", duration_s: int = 5) -> Optional[str]:
        logger.info(f"Adding CTA overlay '{cta_text}' to {video_path}...")
        if not os.path.exists(video_path):
            logger.error(f"Video file not found for CTA overlay: {video_path}")
            return None
            
        video_duration = get_video_duration(video_path)
        if video_duration is None:
            logger.warning(f"Could not get video duration for {video_path}, setting CTA duration to 5s.")
            start_time_s = 0
        else:
            start_time_s = max(0, video_duration - duration_s)
            
        end_time_s = start_time_s + duration_s

        escaped_cta_text = escape_ffmpeg_text(cta_text)
        
        x_pos = "(w-text_w)/2"
        y_pos = "h-th-50" if position == "bottom" else "50"

        drawtext_filter = (
            f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"text='{escaped_cta_text}':"
            f"x={x_pos}:y={y_pos}:"
            f"fontsize=70:fontcolor=white:borderw=3:bordercolor=black:"
            f"enable='between(t,{start_time_s},{end_time_s})'"
        )

        cmd = [
            'ffmpeg', '-y',
            '-i', shlex.quote(video_path),
            '-vf', drawtext_filter,
            '-c:a', 'copy',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv42020p',
            shlex.quote(output_path)
        ]
        stdout, stderr, returncode = run_shell_command(cmd, check_error=False, timeout=120)

        if returncode != 0:
            logger.error(f"FFmpeg failed to add CTA overlay: {stderr}")
            return None

        logger.info(f"CTA overlay added. Output: {output_path}")
        return output_path

    def implement_ai_style_transfer(input_video_path: str, output_path: str, style_image_path: str) -> Optional[str]:
        logger.info(f"Simulating AI style transfer on {input_video_path} with style from {style_image_path}...")

        if not os.path.exists(input_video_path):
            logger.error(f"Input video for style transfer not found: {input_video_path}")
            return None
        if not os.path.exists(style_image_path):
            logger.warning(f"Style image for style transfer not found: {style_image_path}. Using default style.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy(input_video_path, output_path)
        logger.info(f"Placeholder AI style transfer complete. Output: {output_path}")
        return output_path
    """)

    # new_features/interactive_content_generation.py content
    interactive_content_generation_py_content = textwrap.dedent("""\
    import logging
    import time
    from typing import Dict, Any, Optional, List

    logger = logging.getLogger(__name__)

    def conduct_user_feedback_loop(current_content_draft: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Simulating user feedback loop for content refinement...")
        
        refined_content = current_content_draft.copy()
        if "script" in refined_content:
            refined_content["script"] += "\\n[User feedback applied: Script made more concise.]"
        if "video_clips" in refined_content and refined_content["video_clips"]:
            refined_content["video_clips"] = refined_content["video_clips"][:int(len(refined_content["video_clips"]) * 0.8)]
            logger.info("Removed some video clips based on simulated feedback.")
        
        logger.info("Simulated user feedback loop complete. Content refined.")
        return refined_content

    def enable_ai_driven_decision_points(prompt: str, choices: List[str]) -> str:
        logger.info(f"AI making decision for prompt: '{prompt[:50]}...' from choices: {choices}")
        
        if "positive" in prompt.lower() and "optimistic" in choices:
            decision = "optimistic"
        elif "negative" in prompt.lower() and "realistic" in choices:
            decision = "realistic"
        elif choices:
            decision = choices[0]
        else:
            decision = "no decision made"

        logger.info(f"AI decision: {decision}")
        return decision

    def integrate_realtime_data_feeds(data_feed_url: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Simulating real-time data integration from: {data_feed_url}")
        
        if "trend" in data_feed_url:
            data = {"trending_topic": "AI advancements", "hashtags": ["#AI", "#Innovation"], "popularity_score": 95}
        elif "news" in data_feed_url:
            data = {"headline": "New AI model achieves breakthrough", "source": "TechNews", "date": "2025-07-13"}
        else:
            data = {"status": "no data found for this feed"}

        logger.info(f"Simulated real-time data received: {data}")
        return data
    """)

    # new_features/intro_outro_templates.py content
    intro_outro_templates_py_content = textwrap.dedent("""\
    import logging
    import os
    import shutil
    import random # Added for consistency in imports
    from typing import Optional, List

    from utils.shell_utils import run_shell_command # Re-import for dummy video creation
    from utils.video_utils import get_video_duration, get_video_resolution # Re-import for video properties
    from utils.ffmpeg_utils import concatenate_videos # Re-import for video concatenation

    logger = logging.getLogger(__name__)

    _DUMMY_TEMPLATE_DIR = "/tmp/tiktok_project_runtime/templates"
    _DUMMY_INTRO_VIDEO = os.path.join(_DUMMY_TEMPLATE_DIR, "intro_template.mp4")
    _DUMMY_OUTRO_VIDEO = os.path.join(_DUMMY_TEMPLATE_DIR, "outro_template.mp4")

    def _create_dummy_template_files():
        os.makedirs(_DUMMY_TEMPLATE_DIR, exist_ok=True)

        if not os.path.exists(_DUMMY_INTRO_VIDEO):
            logger.info(f"Creating dummy intro video: {_DUMMY_INTRO_VIDEO}")
            cmd_intro = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=blue:s=1280x720:d=3,format=yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30', _DUMMY_INTRO_VIDEO]
            run_shell_command(cmd_intro, check_error=False, timeout=10)
        
        if not os.path.exists(_DUMMY_OUTRO_VIDEO):
            logger.info(f"Creating dummy outro video: {_DUMMY_OUTRO_VIDEO}")
            cmd_outro = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=red:s=1280x720:d=3,format=yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '30', _DUMMY_OUTRO_VIDEO]
            run_shell_command(cmd_outro, check_error=False, timeout=10)


    def get_available_intro_templates() -> List[str]:
        _create_dummy_template_files()
        logger.info("Retrieving available intro templates.")
        return ["Standard Intro", "Dynamic Title Intro"] if os.path.exists(_DUMMY_INTRO_VIDEO) else []

    def get_available_outro_templates() -> List[str]:
        _create_dummy_template_files()
        logger.info("Retrieving available outro templates.")
        return ["Standard Outro", "Social Media CTA Outro"] if os.path.exists(_DUMMY_OUTRO_VIDEO) else []

    def apply_intro_template(main_video_path: str, intro_template_name: str, output_path: str) -> Optional[str]:
        logger.info(f"Applying intro template '{intro_template_name}' to {main_video_path}...")
        _create_dummy_template_files()
        
        if not os.path.exists(main_video_path):
            logger.error(f"Main video not found for intro application: {main_video_path}")
            return None

        intro_video_path = _DUMMY_INTRO_VIDEO

        if not os.path.exists(intro_video_path):
            logger.error(f"Intro template video not found at expected path: {intro_video_path}")
            return None
        
        width, height = get_video_resolution(main_video_path)
        if not width or not height:
            logger.warning(f"Could not get resolution of main video {main_video_path}. Using default 1080x1920 for concat.")
            width, height = 1080, 1920

        concatenated_path = concatenate_videos(
            video_paths=[intro_video_path, main_video_path],
            output_path=output_path,
            target_width=width,
            target_height=height,
            target_duration=(get_video_duration(intro_video_path) or 0) + (get_video_duration(main_video_path) or 0),
            transition="none"
        )
        
        if not concatenated_path:
            logger.error("Failed to apply intro template via concatenation.")
            return None

        logger.info(f"Intro template applied. Output: {concatenated_path}")
        return concatenated_path

    def apply_outro_template(main_video_path: str, outro_template_name: str, output_path: str) -> Optional[str]:
        logger.info(f"Applying outro template '{outro_template_name}' to {main_video_path}...")
        _create_dummy_template_files()

        if not os.path.exists(main_video_path):
            logger.error(f"Main video not found for outro application: {main_video_path}")
            return None

        outro_video_path = _DUMMY_OUTRO_VIDEO

        if not os.path.exists(outro_video_path):
            logger.error(f"Outro template video not found at expected path: {outro_video_path}")
            return None

        width, height = get_video_resolution(main_video_path)
        if not width or not height:
            logger.warning(f"Could not get resolution of main video {main_video_path}. Using default 1080x1920 for concat.")
            width, height = 1080, 1920

        concatenated_path = concatenate_videos(
            video_paths=[main_video_path, outro_video_path],
            output_path=output_path,
            target_width=width,
            target_height=height,
            target_duration=(get_video_duration(main_video_path) or 0) + (get_video_duration(outro_video_path) or 0),
            transition="none"
        )

        if not concatenated_path:
            logger.error("Failed to apply outro template via concatenation.")
            return None

        logger.info(f"Outro template applied. Output: {concatenated_path}")
        return concatenated_path
    """)

    # new_features/long_form_adaptation.py content
    long_form_adaptation_py_content = textwrap.dedent("""\
    import logging
    import math
    import os
    import shutil
    from typing import List, Dict, Any, Optional, Union

    from utils.video_utils import get_video_duration # Re-import for video duration

    logger = logging.getLogger(__name__)

    def adapt_script_for_long_form(short_script: str, target_duration_minutes: int) -> Optional[str]:
        logger.info(f"Adapting script for target duration: {target_duration_minutes} minutes.")
        
        expanded_script = f\"\"\"
        [EXPANDED LONG-FORM SCRIPT]

        Initial script:
        ---
        {short_script}
        ---

        This script has been expanded to support a target duration of {target_duration_minutes} minutes.
        More details, examples, and deeper dives into each topic would be generated here by an LLM.

        Example expansion points:
        - Elaborate on the introduction with historical context or broader implications.
        - Add detailed case studies or real-world applications for each point mentioned.
        - Introduce additional related sub-topics.
        - Include a more extensive conclusion or call to action suitable for longer content.

        [END OF EXPANDED SCRIPT]
        \"\"\"
        logger.info("Script adaptation simulated.")
        return expanded_script

    def segment_video_for_chapters(video_path: str, chapter_markers: List[Dict[str, Union[str, float]]]) -> Optional[Dict[str, Any]]:
        logger.info(f"Simulating segmentation of {video_path} into {len(chapter_markers)} chapters.")

        if not os.path.exists(video_path):
            logger.error(f"Video file not found for segmentation: {video_path}")
            return None

        segmented_output_details = {
            "original_video": video_path,
            "chapters": []
        }

        video_duration = get_video_duration(video_path) or 0
        
        current_time = 0.0
        for i, marker in enumerate(chapter_markers):
            chapter_name = marker.get("name", f"Chapter {i+1}")
            chapter_start = marker.get("start_time_s", current_time)
            chapter_end = marker.get("end_time_s", min(chapter_start + 60, video_duration))
            
            chapter_output_path = video_path.replace(".mp4", f"_chapter_{i+1}.mp4")
            
            os.makedirs(os.path.dirname(chapter_output_path), exist_ok=True)
            with open(chapter_output_path, 'w') as f:
                f.write(f"DUMMY CONTENT FOR {chapter_name} ({chapter_start}-{chapter_end})")

            segmented_output_details["chapters"].append({
                "name": chapter_name,
                "start_time_s": chapter_start,
                "end_time_s": chapter_end,
                "output_file": chapter_output_path
            })
            current_time = chapter_end

        logger.info("Video segmentation simulated.")
        return segmented_output_details

    def optimize_for_platform(video_path: str, platform: str) -> Optional[str]:
        logger.info(f"Simulating optimization of {video_path} for platform: {platform}.")

        if not os.path.exists(video_path):
            logger.error(f"Video file not found for optimization: {video_path}")
            return None

        optimized_path = video_path.replace(".mp4", f"_{platform}_optimized.mp4")
        
        os.makedirs(os.path.dirname(optimized_path), exist_ok=True)
        shutil.copy(video_path, optimized_path)

        logger.info(f"Video optimization for {platform} simulated. Output: {optimized_path}")
        return optimized_path
    """)

    # new_features/multilingual_support.py content
    multilingual_support_py_content = textwrap.dedent("""\
    import logging
    from typing import List, Dict, Any, Optional

    logger = logging.getLogger(__name__)

    def translate_text(text: str, target_language_code: str, source_language_code: Optional[str] = None) -> Optional[str]:
        logger.info(f"Simulating translation of text to {target_language_code}...")
        
        translations = {
            "en": {"hello": "hello", "world": "world", "ai": "AI"},
            "es": {"hello": "hola", "world": "mundo", "ai": "IA"},
            "fr": {"hello": "bonjour", "world": "monde", "ai": "IA"},
            "de": {"hello": "hallo", "world": "welt", "ai": "KI"},
        }
        
        translated_words = []
        for word in text.lower().split():
            translated_words.append(translations.get(target_language_code, {}).get(word, word))
        
        translated_text = " ".join(translated_words) + f" [Translated to {target_language_code}]"
        logger.info(f"Simulated translation: '{text[:50]}...' -> '{translated_text[:50]}...'")
        return translated_text

    def generate_multilingual_captions(original_captions: List[Dict[str, Any]], target_languages: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        logger.info(f"Generating multilingual captions for languages: {target_languages}")
        multilingual_captions = {"original": original_captions}

        for lang in target_languages:
            translated_captions = []
            for entry in original_captions:
                translated_text = translate_text(entry['text'], lang, source_language_code="en")
                if translated_text:
                    translated_captions.append({
                        "text": translated_text,
                        "start_time_s": entry['start_time_s'],
                        "end_time_s": entry['end_time_s']
                    })
            multilingual_captions[lang] = translated_captions
        
        logger.info(f"Multilingual caption generation simulated for {len(target_languages)} languages.")
        return multilingual_captions

    def detect_language(text: str) -> Optional[str]:
        logger.info(f"Simulating language detection for text: '{text[:50]}...'")
        
        if "hello" in text.lower() or "apple" in text.lower():
            return "en"
        elif "hola" in text.lower() or "manzana" in text.lower():
            return "es"
        elif "bonjour" in text.lower() or "pomme" in text.lower():
            return "fr"
        else:
            return "unknown"
    """)

    # new_features/niche_content_specialization.py content
    niche_content_specialization_py_content = textwrap.dedent("""\
    import logging
    from typing import Dict, Any, Optional, List

    logger = logging.getLogger(__name__)

    def generate_niche_specific_script(niche_topic: str, persona: str, keywords: List[str]) -> Optional[str]:
        logger.info(f"Generating niche-specific script for '{niche_topic}' with persona '{persona}' and keywords: {keywords}")
        
        script = f\"\"\"
        [NICHE-SPECIFIC SCRIPT: {niche_topic.upper()}]

        As a {persona}, let's talk about {niche_topic}!
        Keywords: {', '.join(keywords)}.

        This section would contain a script meticulously crafted by an advanced LLM
        to resonate with the target niche audience. It would use specialized terminology,
        address specific pain points or interests, and maintain the chosen persona's voice.

        For instance, if 'niche_topic' is "Quantum Computing" and 'persona' is "Enthusiastic Professor",
        the script would be filled with accessible explanations and exciting analogies.

        [END OF NICHE SCRIPT]
        \"\"\"
        logger.info("Niche-specific script generation simulated.")
        return script

    def select_niche_visual_style(niche_theme: str) -> Dict[str, Any]:
        logger.info(f"Selecting visual style for niche theme: '{niche_theme}'")
        
        style_guide = {
            "science_fiction": {"aesthetic": "futuristic, neon, high-tech", "color_palette": "blues, purples, cyans"},
            "nature_documentary": {"aesthetic": "lush, serene, natural light", "color_palette": "greens, browns, earth tones"},
            "cooking_show": {"aesthetic": "bright, clean, appetizing", "color_palette": "warm yellows, reds, whites"},
            "default": {"aesthetic": "clean, modern", "color_palette": "balanced"}
        }
        
        chosen_style = style_guide.get(niche_theme.lower().replace(" ", "_"), style_guide["default"])
        logger.info(f"Selected visual style: {chosen_style}")
        return chosen_style

    def integrate_community_feedback(niche_community: str, content_draft: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Simulating integration of feedback from {niche_community} community.")
        refined_content = content_draft.copy()
        
        if niche_community == "Gaming":
            feedback_points = ["More action shots", "Include specific game references", "Faster pacing"]
            if "script" in refined_content:
                refined_content["script"] += "\\n[Gaming community feedback: Add more game-specific language.]"
            logger.info(f"Applied simulated gaming community feedback: {feedback_points}")
        else:
            logger.info("No specific community feedback for this niche simulated.")

        return refined_content
    """)

    # new_features/integrated_music_library.py content (NEW FILE)
    integrated_music_library_py_content = textwrap.dedent("""\
    import logging
    import os
    import random
    import shutil
    from typing import List, Optional, Dict, Any

    logger = logging.getLogger(__name__)

    _MUSIC_LIBRARY_DIR = "/tmp/tiktok_project_runtime/music_library"

    def _create_dummy_music_files():
        os.makedirs(_MUSIC_LIBRARY_DIR, exist_ok=True)
        if not os.path.exists(os.path.join(_MUSIC_LIBRARY_DIR, "upbeat_cinematic_dummy.mp3")):
            logger.info("Creating dummy music files...")
            dummy_mp3_content = b'\\xff\\xfb\\x30\\x04' + b'\\x00' * 128
            try:
                with open(os.path.join(_MUSIC_LIBRARY_DIR, "upbeat_cinematic_dummy.mp3"), 'wb') as f:
                    f.write(dummy_mp3_content)
                with open(os.path.join(_MUSIC_LIBRARY_DIR, "calm_acoustic_dummy.mp3"), 'wb') as f:
                    f.write(dummy_mp3_content)
                logger.info("Dummy music files created.")
            except Exception as e:
                logger.error(f"Failed to create dummy music files: {e}", exc_info=True)


    def search_music_by_mood_genre(mood: str, genre: str, duration_s: int) -> List[str]:
        logger.info(f"Searching music library for mood '{mood}', genre '{genre}', duration {duration_s}s...")
        _create_dummy_music_files() # Ensure dummy files exist
        
        available_music = []
        if "upbeat" in mood.lower() and "cinematic" in genre.lower():
            if os.path.exists(os.path.join(_MUSIC_LIBRARY_DIR, "upbeat_cinematic_dummy.mp3")):
                available_music.append(os.path.join(_MUSIC_LIBRARY_DIR, "upbeat_cinematic_dummy.mp3"))
        if "calm" in mood.lower() and "acoustic" in genre.lower():
            if os.path.exists(os.path.join(_MUSIC_LIBRARY_DIR, "calm_acoustic_dummy.mp3")):
                available_music.append(os.path.join(_MUSIC_LIBRARY_DIR, "calm_acoustic_dummy.mp3"))
        
        logger.info(f"Simulated music search found {len(available_music)} tracks.")
        return available_music

    def analyze_audio_for_beats(audio_path: str) -> List[float]:
        logger.info(f"Analyzing {audio_path} for beat detection...")
        # TODO: Integrate with audio analysis libraries like Librosa or Aubio
        # This would involve loading the audio, performing beat tracking, and returning timestamps.
        
        # Placeholder: return dummy beat times
        duration = 30.0 # Assume dummy duration
        beat_times = [i * 0.75 for i in range(int(duration / 0.75))] # Every 0.75 seconds
        logger.info(f"Simulated beat detection returned {len(beat_times)} beats.")
        return beat_times

    def integrate_music_with_video_sync(video_path: str, music_path: str, beat_times: List[float], output_path: str) -> Optional[str]:
        logger.info(f"Integrating music {music_path} with video {video_path} using beat sync...")
        # TODO: Implement complex FFmpeg filtergraphs or moviepy logic to synchronize video cuts
        # or visual effects with detected beat times.
        
        if not os.path.exists(video_path):
            logger.error(f"Video file not found for music integration: {video_path}")
            return None
        if not os.path.exists(music_path):
            logger.error(f"Music file not found for integration: {music_path}")
            return None
            
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        shutil.copy(video_path, output_path) # Simple copy for placeholder
        logger.info(f"Simulated music integration complete. Output: {output_path}")
        return output_path
    """)

    # new_features/list_project_files.py content
    list_project_files_py_content = textwrap.dedent("""\
    import os
    import logging
    import datetime

    logger = logging.getLogger(__name__)

    def update_project_file_list(project_root_dir: str):
        project_files_expected = [
            "config.py",
            "models.py",
            "pipeline.py",
            "ui_pipeline.py",
            os.path.join("utils", "__init__.py"),
            os.path.join("utils", "shell_utils.py"),
            os.path.join("utils", "gcs_utils.py"),
            os.path.join("utils", "cleanup.py"),
            os.path.join("utils", "ffmpeg_utils.py"),
            os.path.join("utils", "audio_utils.py"), # New file
            os.path.join("utils", "video_utils.py"),
            os.path.join("ai_integration", "__init__.py"),
            os.path.join("ai_integration", "gemini_integration.py"),
            os.path.join("ai_integration", "speech_synthesis.py"),
            os.path.join("ai_integration", "image_video_generation.py"),
            os.path.join("media_processing", "__init__.py"),
            os.path.join("media_processing", "video_editor.py"),
            os.path.join("new_features", "__init__.py"),
            os.path.join("new_features", "project_roadmap.py"),
            os.path.join("new_features", "advanced_tts_controls.py"),
            os.path.join("new_features", "cost_analyzer.py"),
            os.path.join("new_features", "dynamic_visual_cues.py"), # New file
            os.path.join("new_features", "interactive_content_generation.py"),
            os.path.join("new_features", "intro_outro_templates.py"),
            os.path.join("new_features", "long_form_adaptation.py"),
            os.path.join("new_features", "niche_content_specialization.py"),
            os.path.join("new_features", "integrated_music_library.py"), # New file
            os.path.join("new_features", "multilingual_support.py"),
            os.path.join("new_features", "feature_integration_pipeline.py"), # The 5000 features framework
            "write_all_project_files.py" # The script that contains all other files
        ]

        output_lines = []
        output_lines.append("--- Einstein Coder Project Files List ---\\n")
        output_lines.append("Generated on: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\\n")
        output_lines.append("Relative paths from project_2.0 folder, with existence check:\\n\\n")

        docs_dir = os.path.join(project_root_dir, 'docs')
        os.makedirs(docs_dir, exist_ok=True)
        
        output_filename = os.path.join(docs_dir, "project_files_list.txt")
        
        for i, file_path_rel in enumerate(project_files_expected):
            full_path_on_drive = os.path.join(project_root_dir, file_path_rel)
            status = " (Exists)" if os.path.exists(full_path_on_drive) else " (MISSING!)"
            output_lines.append(f"{i+1:02d}. {file_path_rel}{status}\\n")
        
        output_lines.append("\\n--- END OF LIST ---")

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.writelines(output_lines)
            logger.info(f"Project file list generated and saved to Google Drive: {output_filename}")
        except Exception as e:
            logger.error(f"Failed to write project file list to Drive: {e}", exc_info=True)

    if __name__ == "__main__":
        if 'PROJECT_ROOT_DIR' in globals():
            update_project_file_list(PROJECT_ROOT_DIR)
        else:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            logger.warning("PROJECT_ROOT_DIR not found. Attempting with current directory (may not be correct in Colab).")
            update_project_file_list(os.getcwd())
    """)

    # new_features/list_writefiles.py content (This file might become less relevant with write_all_project_files.py)
    list_writefiles_py_content = textwrap.dedent("""\
    import os
    import logging

    logger = logging.getLogger(__name__)

    def generate_writefile_commands(project_root_dir: str) -> str:
        """
        Generates a string containing %%writefile commands for all .py files
        in the project_2.0 structure. This is mostly for reference/troubleshooting
        since `write_all_project_files.py` now handles batch updates.
        """
        project_files_to_write = [
            "config.py",
            "models.py",
            "pipeline.py",
            "ui_pipeline.py",
            os.path.join("utils", "__init__.py"),
            os.path.join("utils", "shell_utils.py"),
            os.path.join("utils", "gcs_utils.py"),
            os.path.join("utils", "cleanup.py"),
            os.path.join("utils", "ffmpeg_utils.py"),
            os.path.join("utils", "audio_utils.py"),
            os.path.join("utils", "video_utils.py"),
            os.path.join("ai_integration", "__init__.py"),
            os.path.join("ai_integration", "gemini_integration.py"),
            os.path.join("ai_integration", "speech_synthesis.py"),
            os.path.join("ai_integration", "image_video_generation.py"),
            os.path.join("media_processing", "__init__.py"),
            os.path.join("media_processing", "video_editor.py"),
            os.path.join("new_features", "__init__.py"),
            os.path.join("new_features", "project_roadmap.py"),
            os.path.join("new_features", "advanced_tts_controls.py"),
            os.path.join("new_features", "cost_analyzer.py"),
            os.path.join("new_features", "dynamic_visual_cues.py"),
            os.path.join("new_features", "interactive_content_generation.py"),
            os.path.join("new_features", "intro_outro_templates.py"),
            os.path.join("new_features", "long_form_adaptation.py"),
            os.path.join("new_features", "niche_content_specialization.py"),
            os.path.join("new_features", "integrated_music_library.py"),
            os.path.join("new_features", "multilingual_support.py"),
            os.path.join("new_features", "feature_integration_pipeline.py")
        ]

        commands = ["# --- GENERATED %%writefile COMMANDS ---\\n"]
        for file_path_rel in project_files_to_write:
            full_path = os.path.join(project_root_dir, file_path_rel)
            commands.append(f"%%writefile {full_path}\\n# Content for {file_path_rel}\\n# ... (actual content would follow)\\n\\n")
        commands.append("# --- END OF GENERATED COMMANDS ---")
        
        logger.info("Generated list of %%writefile commands.")
        return "".join(commands)

    if __name__ == "__main__":
        if 'PROJECT_ROOT_DIR' in globals():
            commands_str = generate_writefile_commands(PROJECT_ROOT_DIR)
            print(commands_str)
        else:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            logger.warning("PROJECT_ROOT_DIR not found. Cannot generate commands for specific path.")
            print("Please define PROJECT_ROOT_DIR to generate specific %%writefile commands.")
    """)

    # new_features/feature_integration_pipeline.py content (The 5000 features framework)
    feature_integration_pipeline_py_content = textwrap.dedent("""\
    import logging
    import os
    import pandas as pd
    from typing import List, Dict, Any, Optional

    # Import new feature modules
    from new_features.advanced_tts_controls import apply_emotional_tone, adjust_speech_rate_and_pitch, insert_pauses, perform_voice_cloning
    from new_features.dynamic_visual_cues import apply_smart_cropping_reframing, generate_call_to_action_overlay, implement_ai_style_transfer
    from new_features.interactive_content_generation import conduct_user_feedback_loop, enable_ai_driven_decision_points, integrate_realtime_data_feeds
    from new_features.intro_outro_templates import apply_intro_template, apply_outro_template
    from new_features.long_form_adaptation import adapt_script_for_long_form, segment_video_for_chapters, optimize_for_platform
    from new_features.multilingual_support import translate_text, generate_multilingual_captions, detect_language
    from new_features.niche_content_specialization import generate_niche_specific_script, select_niche_visual_style, integrate_community_feedback
    from new_features.integrated_music_library import search_music_by_mood_genre, analyze_audio_for_beats, integrate_music_with_video_sync
    from new_features.cost_analyzer import cost_analyzer # Global instance

    logger = logging.getLogger(__name__)

    FEATURES_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'einstein_coder_5000_features.csv')

    def load_features_from_csv(csv_path: str) -> pd.DataFrame:
        """Loads features from the CSV file."""
        if not os.path.exists(csv_path):
            logger.error(f"Features CSV not found at: {csv_path}. Cannot load features.")
            return pd.DataFrame()
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} features from CSV.")
            return df
        except Exception as e:
            logger.error(f"Error loading features CSV {csv_path}: {e}", exc_info=True)
            return pd.DataFrame()

    def execute_feature_by_id(feature_id: int, current_project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a specific feature based on its ID from the CSV.
        This is a conceptual dispatcher for individual feature implementations.
        """
        df_features = load_features_from_csv(FEATURES_CSV_PATH)
        feature_row = df_features[df_features['Feature ID'] == feature_id]

        if feature_row.empty:
            logger.warning(f"Feature ID {feature_id} not found in CSV. Skipping execution.")
            return current_project_state

        feature_name = feature_row['Feature Name'].iloc[0]
        category = feature_row['Category'].iloc[0]
        description = feature_row['Description'].iloc[0]

        logger.info(f"Executing feature (ID: {feature_id}, Category: {category}): {feature_name} - {description}")

        updated_state = current_project_state.copy()

        # --- Feature Dispatching Logic (Conceptual) ---
        # This is where you would call the actual implementation functions
        # from the respective new_features modules based on the category and feature name.

        if category == "Templates":
            if "Job Queue" in feature_name:
                logger.info(f"Feature: Implement Job Queue (Templates v2).")
                # TODO: Integrate with a job queuing system (e.g., Celery, GCP Cloud Tasks)
            elif "Conversion Tracking" in feature_name:
                logger.info(f"Feature: Implement Conversion Tracking (Templates v3).")
                # TODO: Implement analytics events and tracking pixels
        elif category == "Analytics":
            if "AI Image Generation" in feature_name and "Analytics" in feature_name: # AI Image Gen (Analytics v4)
                logger.info(f"Feature: Analyze AI Image Generation analytics (v4).")
                # This would typically read logs or data from image_video_generation calls
                cost_analyzer.record_usage('ai_image_gen', 'images', 1) # Example usage recording
                logger.info(f"Current estimated AI Image Gen cost: ${cost_analyzer.cost_metrics.get('ai_image_gen', 0.0):.4f}")
        elif category == "AI Integration":
            if "Motion Tracking" in feature_name:
                logger.info(f"Feature: Implement Motion Tracking (AI Integration v5).")
                # This would involve `dynamic_visual_cues.py` or a new module
                # Example: updated_state['video_path'] = apply_smart_cropping_reframing(updated_state['video_path'], "temp_output.mp4")
        elif category == "Engagement":
            if "Animated Captions" in feature_name:
                logger.info(f"Feature: Implement Animated Captions (Engagement v6).")
                # This would involve `media_processing/video_editor.py` for burning
                # and potentially a new subtitle animation module.
        # --- Add more `elif` blocks for other categories and features ---
        # For example:
        elif category == "Audio & Voice Enhancements":
            if "Voice Synthesis" in feature_name:
                # Example: Call apply_emotional_tone or adjust_speech_rate_and_pitch
                logger.info(f"Feature: Advanced Voice Synthesis control (e.g., emotional tone).")
                # updated_state['script'] = apply_emotional_tone(updated_state['script'], "joyful")
            elif "Music Integration" in feature_name:
                logger.info(f"Feature: AI-powered music selection and beat detection.")
                # music_tracks = search_music_by_mood_genre("upbeat", "electronic", 60)
                # beat_times = analyze_audio_for_beats(music_tracks[0]) if music_tracks else []
                # integrate_music_with_video_sync(current_project_state.get('video_path'), music_tracks[0], beat_times, "output_synced.mp4")
        elif category == "Captions & Subtitles Enhancements":
            if "Multilingual Captions" in feature_name:
                logger.info(f"Feature: Generate multilingual captions.")
                # original_subs = current_project_state.get('subtitle_entries', [])
                # multilingual_subs = generate_multilingual_captions(original_subs, ["es", "fr"])
                # updated_state['multilingual_subtitles'] = multilingual_subs
        elif category == "Scheduling, Orchestration & Automation":
            if "Content Calendar" in feature_name:
                logger.info(f"Feature: Content Calendar & Scheduling system.")
            elif "Multi-Agent" in feature_name:
                logger.info(f"Feature: Multi-Agent & Parallel Architecture.")
        elif category == "Monetization & Rapid Growth":
            if "Affiliate & TikTok Shop Integration" in feature_name:
                logger.info(f"Feature: Auto-generate product videos for TikTok Shop.")
        elif category == "Compliance, Safety & Trust":
            if "AI Content Moderation" in feature_name:
                logger.info(f"Feature: AI content moderation for visuals, audio, text.")
        elif category == "Tech Stack & Infrastructure":
            logger.info(f"Feature: Tech Stack & Infrastructure related update/tracking.")

        else:
            logger.info(f"No specific implementation logic yet for feature: {feature_name} in category {category}.")

        return updated_state

    def run_all_features_pipeline(initial_project_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Conceptually runs a pipeline that incorporates all new features.
        This function iterates through all features in the CSV and "executes" them conceptually.
        """
        logger.info("Initiating the '5000 Features' integration pipeline.")
        df_features = load_features_from_csv(FEATURES_CSV_PATH)
        
        current_state = initial_project_state if initial_project_state is not None else {}
        
        # Example: Add some dummy initial state if none provided
        if 'script' not in current_state:
            current_state['script'] = "This is a sample script for feature testing."
        if 'video_path' not in current_state:
            current_state['video_path'] = "/tmp/tiktok_project_runtime/output/dummy_video_for_features.mp4"
            # Ensure dummy video exists for placeholder operations
            os.makedirs(os.path.dirname(current_state['video_path']), exist_ok=True)
            with open(current_state['video_path'], 'w') as f:
                f.write("DUMMY VIDEO CONTENT FOR FEATURE PIPELINE")

        # Iterate through features (you might want to prioritize based on Status/Priority)
        for index, row in df_features.iterrows():
            feature_id = row['Feature ID']
            logger.info(f"Processing feature ID: {feature_id} - {row['Feature Name']}")
            current_state = execute_feature_by_id(feature_id, current_state)
            
        logger.info("Finished '5000 Features' integration pipeline (conceptual).")
        logger.info(f"Total estimated cost from feature integration: ${cost_analyzer.get_total_cost():.4f}")
        return current_state

    if __name__ == "__main__":
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Ensure the dummy CSV is accessible if running standalone
        # In Colab, the main notebook will write the CSV.
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(FEATURES_CSV_PATH):
            logger.warning(f"Feature CSV not found at {FEATURES_CSV_PATH}. Creating a dummy one.")
            dummy_data = {
                'Feature ID': [1, 2, 3, 4, 5],
                'Category': ['Templates', 'Analytics', 'AI Integration', 'Engagement', 'Audio & Voice Enhancements'],
                'Feature Name': ['Job Queue (Templates v2)', 'Conversion Tracking (Templates v3)', 'AI Image Generation (Analytics v4)', 'Motion Tracking (AI Integration v5)', 'Animated Captions (Engagement v6)'],
                'Description': ['Manage multiple processing tasks asynchronously', 'Track clicks and conversions', 'Create unique images for scenes', 'Track and overlay graphics', 'Add animated, styled captions'],
                'Status': ['Idea', 'Idea', 'Idea', 'In Progress', 'Idea'],
                'Priority': ['Low', 'Medium', 'Medium', 'High', 'Medium'],
                'Owner': ['Eve', 'Dave', 'Eve', 'Eve', 'Judy'],
                'Notes': ['Auto-generated', 'Auto-generated', 'Auto-generated', 'Auto-generated', 'Auto-generated']
            }
            pd.DataFrame(dummy_data).to_csv(FEATURES_CSV_PATH, index=False)
            logger.info("Dummy features CSV created.")

        final_state = run_all_features_pipeline()
        print("\\nFinal Project State after conceptual feature integration:")
        import json
        print(json.dumps(final_state, indent=2))
    """)

    files_to_write = {
        "config.py": config_py_content,
        "models.py": models_py_content,
        "pipeline.py": pipeline_py_content,
        "ui_pipeline.py": ui_pipeline_py_content,
        os.path.join("utils", "__init__.py"): utils_init_py_content,
        os.path.join("utils", "shell_utils.py"): shell_utils_py_content,
        os.path.join("utils", "gcs_utils.py"): gcs_utils_py_content,
        os.path.join("utils", "cleanup.py"): cleanup_py_content,
        os.path.join("utils", "ffmpeg_utils.py"): ffmpeg_utils_py_content,
        os.path.join("utils", "audio_utils.py"): audio_utils_py_content,
        os.path.join("utils", "video_utils.py"): video_utils_py_content,
        os.path.join("ai_integration", "__init__.py"): ai_integration_init_py_content,
        os.path.join("ai_integration", "gemini_integration.py"): gemini_integration_py_content,
        os.path.join("ai_integration", "speech_synthesis.py"): speech_synthesis_py_content,
        os.path.join("ai_integration", "image_video_generation.py"): image_video_generation_py_content,
        os.path.join("media_processing", "__init__.py"): media_processing_init_py_content,
        os.path.join("media_processing", "video_editor.py"): video_editor_py_content,
        os.path.join("new_features", "__init__.py"): new_features_init_py_content,
        os.path.join("new_features", "project_roadmap.py"): project_roadmap_py_content,
        os.path.join("new_features", "advanced_tts_controls.py"): advanced_tts_controls_py_content,
        os.path.join("new_features", "cost_analyzer.py"): cost_analyzer_py_content,
        os.path.join("new_features", "dynamic_visual_cues.py"): dynamic_visual_cues_py_content,
        os.path.join("new_features", "interactive_content_generation.py"): interactive_content_generation_py_content,
        os.path.join("new_features", "intro_outro_templates.py"): intro_outro_templates_py_content,
        os.path.join("new_features", "long_form_adaptation.py"): long_form_adaptation_py_content,
        os.path.join("new_features", "niche_content_specialization.py"): niche_content_specialization_py_content,
        os.path.join("new_features", "integrated_music_library.py"): integrated_music_library_py_content,
        os.path.join("new_features", "multilingual_support.py"): multilingual_support_py_content,
        os.path.join("new_features", "feature_integration_pipeline.py"): feature_integration_pipeline_py_content,
        os.path.join("new_features", "list_project_files.py"): list_project_files_py_content,
        os.path.join("new_features", "list_writefiles.py"): list_writefiles_py_content,
    }

    # Ensure all parent directories exist before writing files
    for file_path_rel in files_to_write.keys():
        full_path = os.path.join(project_root_dir, file_path_rel)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Write each file
    for file_path_rel, content in files_to_write.items():
        full_path = os.path.join(project_root_dir, file_path_rel)
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Successfully wrote/updated: {file_path_rel}")
        except Exception as e:
            logger.error(f"Failed to write file {file_path_rel}: {e}", exc_info=True)

    logger.info("Batch update of all .py files complete.")

# This is the entry point if this script is executed directly (not common in Colab setup)
if __name__ == "__main__":
    if 'PROJECT_ROOT_DIR' in globals():
        write_all_files(PROJECT_ROOT_DIR)
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logger.error("PROJECT_ROOT_DIR not defined. Cannot run batch write.")
