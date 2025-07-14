import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, Union

logger = logging.getLogger(__name__)

class CostAnalyzer:
    """
    A class to track API usage and estimate costs for various AI services.
    Prices are illustrative and should be updated with actual API pricing.
    """
    def __init__(self):
        self.usage_metrics = defaultdict(lambda: defaultdict(float)) # {'service': {'unit': total_units}}
        self.cost_metrics = defaultdict(float) # {'service': total_cost}

        # Illustrative costs per unit (e.g., per 1000 characters for TTS, per image for Image Gen)
        self.cost_rates = {
            'gemini_text_char_k': 0.0001, # per 1k characters, very cheap
            'gemini_vision_sec': 0.002,   # per second of video analyzed
            'google_tts_char_k': 0.004,   # per 1k characters
            'azure_tts_char_k': 0.003,    # per 1k characters
            'gtts_requests': 0.0,         # gTTS is free (unofficial API)
            'pexels_video_search_requests': 0.001, # per search
            'pixabay_video_search_requests': 0.001, # per search
            'ai_image_gen_image': 0.02,   # per image generated (e.g., Imagen, Stable Diffusion)
            'ai_video_gen_sec': 0.05      # per second of AI video generated (e.g., TTV APIs)
        }

    def record_usage(self, service: str, unit: str, value: Union[int, float]):
        """Records usage for a specific service and unit."""
        self.usage_metrics[service][unit] += value
        logger.debug(f"Recorded usage: {service}, {unit}, {value}. Total: {self.usage_metrics[service][unit]}")
        self._recalculate_cost(service)

    def _recalculate_cost(self, service: str):
        """Recalculates the cost for a specific service based on current usage."""
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
        # Add more services as needed

        self.cost_metrics[service] = total_service_cost

    def get_total_cost(self) -> float:
        """Returns the total estimated cost across all tracked services."""
        return sum(self.cost_metrics.values())

    def get_detailed_report(self) -> Dict[str, Any]:
        """Returns a detailed report of usage and costs."""
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
        """Resets all usage and cost metrics."""
        self.usage_metrics = defaultdict(lambda: defaultdict(float))
        self.cost_metrics = defaultdict(float)
        logger.info("CostAnalyzer metrics reset.")

# Global instance of CostAnalyzer for easy access across modules (optional, but convenient)
cost_analyzer = CostAnalyzer()

if __name__ == "__main__":
    # Example Usage
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    analyzer = CostAnalyzer()

    # Simulate some usage
    analyzer.record_usage('gemini_text', 'characters', 5000)
    analyzer.record_usage('google_tts', 'characters', 3000)
    analyzer.record_usage('ai_image_gen', 'images', 5)
    analyzer.record_usage('gemini_vision', 'seconds', 120)

    report = analyzer.get_detailed_report()
    import json
    print(json.dumps(report, indent=2))

    print(f"\nTotal estimated cost: ${analyzer.get_total_cost():.4f}")

    analyzer.reset()
    print(f"\nTotal estimated cost after reset: ${analyzer.get_total_cost():.4f}")
