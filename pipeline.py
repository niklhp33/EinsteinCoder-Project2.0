import os
import logging
import time
import shutil
import json
from typing import Optional, List, Dict, Any

from config import GLOBAL_CONFIG
from models import VideoParams, VideoAspect, VideoSourceType, SpeechSynthesisVoice, SubtitleFont, SubtitlePosition, VideoConcatMode, VideoTransitionMode, SubtitleEntry
from media_processing.video_editor import VideoEditor
from ai_integration.gemini_integration import generate_video_script, analyze_video_content
from utils.audio_utils import get_audio_duration_ffprobe, combine_audio_tracks, synthesize_speech_google, synthesize_speech_azure, synthesize_speech_gtts
from utils.video_utils import find_font_path
from utils.cleanup import setup_runtime_directories, cleanup_runtime_files, LOGS_DIR, RUNTIME_BASE_DIR

logger = logging.getLogger(__name__)

# Define PROJECT_ROOT_DIR_CURRENT globally in this module, similar to how it's done in the main notebook.
try:
    PROJECT_ROOT_DIR_CURRENT = '/content/drive/MyDrive/project_2.0'
except NameError:
    logger.warning("PROJECT_ROOT_DIR not found in global scope. Assuming default project_2.0 structure on Drive.")
    PROJECT_ROOT_DIR_CURRENT = '/content/drive/MyDrive/project_2.0'


class VideoGenerationPipeline:
    def __init__(self):
        self.video_editor = VideoEditor()

    def run(self, params: VideoParams):
        logger.info(f"--- Starting Video Generation Pipeline for subject: '{params.video_subject}' ---")
        logger.info(f"Pipeline Parameters: {json.dumps(params.dict(), indent=2)}")

        if 'PROJECT_ROOT_DIR_CURRENT' not in globals():
            global PROJECT_ROOT_DIR_CURRENT
            PROJECT_ROOT_DIR_CURRENT = '/content/drive/MyDrive/project_2.0'

        try:
            # Step 1: Set up runtime directories
            setup_runtime_directories()
            self.video_editor.setup_local_runtime_directories()
            logger.info("Step 1/9: Runtime directories set up (local /tmp and Google Drive).")

            # Step 2: Generate video script
            logger.info(f"Step 2/9: Generating video script from Gemini for subject '{params.video_subject}'...")
            script_segments = generate_video_script(
                video_subject=params.video_subject,
                video_language=params.video_language.value,
                final_video_duration_s=params.final_video_duration_s
            )
            if not script_segments:
                logger.error("Failed to generate video script. Aborting.")
                return False
            logger.info(f"Script generated with {len(script_segments)} segments.")
            full_script_text = "\n".join(script_segments)

            # Step 3: Generate narration audio
            logger.info(f"Step 3/9: Generating narration audio using {params.speech_synthesis_voice.value} voice...")
            narration_audio_dir = os.path.join(RUNTIME_BASE_DIR, GLOBAL_CONFIG['paths']['audio_dir'])
            os.makedirs(narration_audio_dir, exist_ok=True)
            narration_audio_path = os.path.join(narration_audio_dir, "narration_audio.mp3")
            
            narration_result_path = None
            voice_value = params.speech_synthesis_voice.value

            if "Azure" in voice_value:
                narration_result_path = synthesize_speech_azure(full_script_text, voice_value, narration_audio_path)
            elif "gTTS" in voice_value:
                lang_code = voice_value.split(' ')[0]
                narration_result_path = synthesize_speech_gtts(full_script_text, lang_code, narration_audio_path)
            else: # Assume Google Cloud TTS
                narration_result_path = synthesize_speech_google(full_script_text, voice_value, narration_audio_path)

            if not narration_result_path:
                logger.error("Failed to generate narration audio. Aborting.")
                return False
            logger.info(f"Narration audio generated and saved to {narration_result_path}")
            
            narration_duration = get_audio_duration_ffprobe(narration_result_path)
            if narration_duration is None:
                logger.warning("Could not determine narration duration. Proceeding with default video duration assumptions.")
                narration_duration = params.final_video_duration_s
            else:
                logger.info(f"Narration audio generated with duration: {narration_duration:.2f}s")

            # Step 4: Source/Generate visual assets
            logger.info(f"Step 4/9: Sourcing {params.num_videos_to_source_or_generate} visual assets for '{params.video_subject}'...")
            sourced_video_clips = self.video_editor.source_visual_assets(
                query=params.video_subject,
                video_source_type=params.video_source_type,
                num_assets=params.num_videos_to_source_or_generate,
                max_clip_duration_s=params.max_clip_duration_s,
                target_aspect_ratio=params.video_aspect_ratio,
                image_prompt_suffix=params.image_prompt_suffix
            )
            if not sourced_video_clips:
                logger.error("No suitable video clips could be sourced/generated. Aborting.")
                return False
            logger.info(f"Successfully sourced/generated {len(sourced_video_clips)} visual assets.")

            # Step 5: Assemble base video from clips
            logger.info("Step 5/9: Concatenating video clips with transitions...")
            final_base_video_path = self.video_editor.assemble_base_video(
                video_clip_paths=sourced_video_clips,
                final_video_duration_s=params.final_video_duration_s,
                target_aspect_ratio=params.video_aspect_ratio,
                concat_mode=params.video_concat_mode,
                transition_mode=params.video_transition_mode,
                transition_duration=GLOBAL_CONFIG['video_settings'].get('default_transition_duration', 0.5)
            )
            if not final_base_video_path:
                logger.error("Failed to assemble base video. Aborting.")
                return False
            logger.info(f"Base video assembled at: {final_base_video_path}")

            # Step 6: Add narration and background music to video
            logger.info("Step 6/9: Adding narration and background music to the video...")
            video_with_audio_path = self.video_editor.add_narration_and_music(
                base_video_path=final_base_video_path,
                narration_audio_path=narration_result_path,
                background_music_query=GLOBAL_CONFIG['audio_settings']['default_background_music_query'],
                background_music_volume_db=GLOBAL_CONFIG['audio_settings']['default_background_music_volume'],
                final_video_duration_s=params.final_video_duration_s
            )
            if not video_with_audio_path:
                logger.error("Failed to add narration and music to video. Aborting.")
                return False
            logger.info(f"Narration and music added. Video with audio at: {video_with_audio_path}")

            # Step 7: Add subtitles (if enabled)
            final_video_path_with_subtitles = video_with_audio_path
            if params.enable_subtitles:
                logger.info("Step 7/9: Generating and adding subtitles to the video...")
                
                segment_duration = narration_duration / len(script_segments) if script_segments else 0
                subtitle_entries = []
                current_time = 0.0
                for segment_text in script_segments:
                    estimated_word_count = len(segment_text.split())
                    estimated_segment_duration = estimated_word_count * 0.35
                    
                    subtitle_entries.append(SubtitleEntry(
                        text=segment_text,
                        start_time=current_time,
                        end_time=current_time + estimated_segment_duration
                    ))
                    current_time += estimated_segment_duration

                font_path = find_font_path(params.subtitle_font.value)
                if not font_path:
                    logger.warning(f"Could not find font '{params.subtitle_font.value}'. Subtitles might use a default font.")
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

                if subtitle_entries and font_path:
                    final_video_path_with_subtitles = self.video_editor.add_subtitles(
                        video_path=video_with_audio_path,
                        subtitle_entries=subtitle_entries,
                        font_path=font_path,
                        font_size=params.subtitle_font_size,
                        font_color=params.subtitle_color,
                        outline_color=params.subtitle_outline_color,
                        outline_width=params.subtitle_outline_width,
                        position=params.subtitle_position
                    )
                    if not final_video_path_with_subtitles:
                        logger.error("Failed to add subtitles to video. Proceeding without subtitles.")
                        final_video_path_with_subtitles = video_with_audio_path
                    else:
                        logger.info(f"Subtitles added. Video with subtitles at: {final_video_path_with_subtitles}")
                else:
                    logger.warning("No subtitle entries or font path found. Skipping subtitle addition.")
            
            # Step 8: Finalize and copy to Google Drive
            logger.info("Step 8/9: Finalizing video and copying to Google Drive...")
            output_filename = f"final_video_{params.video_subject.replace(' ', '_')}_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
            google_drive_output_dir = os.path.join(PROJECT_ROOT_DIR_CURRENT, GLOBAL_CONFIG['paths']['output_dir'])
            
            final_output_path = self.video_editor.finalize_video(
                input_video_path=final_video_path_with_subtitles,
                output_filename=output_filename,
                google_drive_output_dir=google_drive_output_dir
            )
            if not final_output_path:
                logger.error("Failed to finalize video and copy to Google Drive.")
                return False
            logger.info(f"Video generation complete! Final video saved to: {final_output_path}")

            logger.info("Step 9/9: Cleaning up temporary runtime files (DISABLED for debugging).")
            return True

        except Exception as e:
            logger.critical(f"An unhandled error occurred during the pipeline execution: {e}", exc_info=True)
            logger.error("Video generation failed! Please check logs above for details.")
            return False
        finally:
            # Ensure logs are copied to Drive before cleanup
            try:
                file_handler_found = None
                for handler in logging.getLogger().handlers:
                    if isinstance(handler, logging.FileHandler) and RUNTIME_BASE_DIR in handler.baseFilename:
                        file_handler_found = handler
                        break

                if file_handler_found:
                    file_handler_found.flush()
                    file_handler_found.close()

                    log_filename = os.path.basename(file_handler_found.baseFilename)
                    gdrive_log_path = os.path.join(PROJECT_ROOT_DIR_CURRENT, GLOBAL_CONFIG['paths']['logs_dir'], log_filename)
                    os.makedirs(os.path.dirname(gdrive_log_path), exist_ok=True)
                    shutil.copy(file_handler_found.baseFilename, gdrive_log_path)
                    logger.info(f"Pipeline log copied to Google Drive: {gdrive_log_path}")
                else:
                    logger.warning("Could not find active file handler for runtime logs to copy to Google Drive.")

            except Exception as e:
                logger.error(f"Failed to copy pipeline log to Google Drive during cleanup: {e}", exc_info=True)

            # cleanup_runtime_files() # COMMENTED OUT to disable cleanup for debugging
            logger.info("Temporary files cleanup is DISABLED.")
