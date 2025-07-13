import logging
import os
import random
import shutil
import uuid
import shlex
from typing import List, Optional, Tuple, Dict, Any

from moviepy.editor import VideoFileClip, concatenate_videoclips
from PIL import Image

from config import GLOBAL_CONFIG
from models import VideoSourceType, VideoAspect, VideoConcatMode, VideoTransitionMode, SubtitleEntry, ImagePrompt, SubtitlePosition
from utils.ffmpeg_utils import (
    concatenate_videos,
    add_audio_to_video,
    add_subtitles_to_video,
    get_video_dimensions,
    get_video_duration
)
from utils.video_utils import (
    search_pexels_videos,
    search_pixabay_videos,
    download_video_clip,
    inject_silent_audio_if_needed,
    find_font_path
)
from utils.audio_utils import (
    download_background_music,
    adjust_audio_volume,
    combine_audio_tracks,
    synthesize_speech_google # Ensure consistency, although pipeline directly calls
)
from utils.cleanup import (
    VIDEO_DOWNLOADS_DIR,
    AUDIO_DIR,
    IMAGES_DIR,
    OUTPUT_DIR,
    TEMP_FILES_DIR,
    LOGS_DIR,
    RUNTIME_BASE_DIR
)
from ai_integration.image_video_generation import generate_image_from_prompt # Correct function name

logger = logging.getLogger(__name__)

class VideoEditor:
    def __init__(self):
        self.base_dir = RUNTIME_BASE_DIR
        self.video_downloads_dir = os.path.join(self.base_dir, VIDEO_DOWNLOADS_DIR)
        self.audio_dir = os.path.join(self.base_dir, AUDIO_DIR)
        self.images_dir = os.path.join(self.base_dir, IMAGES_DIR)
        self.output_dir = os.path.join(self.base_dir, OUTPUT_DIR)
        self.temp_files_dir = os.path.join(self.base_dir, TEMP_FILES_DIR)
        self.logs_dir = os.path.join(self.base_dir, LOGS_DIR)
        logger.info(f"VideoEditor initialized. It will use local /tmp paths for processing.")
        
        self.setup_local_runtime_directories()

    def setup_local_runtime_directories(self):
        """Ensures all necessary local temporary directories exist."""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.video_downloads_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.temp_files_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def source_visual_assets(
        self,
        query: str,
        video_source_type: VideoSourceType,
        num_assets: int,
        max_clip_duration_s: int,
        target_aspect_ratio: VideoAspect,
        image_prompt_suffix: Optional[str] = None
    ) -> List[str]:
        """
        Sources video clips or generates images based on the specified type and query.
        Returns a list of paths to the downloaded/generated visual assets.
        """
        logger.info(f"Sourcing {num_assets} visual assets for '{query}' from {video_source_type.value}.")
        sourced_files = []
        
        orientation = "portrait" if target_aspect_ratio == VideoAspect.PORTRAIT_9_16 else "landscape"

        if video_source_type == VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY:
            # Pexels Search
            pexels_results = search_pexels_videos(query=query, orientation=orientation, per_page=num_assets * 2, max_duration_s=max_clip_duration_s)
            
            # Pixabay Search
            pixabay_results = search_pixabay_videos(query=query, orientation=orientation, per_page=num_assets * 2, max_duration_s=max_clip_duration_s)
            
            all_stock_videos = pexels_results + pixabay_results
            random.shuffle(all_stock_videos)

            for video_info in all_stock_videos:
                if len(sourced_files) >= num_assets:
                    break
                
                # Check aspect ratio for relevance
                is_portrait = video_info['height'] > video_info['width']
                is_landscape = video_info['width'] > video_info['height']
                is_square = video_info['width'] == video_info['height']

                if (target_aspect_ratio == VideoAspect.PORTRAIT_9_16 and is_portrait) or \
                   (target_aspect_ratio == VideoAspect.LANDSCAPE_16_9 and is_landscape) or \
                   (target_aspect_ratio == VideoAspect.SQUARE_1_1 and is_square):
                    
                    downloaded_path = download_video_clip(video_info['download_link'], self.video_downloads_dir)
                    if downloaded_path:
                        final_clip_path = os.path.join(self.temp_files_dir, f"clip_with_audio_{uuid.uuid4().hex}.mp4")
                        clip_duration = get_video_duration(downloaded_path)
                        if clip_duration is None:
                            logger.warning(f"Could not get duration for downloaded clip {downloaded_path}. Skipping.")
                            os.remove(downloaded_path)
                            continue

                        processed_clip_path = inject_silent_audio_if_needed(downloaded_path, final_clip_path, clip_duration)
                        if processed_clip_path:
                            sourced_files.append(processed_clip_path)
                            os.remove(downloaded_path)
                        else:
                            logger.warning(f"Failed to ensure audio for clip: {downloaded_path}. Skipping.")
                            os.remove(downloaded_path)
                else:
                    logger.debug(f"Skipping video due to aspect ratio mismatch: {video_info['width']}x{video_info['height']} for target {target_aspect_ratio.value}")
        
        elif video_source_type == VideoSourceType.STOCK_FOOTAGE_PEXELS_ONLY:
             # Similar logic but only call search_pexels_videos
             pexels_results = search_pexels_videos(query=query, orientation=orientation, per_page=num_assets * 2, max_duration_s=max_clip_duration_s)
             random.shuffle(pexels_results)
             for video_info in pexels_results:
                if len(sourced_files) >= num_assets: break
                is_portrait = video_info['height'] > video_info['width']
                is_landscape = video_info['width'] > video_info['height']
                is_square = video_info['width'] == video_info['height']
                if (target_aspect_ratio == VideoAspect.PORTRAIT_9_16 and is_portrait) or \
                   (target_aspect_ratio == VideoAspect.LANDSCAPE_16_9 and is_landscape) or \
                   (target_aspect_ratio == VideoAspect.SQUARE_1_1 and is_square):
                    downloaded_path = download_video_clip(video_info['download_link'], self.video_downloads_dir)
                    if downloaded_path:
                        final_clip_path = os.path.join(self.temp_files_dir, f"clip_with_audio_{uuid.uuid4().hex}.mp4")
                        clip_duration = get_video_duration(downloaded_path)
                        if clip_duration is None: logger.warning(f"Could not get duration for downloaded clip {downloaded_path}. Skipping."); os.remove(downloaded_path); continue
                        processed_clip_path = inject_silent_audio_if_needed(downloaded_path, final_clip_path, clip_duration)
                        if processed_clip_path: sourced_files.append(processed_clip_path); os.remove(downloaded_path)
                        else: logger.warning(f"Failed to ensure audio for clip: {downloaded_path}. Skipping."); os.remove(downloaded_path)
        
        elif video_source_type == VideoSourceType.STOCK_FOOTAGE_PIXABAY_ONLY:
            # Similar logic but only call search_pixabay_videos
            pixabay_results = search_pixabay_videos(query=query, orientation=orientation, per_page=num_assets * 2, max_duration_s=max_clip_duration_s)
            random.shuffle(pixabay_results)
            for video_info in pixabay_results:
                if len(sourced_files) >= num_assets: break
                is_portrait = video_info['height'] > video_info['width']
                is_landscape = video_info['width'] > video_info['height']
                is_square = video_info['width'] == video_info['height']
                if (target_aspect_ratio == VideoAspect.PORTRAIT_9_16 and is_portrait) or \
                   (target_aspect_ratio == VideoAspect.LANDSCAPE_16_9 and is_landscape) or \
                   (target_aspect_ratio == VideoAspect.SQUARE_1_1 and is_square):
                    downloaded_path = download_video_clip(video_info['download_link'], self.video_downloads_dir)
                    if downloaded_path:
                        final_clip_path = os.path.join(self.temp_files_dir, f"clip_with_audio_{uuid.uuid4().hex}.mp4")
                        clip_duration = get_video_duration(downloaded_path)
                        if clip_duration is None: logger.warning(f"Could not get duration for downloaded clip {downloaded_path}. Skipping."); os.remove(downloaded_path); continue
                        processed_clip_path = inject_silent_audio_if_needed(downloaded_path, final_clip_path, clip_duration)
                        if processed_clip_path: sourced_files.append(processed_clip_path); os.remove(downloaded_path)
                        else: logger.warning(f"Failed to ensure audio for clip: {downloaded_path}. Skipping."); os.remove(downloaded_path)

        elif video_source_type == VideoSourceType.AI_GENERATED_IMAGES:
            logger.info(f"Attempting to generate {num_assets} images using AI for prompt: '{query}' with suffix '{image_prompt_suffix}'.")
            for i in range(num_assets):
                if len(sourced_files) >= num_assets:
                    break
                full_image_prompt = f"{query} {image_prompt_suffix if image_prompt_suffix else ''}"
                generated_image_path = generate_image_from_prompt( # This is the function in image_video_generation.py
                    text_prompt=full_image_prompt,
                    output_dir=self.images_dir
                )
                if generated_image_path:
                    # Convert image to a short video clip (e.g., 5 seconds long or max_clip_duration_s)
                    video_from_image_path = os.path.join(self.temp_files_dir, f"ai_image_video_{uuid.uuid4().hex}.mp4")
                    clip_duration_for_image = min(max_clip_duration_s, 5) # Default 5s, max to user setting
                    converted_video_path = moviepy.editor.ImageClip(generated_image_path, duration=clip_duration_for_image).write_videofile(
                        video_from_image_path, fps=25, verbose=False, logger=None
                    )
                    # Ensure audio for the converted video (images don't have audio)
                    final_clip_path_with_audio = os.path.join(self.temp_files_dir, f"ai_image_video_audio_{uuid.uuid4().hex}.mp4")
                    processed_clip_path = inject_silent_audio_if_needed(converted_video_path, final_clip_path_with_audio, clip_duration_for_image)
                    if processed_clip_path:
                        sourced_files.append(processed_clip_path)
                        os.remove(generated_image_path) # Clean up original image
                        os.remove(converted_video_path) # Clean up intermediate video
                    else:
                        logger.warning(f"Failed to ensure audio for AI image video: {converted_video_path}. Skipping.")
                        if os.path.exists(converted_video_path): os.remove(converted_video_path)
                        if os.path.exists(generated_image_path): os.remove(generated_image_path)
                else:
                    logger.warning(f"Failed to generate image for prompt: '{full_image_prompt}'. Skipping.")
        
        elif video_source_type == VideoSourceType.AI_GENERATED_VIDEOS:
            logger.warning("AI-generated videos not yet implemented for direct sourcing.")
            return [] # Currently not implemented

        if not sourced_files:
            logger.error("No suitable video clips could be sourced/generated.")
            return []
        
        # Ensure all sourced files are actually mp4s and are pre-processed to target aspect ratio and have audio
        final_processed_clips = []
        for clip_path in sourced_files:
            duration = get_video_duration(clip_path)
            if duration is None:
                logger.warning(f"Could not get duration for sourced clip {clip_path}. Skipping.")
                continue

            if duration > max_clip_duration_s:
                trimmed_clip_path = os.path.join(self.temp_files_dir, f"trimmed_clip_{uuid.uuid4().hex}.mp4")
                logger.info(f"Trimming clip {os.path.basename(clip_path)} from {duration:.2f}s to {max_clip_duration_s}s.")
                cmd_trim = [
                    'ffmpeg', '-y', '-i', shlex.quote(clip_path), '-ss', '0', '-t', str(max_clip_duration_s),
                    '-c', 'copy', shlex.quote(trimmed_clip_path)
                ]
                stdout, stderr, returncode = run_shell_command(cmd_trim, check_error=True, timeout=60)
                if returncode == 0:
                    clip_path = trimmed_clip_path
                    duration = get_video_duration(clip_path)
                    logger.info(f"Clip trimmed to {duration:.2f}s.")
                else:
                    logger.error(f"Failed to trim clip {clip_path}: {stderr}. Using original clip.")
            
            final_processed_clips.append(clip_path)

        if not final_processed_clips:
            logger.error("No valid clips remained after processing and trimming.")
            return []

        return final_processed_clips

    def assemble_base_video(
        self,
        video_clip_paths: List[str],
        final_video_duration_s: int,
        target_aspect_ratio: VideoAspect,
        concat_mode: VideoConcatMode,
        transition_mode: VideoTransitionMode,
        transition_duration: float
    ) -> Optional[str]:
        """
        Assembles a base video from individual clips, applying concatenation and transitions.
        """
        if not video_clip_paths:
            logger.error("No video clips provided to assemble_base_video.")
            return None

        target_width, target_height = 1080, 1920
        if target_aspect_ratio == VideoAspect.LANDSCAPE_16_9:
            target_width, target_height = 1920, 1080
        elif target_aspect_ratio == VideoAspect.SQUARE_1_1:
            target_width, target_height = 1080, 1080

        logger.info(f"Assembling base video from {len(video_clip_paths)} clips. Target resolution: {target_width}x{target_height}.")

        if concat_mode == VideoConcatMode.RANDOM_CONCATENATION:
            random.shuffle(video_clip_paths)
            logger.info("Randomizing clip order for concatenation.")

        output_filepath = os.path.join(self.temp_files_dir, f"base_video_{uuid.uuid4().hex}.mp4")

        success = concatenate_videos(
            video_paths=video_clip_paths,
            output_path=output_filepath,
            target_width=target_width,
            target_height=target_height,
            target_duration=float(final_video_duration_s),
            transition=transition_mode.value, # Pass the string value
            transition_duration=transition_duration
        )

        if not success:
            logger.error("Failed to concatenate videos.")
            return None
        
        actual_duration = get_video_duration(output_filepath)
        if actual_duration is None:
            logger.warning("Could not get duration of assembled base video. Cannot verify target duration.")
            return output_filepath
            
        if abs(actual_duration - final_video_duration_s) > 1.0:
            logger.warning(f"Assembled base video duration ({actual_duration:.2f}s) differs from target ({final_video_duration_s}s) by more than 1s. Re-trimming for exactness.")
            trimmed_output_filepath = os.path.join(self.temp_files_dir, f"base_video_trimmed_{uuid.uuid4().hex}.mp4")
            cmd_trim = [
                'ffmpeg', '-y', '-i', shlex.quote(output_filepath), '-ss', '0', '-t', str(final_video_duration_s),
                '-c', 'copy', shlex.quote(trimmed_output_filepath)
            ]
            stdout, stderr, returncode = run_shell_command(cmd_trim, check_error=True, timeout=60)
            if returncode == 0:
                os.remove(output_filepath)
                output_filepath = trimmed_output_filepath
                logger.info(f"Assembled base video trimmed to exact duration: {final_video_duration_s}s.")
            else:
                logger.error(f"Failed to re-trim assembled base video: {stderr}. Using potentially inaccurate video.")

        return output_filepath

    def add_narration_and_music(
        self,
        base_video_path: str,
        narration_audio_path: str,
        background_music_query: str,
        background_music_volume_db: int,
        final_video_duration_s: int
    ) -> Optional[str]:
        """
        Adds narration and background music to the video.
        """
        if not os.path.exists(base_video_path):
            logger.error(f"Base video not found: {base_video_path}")
            return None
        if not os.path.exists(narration_audio_path):
            logger.error(f"Narration audio not found: {narration_audio_path}")
            return None

        bg_music_path = download_background_music(background_music_query, self.audio_dir, final_video_duration_s)

        combined_audio_path = os.path.join(self.audio_dir, f"combined_audio_{uuid.uuid4().hex}.mp3")
        audio_combined_success = combine_audio_tracks(
            narration_path=narration_audio_path,
            background_music_path=bg_music_path,
            output_path=combined_audio_path,
            background_music_volume_db=background_music_volume_db
        )
        if not audio_combined_success:
            logger.error("Failed to combine narration and background music.")
            return None

        video_with_audio_path = os.path.join(self.temp_files_dir, f"video_with_audio_{uuid.uuid4().hex}.mp4")
        video_audio_added_success = add_audio_to_video(base_video_path, combined_audio_path, video_with_audio_path)
        if not video_audio_added_success:
            logger.error("Failed to add combined audio to video.")
            return None

        if os.path.exists(combined_audio_path):
            os.remove(combined_audio_path)
        if bg_music_path and os.path.exists(bg_music_path):
            os.remove(bg_music_path)

        return video_with_audio_path

    def add_subtitles(
        self,
        video_path: str,
        subtitle_entries: List[SubtitleEntry],
        font_path: str,
        font_size: int,
        font_color: str,
        outline_color: str,
        outline_width: int,
        position: SubtitlePosition
    ) -> Optional[str]:
        """
        Generates an ASS subtitle file and burns it into the video.
        """
        logger.info(f"Generating ASS subtitle file for {video_path}...")
        subtitle_file_path = os.path.join(self.temp_files_dir, f"subtitles_{uuid.uuid4().hex}.ass")

        def hex_to_ass_color(hex_color: str) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f"&H{b:02X}{g:02X}{r:02X}"

        ass_font_color = hex_to_ass_color(font_color)
        ass_outline_color = hex_to_ass_color(outline_color)

        # Retrieve aspect ratio dimensions from GLOBAL_CONFIG for PlayResX/Y
        default_aspect_ratio_str = GLOBAL_CONFIG['video_settings']['default_aspect_ratio'].split(' ')[1] # e.g., "9:16"
        res_x, res_y = map(int, default_aspect_ratio_str.split(':'))
        
        ass_content = f"""
[Script Info]
ScriptType: v4.00+
ScaledBorderAndShadow: yes
Collisions: Normal
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{os.path.basename(font_path)},{font_size},{ass_font_color},&H000000FF,{ass_outline_color},&H00000000,0,0,0,0,100,100,0,0,1,{outline_width},0,{position.to_ass_alignment()},10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        for entry in subtitle_entries:
            start_h = int(entry.start_time // 3600)
            start_m = int((entry.start_time % 3600) // 60)
            start_s = entry.start_time % 60
            
            end_h = int(entry.end_time // 3600)
            end_m = int((entry.end_time % 3600) // 60)
            end_s = entry.end_time % 60
            
            start_time_str = f"{start_h}:{start_m:02}:{start_s:05.2f}"
            end_time_str = f"{end_h}:{end_m:02}:{end_s:05.2f}"
            
            escaped_text = entry.text.replace(",", "\\N")
            
            ass_content += f"Dialogue: 0,{start_time_str},{end_time_str},Default,,0,0,0,,{escaped_text}\n"

        with open(subtitle_file_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        
        logger.info(f"ASS subtitle file generated at: {subtitle_file_path}")

        output_video_with_subtitles_path = os.path.join(self.temp_files_dir, f"video_with_subtitles_{uuid.uuid4().hex}.mp4")
        
        success = add_subtitles_to_video(
            video_path=video_path,
            subtitle_file_path=subtitle_file_path,
            output_path=output_video_with_subtitles_path,
            font_path=font_path,
            font_size=font_size,
            font_color=font_color,
            outline_color=outline_color,
            outline_width=outline_width,
            position=position.value
        )

        if os.path.exists(subtitle_file_path):
            os.remove(subtitle_file_path)

        if not success:
            logger.error("Failed to add subtitles to video.")
            return None
        
        return output_video_with_subtitles_path

    def finalize_video(self, input_video_path: str, output_filename: str, google_drive_output_dir: str) -> Optional[str]:
        """
        Copies the final processed video from temporary storage to Google Drive.
        """
        if not os.path.exists(input_video_path):
            logger.error(f"Input video for finalization not found: {input_video_path}")
            return None
        
        os.makedirs(google_drive_output_dir, exist_ok=True)
        final_output_path = os.path.join(google_drive_output_dir, output_filename)
        
        try:
            shutil.copy(input_video_path, final_output_path)
            logger.info(f"Final video copied to Google Drive: {final_output_path}")
            return final_output_path
        except Exception as e:
            logger.error(f"Failed to copy final video to Google Drive: {e}", exc_info=True)
            return None
