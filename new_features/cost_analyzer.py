import logging
from typing import Dict, Any, List, Optional
import math

logger = logging.getLogger(__name__)

class CostAnalyzer:
    """
    Analyzes projected usage of the Einstein Coder pipeline and estimates monthly costs
    based on current API pricing.
    """

    # --- EXAMPLE API PRICING DATA (as of early 2025 - SUBJECT TO CHANGE) ---
    # Always check official provider documentation for the latest pricing.
    # Prices are typically per 1,000 (K), 1 Million (M) characters/tokens, or per image/minute.
    API_PRICING = {
        "google_gemini": {
            "text_input_char_cost_per_m": 0.50,  # $0.0005 per 1K chars, so $0.50 per 1M chars (Gemini 1.5 Pro)
            "text_output_char_cost_per_m": 1.50, # $0.0015 per 1K chars, so $1.50 per 1M chars (Gemini 1.5 Pro)
            # Multimodal (Video analysis) is complex, often per frame or per second processed.
            # Example: $0.0001 per second analyzed for video input.
            "video_analysis_cost_per_s": 0.0001, # Example: $0.01 per minute, so $0.0001 per second
        },
        "google_tts": {
            "wavenet_char_cost_per_m": 16.00, # $16.00 per 1M characters
            "standard_char_cost_per_m": 4.00, # $4.00 per 1M characters
        },
        "openai_dalle": {
            "dalle3_1024x1024_cost_per_image": 0.04, # DALL-E 3 Standard 1024x1024
            "dalle3_1024x1792_cost_per_image": 0.08, # DALL-E 3 Standard 1024x1792 (portrait)
            "dalle3_1792x1024_cost_per_image": 0.08, # DALL-E 3 Standard 1792x1024 (landscape)
            "dalle2_1024x1024_cost_per_image": 0.02, # DALL-E 2 1024x1024
        },
        "pixabay_pexels": {
            "api_cost": 0.0, # APIs generally free for typical usage, check enterprise tiers if very high volume
            "downloads_cost": 0.0, # Royalty-free, no direct cost per download
        },
        "azure_tts": { # Example pricing, often similar to Google
            "neural_char_cost_per_m": 16.00,
            "standard_char_cost_per_m": 4.00,
        },
        "gcp_storage": {
            "storage_cost_per_gb_month": 0.026, # Example: $0.026 per GB/month for standard storage
            "egress_cost_per_gb": 0.12, # Example: $0.12 per GB (internet egress)
            "ops_cost_per_10k_ops": 0.004, # Example: Class A Ops $0.004 per 10k ops
        },
        "colab_compute": {
            "estimated_session_cost_per_hr": 0.50, # Rough estimate for Colab Pro compute usage
        }
    }

    def __init__(self):
        logger.info("Cost Analyzer initialized. Using example API pricing (check official docs for latest).")

    def project_monthly_costs(self, usage_scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Projects the monthly cost of maintaining the Einstein Coder project
        based on a given usage scenario.

        Args:
            usage_scenario: A dictionary defining projected monthly usage, e.g.:
                {
                    "num_videos_per_month": 30,
                    "avg_video_duration_s": 60, # seconds
                    "avg_script_char_per_video": 1000, # characters
                    "avg_response_char_per_video": 1500, # characters from Gemini
                    "video_source_type": "AI_GENERATED_IMAGES", # or "STOCK_FOOTAGE", "AI_GENERATED_VIDEOS"
                    "avg_images_per_video": 5, # if AI_GENERATED_IMAGES
                    "avg_image_resolution": "1024x1792", # if AI_GENERATED_IMAGES, matches DALL-E pricing keys
                    "avg_ttv_clips_per_video": 3, # if AI_GENERATED_VIDEOS
                    "avg_ttv_clip_duration_s": 10, # if AI_GENERATED_VIDEOS
                    "narration_voice_type": "WAVENET", # "WAVENET" or "STANDARD" (for Google/Azure)
                    "enable_video_analysis": False, # if Gemini video analysis is used
                    "avg_video_analysis_s_per_video": 0, # seconds of video analyzed by Gemini
                    "avg_final_video_size_mb": 20, # MB per final video stored/uploaded
                    "avg_temp_data_processing_gb": 5, # GB of temporary data processed by FFmpeg locally
                    "avg_colab_usage_hr_per_month": 40, # hours of Colab runtime
                }

        Returns:
            A dictionary detailing the projected costs per service and total monthly cost.
        """
        logger.info("Starting monthly cost projection...")

        num_videos = usage_scenario.get("num_videos_per_month", 0)
        avg_video_duration_s = usage_scenario.get("avg_video_duration_s", 60)
        avg_script_char_per_video = usage_scenario.get("avg_script_char_per_video", 1000)
        avg_response_char_per_video = usage_scenario.get("avg_response_char_per_video", 1500)
        video_source_type = usage_scenario.get("video_source_type", "STOCK_FOOTAGE")
        avg_images_per_video = usage_scenario.get("avg_images_per_video", 0)
        avg_image_resolution = usage_scenario.get("avg_image_resolution", "1024x1024")
        avg_ttv_clips_per_video = usage_scenario.get("avg_ttv_clips_per_video", 0)
        avg_ttv_clip_duration_s = usage_scenario.get("avg_ttv_clip_duration_s", 0)
        narration_voice_type = usage_scenario.get("narration_voice_type", "WAVENET").upper()
        enable_video_analysis = usage_scenario.get("enable_video_analysis", False)
        avg_video_analysis_s_per_video = usage_scenario.get("avg_video_analysis_s_per_video", 0)
        avg_final_video_size_mb = usage_scenario.get("avg_final_video_size_mb", 20)
        avg_temp_data_processing_gb = usage_scenario.get("avg_temp_data_processing_gb", 5)
        avg_colab_usage_hr_per_month = usage_scenario.get("avg_colab_usage_hr_per_month", 40)


        costs = {
            "google_gemini_text_gen": 0.0,
            "google_gemini_video_analysis": 0.0,
            "google_tts": 0.0,
            "openai_dalle": 0.0,
            "pixabay_pexels": 0.0,
            "gcp_storage": 0.0,
            "gcp_network_egress": 0.0,
            "gcp_operations": 0.0,
            "colab_compute": 0.0,
            "total_monthly_cost": 0.0
        }

        # 1. Google Gemini (Text Generation)
        total_input_chars = num_videos * avg_script_char_per_video
        total_output_chars = num_videos * avg_response_char_per_video
        
        costs["google_gemini_text_gen"] = (
            (total_input_chars / 1_000_000) * self.API_PRICING["google_gemini"]["text_input_char_cost_per_m"] +
            (total_output_chars / 1_000_000) * self.API_PRICING["google_gemini"]["text_output_char_cost_per_m"]
        )
        logger.debug(f"Gemini Text Gen Cost: ${costs['google_gemini_text_gen']:.2f}")

        # 2. Google Gemini (Video Analysis - if enabled)
        if enable_video_analysis:
            total_video_analysis_seconds = num_videos * avg_video_analysis_s_per_video
            costs["google_gemini_video_analysis"] = total_video_analysis_seconds * self.API_PRICING["google_gemini"]["video_analysis_cost_per_s"]
            logger.debug(f"Gemini Video Analysis Cost: ${costs['google_gemini_video_analysis']:.2f}")
        
        # 3. Google/Azure Text-to-Speech
        total_tts_chars = total_input_chars # Assuming script length is TTS input length
        if narration_voice_type == "WAVENET":
            costs["google_tts"] = (total_tts_chars / 1_000_000) * self.API_PRICING["google_tts"]["wavenet_char_cost_per_m"]
        else: # Default to standard if not Wavenet or explicit
            costs["google_tts"] = (total_tts_chars / 1_000_000) * self.API_PRICING["google_tts"]["standard_char_cost_per_m"]
        logger.debug(f"TTS Cost: ${costs['google_tts']:.2f}")

        # 4. OpenAI DALL-E (if AI_GENERATED_IMAGES)
        if video_source_type == "AI_GENERATED_IMAGES":
            total_images = num_videos * avg_images_per_video
            if avg_image_resolution == "1024x1024":
                costs["openai_dalle"] = total_images * self.API_PRICING["openai_dalle"]["dalle3_1024x1024_cost_per_image"]
            elif avg_image_resolution == "1024x1792":
                costs["openai_dalle"] = total_images * self.API_PRICING["openai_dalle"]["dalle3_1024x1792_cost_per_image"]
            elif avg_image_resolution == "1792x1024":
                costs["openai_dalle"] = total_images * self.API_PRICING["openai_dalle"]["dalle3_1792x1024_cost_per_image"]
            else:
                logger.warning(f"Unknown DALL-E resolution '{avg_image_resolution}'. Using default 1024x1024 for cost estimate.")
                costs["openai_dalle"] = total_images * self.API_PRICING["openai_dalle"]["dalle3_1024x1024_cost_per_image"]
            logger.debug(f"DALL-E Cost: ${costs['openai_dalle']:.2f}")
        
        # 5. Pixabay/Pexels (generally free)
        costs["pixabay_pexels"] = self.API_PRICING["pixabay_pexels"]["api_cost"] # Should remain 0 for typical use
        logger.debug(f"Pexels/Pixabay Cost: ${costs['pixabay_pexels']:.2f}")

        # 6. GCP Storage
        # This considers storage of final videos and temporary data processing.
        total_final_video_size_gb = (num_videos * avg_final_video_size_mb) / 1024 # MB to GB
        total_temp_data_gb = avg_temp_data_processing_gb # Direct input for overall temporary processing
        
        # Assume final videos are stored for the month, plus some temporary processing data
        total_storage_gb = total_final_video_size_gb + total_temp_data_gb
        costs["gcp_storage"] = total_storage_gb * self.API_PRICING["gcp_storage"]["storage_cost_per_gb_month"]

        # 7. GCP Network Egress (uploading final videos to GCS)
        costs["gcp_network_egress"] = total_final_video_size_gb * self.API_PRICING["gcp_storage"]["egress_cost_per_gb"]
        
        # 8. GCP Operations (uploads, reads, lists) - very rough estimate
        # Assuming ~100 ops per video (upload, check access, list blobs etc)
        total_ops = num_videos * 100
        costs["gcp_operations"] = (total_ops / 10_000) * self.API_PRICING["gcp_storage"]["ops_cost_per_10k_ops"]
        logger.debug(f"GCP Storage/Network/Ops Cost: ${costs['gcp_storage'] + costs['gcp_network_egress'] + costs['gcp_operations']:.2f}")

        # 9. Colab Compute
        costs["colab_compute"] = avg_colab_usage_hr_per_month * self.API_PRICING["colab_compute"]["estimated_session_cost_per_hr"]
        logger.debug(f"Colab Compute Cost: ${costs['colab_compute']:.2f}")

        # Sum total
        costs["total_monthly_cost"] = sum(v for k, v in costs.items() if k != "total_monthly_cost")

        logger.info("Monthly cost projection complete.")
        return costs

    def generate_cost_report(self, projected_costs: Dict[str, Any]) -> str:
        """
        Generates a human-readable report from the projected costs.
        """
        report = "\n--- Monthly Cost Projection Report ---\n"
        report += "--------------------------------------\n"
        for service, cost in projected_costs.items():
            if service != "total_monthly_cost":
                report += f"{service.replace('_', ' ').title().ljust(30)}: ${cost:.2f}\n"
        report += "--------------------------------------\n"
        report += f"Total Projected Monthly Cost     : ${projected_costs['total_monthly_cost']:.2f}\n"
        report += "--------------------------------------\n"
        report += "\nImportant Notes:\n"
        report += " - All prices are examples from early 2025 and are SUBJECT TO CHANGE by service providers.\n"
        report += " - Free tiers may apply for low usage, significantly reducing or eliminating costs.\n"
        report += " - Video analysis and Text-to-Video generation (if implemented) are significant cost drivers.\n"
        report += " - Colab Compute cost is an estimate for Colab Pro usage; free Colab has usage limits.\n"
        report += " - GCP storage and network egress costs depend heavily on actual data volume.\n"
        report += " - Actual costs may vary based on specific usage patterns, network conditions, and provider updates.\n"
        report += " - Consider optimizing script length, video duration, and image/video resolution to reduce costs.\n"
        return report
