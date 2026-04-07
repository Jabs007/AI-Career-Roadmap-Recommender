"""
Accessibility Framework Configuration
===================================
Comprehensive accessibility settings and preferences management for the
AI Career Roadmap Recommender System.

This module manages all accessibility-related configurations including:
- Visual preferences (font size, contrast, colors)
- Motor accessibility (keyboard navigation, timing)
- Cognitive preferences (simplified layouts, reduced motion)
- Assistive technology settings (screen reader modes)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, cast # type: ignore
from enum import Enum
import json
import os


class AccessibilityProfile(Enum):
    """Predefined accessibility profiles for quick setup"""
    DEFAULT = "default"
    VISUAL_IMPAIRMENT = "visual_impairment"
    MOTOR_DISABILITY = "motor_disability"
    COGNITIVE_DIFFICULTY = "cognitive_difficulty"
    NEURODIVERGENT = "neurodivergent"
    DEAF_HARD_HEARING = "deaf_hard_hearing"


@dataclass
class VisualSettings:
    """Visual accessibility settings"""
    font_size: str = "medium"  # small, medium, large, extra_large
    color_scheme: str = "default"  # default, high_contrast, dark_mode, light_mode
    text_zoom: int = 100  # percentage (50-200)
    line_spacing: str = "normal"  # compact, normal, relaxed
    letter_spacing: str = "normal"  # compact, normal, relaxed
    word_spacing: str = "normal"  # compact, normal, relaxed
    font_family: str = "default"  # default, dyslexic_friendly, monospace
    color_blind_mode: str = "none"  # none, protanopia, deuteranopia, tritanopia
    focus_indicator: str = "high"  # none, standard, high


@dataclass
class MotorSettings:
    """Motor/accessibility settings for users with mobility challenges"""
    keyboard_navigation: bool = True
    skip_links: bool = True
    tab_navigation_only: bool = False
    auto_submit_forms: bool = False
    click_hold_time: int = 500  # milliseconds
    double_click_interval: int = 500  # milliseconds
    drag_drop_enabled: bool = True
    scroll_acceleration: str = "normal"  # slow, normal, fast
    cursor_size: str = "normal"  # small, normal, large, extra_large
    sticky_keys_enabled: bool = False
    toggle_keys_enabled: bool = False


@dataclass
class CognitiveSettings:
    """Cognitive and neurodivergent accessibility settings"""
    simplified_navigation: bool = False
    reduced_motion: bool = False
    hide_animations: bool = False
    show_progress_steps: bool = True
    chunk_content: bool = False
    max_items_per_page: int = 5
    clear_all_button: bool = True
    confirmation_dialogs: bool = True
    simple_language_mode: bool = False
    icon_labels: bool = True  # Always show text labels with icons
    breadcrumbs: bool = True
    reading_level: str = "standard"  # simplified, standard, detailed
    break_into_steps: bool = True
    show_summaries: bool = True
    auto_save_drafts: bool = True
    undo_functionality: bool = True


@dataclass
class AudioSettings:
    """Audio and hearing-related settings"""
    screen_reader_enabled: bool = False
    screen_reader_voice: str = "default"
    screen_reader_speed: int = 1  # 0.5 - 2.0
    announcements_enabled: bool = True
    sound_feedback: bool = True
    captcha_alternative: bool = False
    visual_notifications: bool = True
    transcript_available: bool = True


@dataclass
class DisabilityAccommodations:
    """Specific disability accommodation preferences"""
    disability_type: Optional[str] = None
    accommodation_needs: List[str] = field(default_factory=list)
    workplace_requirements: List[str] = field(default_factory=list)
    assistive_technology: List[str] = field(default_factory=list)
    preferred_work_arrangement: str = "any"  # remote, hybrid, onsite, any
    mobility_aid_required: bool = False
    communication_preferences: List[str] = field(default_factory=list)
    environmental_needs: List[str] = field(default_factory=list)
    technology_proficiency: str = "intermediate"  # beginner, intermediate, advanced
    job_search_assistance_level: str = "independent"  # independent, guided, intensive


@dataclass
class AccessibilityPreferences:
    """Complete accessibility preferences container"""
    profile: str = AccessibilityProfile.DEFAULT.value
    visual: VisualSettings = field(default_factory=VisualSettings)
    motor: MotorSettings = field(default_factory=MotorSettings)
    cognitive: CognitiveSettings = field(default_factory=CognitiveSettings)
    audio: AudioSettings = field(default_factory=AudioSettings)
    accommodations: DisabilityAccommodations = field(default_factory=DisabilityAccommodations)
    high_contrast_mode: bool = False
    screen_reader_optimized: bool = False
    reduced_data_mode: bool = False  # For low-bandwidth situations
    offline_mode_enabled: bool = False
    language: str = "en"  # English, sw (Kiswahili), bilingual
    custom_settings: Dict = field(default_factory=dict)
    
    def apply_profile(self, profile: AccessibilityProfile):
        """Apply a predefined accessibility profile"""
        profile_configs = {
            AccessibilityProfile.VISUAL_IMPAIRMENT: {
                "visual": VisualSettings(
                    font_size="extra_large",
                    color_scheme="high_contrast",
                    text_zoom=150,
                    color_blind_mode="high",
                    focus_indicator="high"
                ),
                "audio": AudioSettings(
                    screen_reader_enabled=True,
                    announcements_enabled=True,
                    sound_feedback=False,
                    visual_notifications=True
                ),
                "screen_reader_optimized": True,
                "high_contrast_mode": True
            },
            AccessibilityProfile.MOTOR_DISABILITY: {
                "motor": MotorSettings(
                    keyboard_navigation=True,
                    skip_links=True,
                    click_hold_time=1000,
                    drag_drop_enabled=False,
                    auto_submit_forms=True
                ),
                "cognitive": CognitiveSettings(
                    simplified_navigation=True,
                    chunk_content=True,
                    max_items_per_page=3
                )
            },
            AccessibilityProfile.COGNITIVE_DIFFICULTY: {
                "cognitive": CognitiveSettings(
                    simplified_navigation=True,
                    reduced_motion=True,
                    hide_animations=True,
                    chunk_content=True,
                    max_items_per_page=3,
                    simple_language_mode=True,
                    show_summaries=True,
                    break_into_steps=True,
                    reading_level="simplified"
                ),
                "visual": VisualSettings(
                    font_size="large",
                    line_spacing="relaxed",
                    letter_spacing="relaxed"
                )
            },
            AccessibilityProfile.NEURODIVERGENT: {
                "cognitive": CognitiveSettings(
                    reduced_motion=True,
                    hide_animations=True,
                    show_progress_steps=True,
                    chunk_content=True,
                    clear_all_button=True,
                    confirmation_dialogs=True,
                    icon_labels=True,
                    breadcrumbs=True,
                    auto_save_drafts=True,
                    undo_functionality=True
                ),
                "visual": VisualSettings(
                    font_size="large",
                    color_scheme="high_contrast",
                    font_family="dyslexic_friendly"
                ),
                "motor": MotorSettings(
                    skip_links=True
                )
            },
            AccessibilityProfile.DEAF_HARD_HEARING: {
                "audio": AudioSettings(
                    sound_feedback=False,
                    visual_notifications=True,
                    captcha_alternative=True,
                    transcript_available=True
                )
            }
        }
        
        if profile in profile_configs:
            config_dict: Any = profile_configs[profile]
            for section, settings in config_dict.items(): # type: ignore
                if hasattr(self, section):
                    if isinstance(settings, dict):
                        for key, value in settings.items():
                            section_obj: Any = getattr(self, section)
                            if hasattr(section_obj, key):
                                setattr(section_obj, key, value)
                    else:
                        setattr(self, section, settings)
        
        self.profile = str(profile.value) # type: ignore
    
    def to_dict(self) -> Dict:
        """Convert preferences to dictionary for storage"""
        return {
            "profile": self.profile,
            "visual": self.visual.__dict__,
            "motor": self.motor.__dict__,
            "cognitive": self.cognitive.__dict__,
            "audio": self.audio.__dict__,
            "accommodations": self.accommodations.__dict__,
            "high_contrast_mode": self.high_contrast_mode,
            "screen_reader_optimized": self.screen_reader_optimized,
            "reduced_data_mode": self.reduced_data_mode,
            "offline_mode_enabled": self.offline_mode_enabled,
            "language": self.language,
            "custom_settings": self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AccessibilityPreferences":
        """Create preferences from dictionary"""
        prefs = cls()
        if "profile" in data:
            prefs.profile = data["profile"]
        if "visual" in data:
            prefs.visual = VisualSettings(**cast(dict, data["visual"])) # type: ignore
        if "motor" in data:
            prefs.motor = MotorSettings(**cast(dict, data["motor"])) # type: ignore
        if "cognitive" in data:
            prefs.cognitive = CognitiveSettings(**cast(dict, data["cognitive"])) # type: ignore
        if "audio" in data:
            prefs.audio = AudioSettings(**cast(dict, data["audio"])) # type: ignore
        if "accommodations" in data:
            prefs.accommodations = DisabilityAccommodations(**cast(dict, data["accommodations"])) # type: ignore
        if "high_contrast_mode" in data:
            prefs.high_contrast_mode = data["high_contrast_mode"]
        if "screen_reader_optimized" in data:
            prefs.screen_reader_optimized = data["screen_reader_optimized"]
        if "reduced_data_mode" in data:
            prefs.reduced_data_mode = data["reduced_data_mode"]
        if "offline_mode_enabled" in data:
            prefs.offline_mode_enabled = data["offline_mode_enabled"]
        if "language" in data:
            prefs.language = data["language"]
        if "custom_settings" in data:
            prefs.custom_settings = data["custom_settings"]
        return prefs
    
    def to_json(self, filepath: Optional[str] = None) -> str:
        """Export preferences as JSON string"""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2)
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        return json_str
    
    @classmethod
    def from_json(cls, json_str: Optional[str] = None, filepath: Optional[str] = None) -> "AccessibilityPreferences":
        """Import preferences from JSON"""
        if filepath:
            with open(filepath, 'r') as f:
                json_str = f.read()
        if json_str:
            data = json.loads(json_str)
            return cls.from_dict(data)
        return cls()


# Accommodation Need Templates
DISABILITY_ACCOMMODATION_TEMPLATES = {
    "visual_impairment": [
        "screen_reader_compatible",
        "large_print_materials",
        "braille_documentation",
        "audio_descriptions",
        "high_contrast_displays",
        "magnification_software"
    ],
    "mobility_disability": [
        "wheelchair_accessible_workspace",
        "adjustable_desk",
        "ergonomic_equipment",
        "voice_recognition_software",
        "alternative_input_devices",
        "accessible_parking"
    ],
    "hearing_impairment": [
        "sign_language_interpreter",
        "captioning_services",
        "visual_alert_systems",
        "assistive_listening_devices",
        "written_communication",
        "real_time_transcription"
    ],
    "cognitive_disability": [
        "clear_written_instructions",
        "extended_time_requirements",
        "task_breakdown_assistance",
        "consistent_work_environment",
        "noise_reduced_workspace",
        "memory_aids"
    ],
    "adhd": [
        "quiet_workspace",
        "flexible_break_schedule",
        "task_management_software",
        "structured_daily_routines",
        "reduced_distractions",
        "regular_feedback_sessions"
    ],
    "autism_spectrum": [
        "predictable_work_schedule",
        "clear_communication",
        "sensory_considerations",
        "quiet_workspace_option",
        "social_skills_support",
        "interest_based_motivation"
    ],
    "dyslexia": [
        "text_to_speech_software",
        "extended_time_reading",
        "dyslexia_friendly_fonts",
        "audio_formats",
        "proofreading_support",
        "structured_approaches"
    ],
    "chronic_illness": [
        "flexible_work_hours",
        "remote_work_option",
        "rest_break_flexibility",
        "ergonomic_workspace",
        "health_appointment_accommodation",
        "reduced_stress_environment"
    ]
}

# Workplace Accessibility Requirements
WORKPLACE_REQUIREMENTS = [
    "fully_accessible_building",
    "elevator_access",
    "accessible_restrooms",
    "adjustable_workstations",
    "ergonomic_furniture",
    "accessible_parking",
    "public_transit_proximity",
    "flexible_work_hours",
    "remote_work_option",
    "assistive_technology_provided",
    "sign_language_interpreter_available",
    "captioning_services_available",
    "quiet_workspace_available",
    "sensory_friendly_environment",
    "service_animal_friendly",
    "accessible_emergency_exits",
    "medical_facility_proximity"
]


def get_default_accommodations(disability_type: str) -> List[str]:
    """Get default accommodation needs based on disability type"""
    return DISABILITY_ACCOMMODATION_TEMPLATES.get(
        disability_type.lower().replace(" ", "_"), 
        []
    )
