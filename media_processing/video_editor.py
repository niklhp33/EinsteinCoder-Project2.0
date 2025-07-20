# media_processing/video_editor.py (FIXED: Enhanced Logging for write_videofile)
import os
import logging
import random
import shlex
import shutil
import time
from typing import List, Optional, Tuple, Any

# Import MoviePy components
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, TextClip, CompositeVideoClip, ColorClip, CompositeAudioClip
from moviepy.video.fx import all as vfx # To make sure resize is accessible via vfx.resize

from utils.ffmpeg_utils import add_audio_to_video, add_subtitles_to_video, escape_ffmpeg_text
from utils.video_utils import get_video_duration, search_pexels_videos, search_pixabay_videos, download_video_clip, get_video_resolution
from ai_integration.image_video_generation import generate_image_with_imagen, generate_video_with_ttv_api, combine_ai_visuals_with_stock_footage
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
    """
    Generates an ASS (Advanced SubStation Alpha) subtitle file from a list of subtitle entries.
    Includes styling information for FFmpeg to burn in.
    """
    logger.info(f"Generating ASS subtitle file: {output_filepath}")

    ass_content = f"""[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font.value},{font_size},{color},{color},{outline_color},{outline_color},0,0,0,0,100,100,0,0,1,{outline_width},0,{position.to_ffmpeg_ass_position()},0,0,0,1
"""
    for entry in subtitle_entries:
        start_time = time.strftime('%H:%M:%S', time.gmtime(entry.start_time_s)) + f".{int((entry.start_time_s % 1) * 100):02d}"
        end_time = time.strftime('%H:%M:%S', time.gmtime(entry.end_time_s)) + f".{int((entry.end_time_s % 1) * 100):02d}"
        safe_text = escape_ffmpeg_text(entry.text)
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{safe_text}\n"

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        logger.info(f"Subtitle file created successfully: {output_filepath}")
        return output_filepath
    except Exception as e:
        logger.error(f"Failed to write subtitle file: {e}", exc_info=True)
        return None

def download_source_clips(video_params: Any, video_downloads_dir: str, max_clip_duration_s: int) -> List[str]:
    """
    Downloads video clips based on the selected source type.
    """
    downloaded_clip_paths = []
    
    target_width = 1080
    target_height = 1920

    if video_params.video_aspect_ratio == VideoAspect.PORTRAIT_9_16:
        target_width, target_height = 1080, 1920
    elif video_params.video_aspect_ratio == VideoAspect.LANDSCAPE_16_9:
        target_width, target_height = 1920, 1080
    elif video_params.video_aspect_ratio == VideoAspect.SQUARE_1_1:
        target_width, target_height = 1080, 1080
    else:
        logger.error(f"Unsupported video aspect ratio: {video_aspect_ratio}. Defaulting to 9:16.")
        target_width, target_height = 1080, 1920

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
                if v_file.get('quality') in ['hd', 'sd'] and \
                   ((video_params.video_aspect_ratio == VideoAspect.PORTRAIT_9_16 and v_file.get('height',0) > v_file.get('width',0)) or \
                    (video_params.video_aspect_ratio == VideoAspect.LANDSCAPE_16_9 and v_file.get('width',0) > v_file.get('height',0)) or \
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
                
                try:
                    clip = ImageClip(image_path, fps=24).set_duration(max_clip_duration_s) 
                    clip = clip.resize(newsize=(target_width, target_height))
                    clip.write_videofile(image_video_path, codec="libx264", fps=24, preset="fast", audio_codec=None)
                    downloaded_clip_paths.append(image_video_path)
                except Exception as e:
                    logger.error(f"Failed to convert AI image {image_path} to video using MoviePy: {e}", exc_info=True)

    if video_params.video_source_type == VideoSourceType.AI_GENERATED_VIDEOS:
        logger.info(f"Generating AI videos for topic: {video_params.video_subject}")
        for i in range(video_params.num_videos_to_source_or_generate):
            prompt = video_params.video_subject
            video_path = generate_video_with_ttv_api(
                script_segment=prompt,
                duration_seconds=max_clip_duration_s,
                video_style="cinematic"
            )
            if video_path:
                downloaded_clip_paths.append(video_path)

    if downloaded_clip_paths and video_params.video_source_type == VideoSourceType.STOCK_FOOTAGE_PEXELS_PIXABAY:
        pass

    logger.info(f"Finished sourcing/generating clips. Total clips: {len(downloaded_clip_paths)}")
    return downloaded_clip_paths

# --- New helper function for crossfading clips ---
def _crossfade_clips(clip1, clip2, duration):
    """
    Applies a crossfade between two MoviePy video clips.
    """
    if clip1 is None or clip2 is None:
        logger.error("Cannot crossfade None clips.")
        return None
    
    # Ensure clips are the same size before composing
    if clip1.size != clip2.size:
        logger.warning(f"Clip sizes differ: {clip1.size} vs {clip2.size}. Resizing clip2 to match clip1.")
        clip2 = clip2.resize(newsize=clip1.size) 
        
    # Ensure durations are sufficient for crossfade
    actual_crossfade_duration = min(clip1.duration, clip2.duration, duration)
    if actual_crossfade_duration <= 0:
        logger.warning(f"Effective crossfade duration is zero or negative ({actual_crossfade_duration:.2f}s). Skipping crossfade.")
        return clip1 # Just return the first clip if crossfade is impossible

    # Set up fade in/out on the clips
    # Trim clip1 so its end aligns with the crossfade start
    clip1_part = clip1.subclip(0, clip1.duration - actual_crossfade_duration)
    
    # Apply fadeout to the last part of clip1
    clip1_faded_out = clip1_part.fadeout(duration=actual_crossfade_duration) 

    # Apply fadein to the beginning of clip2
    clip2_faded_in = clip2.fadein(duration=actual_crossfade_duration) 
    
    # Composite the faded clips. clip2_faded_in starts at the point where clip1_faded_out begins
    final_clip = CompositeVideoClip([clip1_faded_out, clip2_faded_in.set_start(clip1_part.duration)])

    # If audio is present, combine audio
    if clip1.audio and clip2.audio:
        final_clip = final_clip.set_audio(CompositeAudioClip([clip1.audio.subclip(0, clip1.duration - actual_crossfade_duration), clip2.audio.set_start(clip1.duration - actual_crossfade_duration)]))

    return final_clip


def combine_and_edit_clips(
    video_paths: List[str],
    final_video_duration_s: int,
    video_concat_mode: VideoConcatMode,
    video_transition_mode: VideoTransitionMode,
    video_aspect_ratio: VideoAspect,
    temp_files_dir: str,
    output_base_name: str
) -> Optional[str]:
    """
    Manages the concatenation and basic editing of video clips using MoviePy for transitions.
    """
    logger.info(f"Starting combine and edit clips process using MoviePy.")

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

    moviepy_clips = []
    for i, path in enumerate(video_paths):
        try:
            clip = VideoFileClip(path)
            clip = clip.resize(newsize=(target_width, target_height))
            moviepy_clips.append(clip)
        except Exception as e:
            logger.error(f"Failed to load or process clip {path} with MoviePy: {e}", exc_info=True)
            continue

    if not moviepy_clips:
        logger.error("No valid video clips loaded for MoviePy concatenation.")
        return None

    final_clip = None
    transition_duration = GLOBAL_CONFIG['video_settings']['default_transition_duration']

    if video_transition_mode == VideoTransitionMode.NONE:
        final_clip = concatenate_videoclips(moviepy_clips, method="compose")
        logger.info("Concatenating videos with no transitions (MoviePy).")
    elif video_transition_mode in [VideoTransitionMode.FADE, VideoTransitionMode.CROSSFADE]:
        logger.info(f"Concatenating videos with {video_transition_mode.value} transition (MoviePy). Duration: {transition_duration}s")
        
        if len(moviepy_clips) < 2:
            logger.warning("Only one clip available, cannot apply transition. Using clip as is.")
            final_clip = moviepy_clips[0]
        else:
            composed_clip = moviepy_clips[0]
            for i in range(1, len(moviepy_clips)):
                next_clip = moviepy_clips[i]
                
                if composed_clip.audio is None or next_clip.audio is None:
                    logger.warning(f"Audio missing in one or both clips for crossfade. Proceeding without audio crossfade for this segment.")
                
                crossfaded_segment = _crossfade_clips(composed_clip, next_clip, transition_duration)
                
                if crossfaded_segment is None:
                    logger.error(f"Failed to apply crossfade between clip {i-1} and {i}. Aborting with current composed clip.")
                    final_clip = composed_clip
                    break
                composed_clip = crossfaded_segment
            final_clip = composed_clip

    elif video_transition_mode == VideoTransitionMode.SLIDE:
        logger.info("MoviePy Slide transition is complex; using basic concatenation as fallback for now.")
        final_clip = concatenate_videoclips(moviepy_clips, method="compose")
    else:
        logger.warning(f"Unsupported MoviePy transition mode: {video_transition_mode.value}. Using no transition.")
        final_clip = concatenate_videoclips(moviepy_clips, method="compose")

    if not final_clip:
        logger.error("MoviePy concatenation failed: final_clip is None.")
        return None

    if final_clip.duration > final_video_duration_s:
        final_clip = final_clip.subclip(0, final_video_duration_s)
        logger.info(f"Trimmed final video to target duration: {final_video_duration_s}s")
    elif final_clip.duration < final_video_duration_s:
        num_loops = int(final_video_duration_s / final_clip.duration) + 1
        looped_clip = concatenate_videoclips([final_clip] * num_loops)
        final_clip = looped_clip.subclip(0, final_video_duration_s)
        logger.info(f"Looped video to meet target duration: {final_video_duration_s}s")
        
    final_concat_output = os.path.join(temp_files_dir, f"{output_base_name}_concatenated.mp4")

    try:
        final_clip.write_videofile(final_concat_output, codec="libx264", audio_codec="aac", fps=24, preset="fast", logger=None)
        logger.info(f"Videos concatenated successfully using MoviePy. Output: {final_concat_output}.")
        return final_concat_output
    except Exception as e:
        logger.error(f"MoviePy failed to write video file: {e}", exc_info=True)
        return None