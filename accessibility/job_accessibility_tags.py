"""
Job Accessibility Tagging System
================================
System for tagging and matching job listings with accessibility features.

This module provides:
- Standardized accessibility feature definitions
- Job accessibility tagging
- Employer accessibility profiles
- Matching algorithms for accessibility requirements
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
import json
import os


class AccessibilityFeature(Enum):
    """
    Standardized accessibility features for job tagging.
    Based on WCAG 2.1 and ADA requirements.
    """
    # Physical Accessibility
    WHEELCHAIR_ACCESSIBLE = "wheelchair_accessible"
    ELEVATOR_ACCESS = "elevator_access"
    ACCESSIBLE_PARKING = "accessible_parking"
    ACCESSIBLE_RESTROOM = "accessible_restroom"
    ADJUSTABLE_DESK = "adjustable_desk"
    ERGONOMIC_EQUIPMENT = "ergonomic_equipment"
    GROUND_FLOOR_ACCESS = "ground_floor_access"
    RAMP_ACCESS = "ramp_access"
    ACCESSIBLE_ENTRANCE = "accessible_entrance"
    SERVICE_ANIMAL_FRIENDLY = "service_animal_friendly"
    
    # Sensory Accessibility
    QUIET_WORKSPACE = "quiet_workspace"
    NOISE_CANCELLATION = "noise_cancellation"
    NATURAL_LIGHT = "natural_light"
    ADJUSTABLE_LIGHTING = "adjustable_lighting"
    LOW_SCENT_ENVIRONMENT = "low_scent_environment"
    
    # Communication Accessibility
    SIGN_LANGUAGE_INTERPRETER = "sign_language_interpreter"
    CAPTIONING_SERVICES = "captioning_services"
    VIDEO_CALLS_WITH_CAPTIONS = "video_calls_with_captions"
    REAL_TIME_TRANSCRIPTION = "real_time_transcription"
    WRITTEN_COMMUNICATION = "written_communication"
    VIDEO_RELAY_SERVICE = "video_relay_service"
    VISUAL_ALERTS = "visual_alerts"
    
    # Technology Accessibility
    SCREEN_READER_COMPATIBLE = "screen_reader_compatible"
    ACCESSIBLE_SOFTWARE = "accessible_software"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    VOICE_RECOGNITION_SOFTWARE = "voice_recognition_software"
    SCREEN_MAGNIFICATION = "screen_magnification"
    LARGE_DISPLAYS = "large_displays"
    BRAILLE_DISPLAYS = "braille_displays"
    
    # Cognitive Accessibility
    FLEXIBLE_SCHEDULE = "flexible_schedule"
    REMOTE_WORK = "remote_work"
    HYBRID_WORK = "hybrid_work"
    STRUCTURED_TASKS = "structured_tasks"
    REGULAR_FEEDBACK = "regular_feedback"
    WORKLOAD_ADJUSTMENT = "workload_adjustment"
    CLEAR_INSTRUCTIONS = "clear_instructions"
    TASK_BREAKDOWN = "task_breakdown"
    
    # Workplace Culture
    DISABILITY_AWARENESS_TRAINING = "disability_awareness_training"
    INCLUSIVE_HIRING = "inclusive_hiring"
    DIVERSITY_INITIATIVES = "diversity_initiatives"
    ACCESSIBILITY_COMMITTEE = "accessibility_committee"
    
    # Additional Accommodations
    FLEXIBLE_BREAKS = "flexible_breaks"
    PART_TIME_OPTION = "part_time_option"
    JOB_SHARING = "job_sharing"
    ASSISTIVE_TECH_PROVIDED = "assistive_tech_provided"
    TRAINING_PROVIDED = "training_provided"
    MENTORSHIP_PROGRAM = "mentorship_program"
    MEDICAL_FACILITY_PROXIMITY = "medical_facility_proximity"
    PUBLIC_TRANSPORT_PROXIMITY = "public_transport_proximity"


class AccessibilityLevel(Enum):
    """Level of accessibility support"""
    FULL = "full"           # All features available
    PARTIAL = "partial"    # Some features available
    BASIC = "basic"        # Minimal features
    NONE = "none"          # No accessibility features
    VERIFY = "verify"      # Needs verification


@dataclass
class WorkplaceAccessibilityProfile:
    """
    Profile of an employer's workplace accessibility.
    """
    employer_id: str
    employer_name: str
    accessibility_level: str = AccessibilityLevel.BASIC.value
    accessibility_score: float = 0.0
    features_available: List[str] = field(default_factory=list)
    features_planned: List[str] = field(default_factory=list)
    accommodation_history: Dict[str, int] = field(default_factory=dict)
    employee_satisfaction: float = 0.0
    last_assessment_date: Optional[str] = None
    assessment_notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "employer_id": self.employer_id,
            "employer_name": self.employer_name,
            "accessibility_level": self.accessibility_level,
            "features_available": self.features_available,
            "features_planned": self.features_planned,
            "accommodation_history": self.accommodation_history,
            "employee_satisfaction": self.employee_satisfaction,
            "last_assessment_date": self.last_assessment_date,
            "assessment_notes": self.assessment_notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkplaceAccessibilityProfile":
        """Create from dictionary"""
        return cls(
            employer_id=data.get("employer_id", ""),
            employer_name=data.get("employer_name", ""),
            accessibility_level=data.get("accessibility_level", "basic"),
            accessibility_score=data.get("accessibility_score", 0.0),
            features_available=data.get("features_available", []),
            features_planned=data.get("features_planned", []),
            accommodation_history=data.get("accommodation_history", {}),
            employee_satisfaction=data.get("employee_satisfaction", 0.0),
            last_assessment_date=data.get("last_assessment_date"),
            assessment_notes=data.get("assessment_notes", "")
        )
    
    def calculate_accessibility_score(self) -> float:
        """Calculate overall accessibility score (0-100)"""
        if not self.features_available:
            return 0.0
        
        # Define feature weights
        feature_weights = {
            "wheelchair_accessible": 10,
            "elevator_access": 8,
            "accessible_parking": 5,
            "accessible_restroom": 7,
            "adjustable_desk": 5,
            "ergonomic_equipment": 5,
            "quiet_workspace": 4,
            "sign_language_interpreter": 10,
            "captioning_services": 6,
            "screen_reader_compatible": 8,
            "remote_work": 6,
            "flexible_schedule": 5,
            "disability_awareness_training": 5
        }
        
        total_score = 0
        max_score = sum(feature_weights.values())
        
        for feature in self.features_available:
            weight = feature_weights.get(feature, 2)
            total_score += weight
        
        return float(min(100.0, float((total_score / max_score) * 100))) # type: ignore


@dataclass
class JobAccessibilityTag:
    """
    Accessibility tags for a specific job listing.
    """
    job_id: str
    employer_id: str
    features_available: List[str] = field(default_factory=list)
    features_not_available: List[str] = field(default_factory=list)
    features_negotiable: List[str] = field(default_factory=list)
    verification_status: str = "unverified"  # unverified, verified, pending
    verified_by: Optional[str] = None
    verification_date: Optional[str] = None
    candidate_notes: str = ""
    employer_questions: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "employer_id": self.employer_id,
            "features_available": self.features_available,
            "features_not_available": self.features_not_available,
            "features_negotiable": self.features_negotiable,
            "verification_status": self.verification_status,
            "verified_by": self.verified_by,
            "verification_date": self.verification_date,
            "candidate_notes": self.candidate_notes,
            "employer_questions": self.employer_questions
        }
    
    def get_accessibility_summary(self) -> Dict[str, Any]:
        """Get summary of job accessibility"""
        return {
            "total_features": len(self.features_available),
            "critical_features": sum(1 for f in self.features_available 
                                   if f in ["wheelchair_accessible", "sign_language_interpreter"]),
            "negotiable_count": len(self.features_negotiable),
            "verification_status": self.verification_status,
            "score": self._calculate_quick_score()
        }
    
    def _calculate_quick_score(self) -> float:
        """Calculate quick accessibility score"""
        critical_features = ["wheelchair_accessible", "sign_language_interpreter", 
                           "screen_reader_compatible", "elevator_access"]
        
        score = 0
        for feature in critical_features:
            if feature in self.features_available:
                score += 25
            elif feature in self.features_negotiable:
                score += 12
        
        # Additional features
        score += min(25, len(self.features_available) * 3)
        
        return min(100, score)


class AccessibilityTagStore:
    """
    Storage and management system for accessibility tags.
    """
    
    def __init__(self, storage_path: str = "data/accessibility/"):
        """
        Initialize the tag store.
        
        Args:
            storage_path: Path to store tag data
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        self.job_tags: Dict[str, JobAccessibilityTag] = {}
        self.employer_profiles: Dict[str, WorkplaceAccessibilityProfile] = {}
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load stored tags from disk"""
        job_tags_file = os.path.join(self.storage_path, "job_tags.json")
        employer_profiles_file = os.path.join(self.storage_path, "employer_profiles.json")
        
        if os.path.exists(job_tags_file):
            with open(job_tags_file, 'r') as f:
                data = json.load(f)
                for job_data in data:
                    tag = JobAccessibilityTag(**job_data) # type: ignore
                    self.job_tags[str(job_data["job_id"])] = tag
        
        if os.path.exists(employer_profiles_file):
            with open(employer_profiles_file, 'r') as f:
                data = json.load(f)
                for emp_data in data:
                    profile = WorkplaceAccessibilityProfile.from_dict(emp_data)
                    self.employer_profiles[emp_data["employer_id"]] = profile
    
    def _save_to_disk(self):
        """Save tags to disk"""
        job_tags_file = os.path.join(self.storage_path, "job_tags.json")
        employer_profiles_file = os.path.join(self.storage_path, "employer_profiles.json")
        
        # Save job tags
        job_tags_data = [tag.to_dict() for tag in self.job_tags.values()]
        with open(job_tags_file, 'w') as f:
            json.dump(job_tags_data, f, indent=2)
        
        # Save employer profiles
        employer_data = [profile.to_dict() for profile in self.employer_profiles.values()]
        with open(employer_profiles_file, 'w') as f:
            json.dump(employer_data, f, indent=2)
    
    def tag_job(self, job_id: str, employer_id: str, features: List[str]) -> JobAccessibilityTag:
        """
        Add accessibility tags to a job.
        
        Args:
            job_id: Job listing ID
            employer_id: Employer ID
            features: List of available accessibility features
            
        Returns:
            JobAccessibilityTag object
        """
        tag = JobAccessibilityTag(
            job_id=job_id,
            employer_id=employer_id,
            features_available=features
        )
        self.job_tags[job_id] = tag
        self._save_to_disk()
        return tag
    
    def get_job_accessibility(self, job_id: str) -> Optional[JobAccessibilityTag]:
        """Get accessibility tags for a job"""
        return self.job_tags.get(job_id)
    
    def get_employer_profile(self, employer_id: str) -> Optional[WorkplaceAccessibilityProfile]:
        """Get employer accessibility profile"""
        return self.employer_profiles.get(employer_id)
    
    def create_employer_profile(
        self,
        employer_id: str,
        employer_name: str,
        features: List[str]
    ) -> WorkplaceAccessibilityProfile:
        """
        Create or update employer accessibility profile.
        
        Args:
            employer_id: Unique employer identifier
            employer_name: Employer name
            features: Available accessibility features
            
        Returns:
            WorkplaceAccessibilityProfile object
        """
        profile = WorkplaceAccessibilityProfile(
            employer_id=employer_id,
            employer_name=employer_name,
            features_available=features
        )
        profile.accessibility_level = self._determine_level(features)
        profile.accessibility_score = profile.calculate_accessibility_score()
        
        self.employer_profiles[employer_id] = profile
        self._save_to_disk()
        return profile
    
    def _determine_level(self, features: List[str]) -> str:
        """Determine accessibility level based on features"""
        critical_features = ["wheelchair_accessible", "sign_language_interpreter"]
        important_features = ["elevator_access", "accessible_parking", 
                             "captioning_services", "screen_reader_compatible"]
        nice_features = ["flexible_schedule", "remote_work", "quiet_workspace"]
        
        has_critical = any(f in features for f in critical_features)
        has_important = any(f in features for f in important_features)
        has_nice = any(f in features for f in nice_features)
        
        if has_critical and has_important and has_nice:
            return AccessibilityLevel.FULL.value
        elif has_critical or (has_important and has_nice):
            return AccessibilityLevel.PARTIAL.value
        elif has_important or has_nice:
            return AccessibilityLevel.BASIC.value
        else:
            return AccessibilityLevel.NONE.value
    
    def find_jobs_with_features(
        self,
        required_features: List[str],
        minimum_score: float = 50
    ) -> List[JobAccessibilityTag]:
        """
        Find jobs that have specific accessibility features.
        
        Args:
            required_features: Features the job must have
            minimum_score: Minimum accessibility score
            
        Returns:
            List of matching JobAccessibilityTag objects
        """
        matches = []
        
        for tag in self.job_tags.values():
            # Check if job has all required features
            has_all = all(f in tag.features_available for f in required_features)
            
            # Calculate score
            score = tag._calculate_quick_score()
            
            if has_all and score >= minimum_score:
                matches.append(tag)
        
        return matches
    
    def generate_employer_questionnaire(self, employer_id: str) -> Dict[str, List[str]]:
        """
        Generate questions to ask employer about accessibility.
        
        Args:
            employer_id: Employer to generate questions for
            
        Returns:
            Dict of question categories and questions
        """
        questions = {
            "physical_access": [
                "Is the workplace wheelchair accessible?",
                "Are there elevators to all floors?",
                "Are accessible restrooms available on all floors?",
                "Is accessible parking available near the entrance?"
            ],
            "communication": [
                "Do you provide sign language interpreters for meetings?",
                "Are video calls available with captioning?",
                "Is real-time transcription available for conferences?"
            ],
            "technology": [
                "Are computers equipped with screen reader software?",
                "Is keyboard-only navigation supported?",
                "Are adjustable workstations available?"
            ],
            "work_arrangements": [
                "Is remote work available as an accommodation?",
                "Are flexible hours supported?",
                "Can workload be adjusted as needed?"
            ],
            "culture": [
                "Does the company provide disability awareness training?",
                "Is there an accessibility committee or liaison?",
                "How many accommodations have been provided in the past year?"
            ]
        }
        
        # Get employer's current profile to customize questions
        profile = self.get_employer_profile(employer_id)
        if profile:
            # Add questions about planned improvements
            if profile.features_planned:
                questions["planned_improvements"] = [
                    f"What is the timeline for adding {feature}?"
                    for feature in profile.features_planned[:3] # type: ignore
                ]
        
        return questions


# Feature descriptions for display
ACCESSIBILITY_FEATURE_DESCRIPTIONS = {
    "wheelchair_accessible": "Workspace is wheelchair accessible with ramps/lifts and wide doorways",
    "elevator_access": "Elevators available to access all floors",
    "accessible_parking": "Designated accessible parking spaces near entrance",
    "accessible_restroom": "Accessible restroom facilities available",
    "adjustable_desk": "Height-adjustable desks available",
    "quiet_workspace": "Low-noise workspace available for concentration",
    "sign_language_interpreter": "Sign language interpreter services available",
    "captioning_services": "Real-time captioning for meetings and events",
    "screen_reader_compatible": "Computers with screen reader software (JAWS, NVDA, VoiceOver)",
    "remote_work": "Remote work available as an accommodation",
    "flexible_schedule": "Flexible working hours supported",
    "disability_awareness_training": "Staff receive disability awareness training"
}


def get_feature_description(feature: str) -> str:
    """Get description for an accessibility feature"""
    return ACCESSIBILITY_FEATURE_DESCRIPTIONS.get(
        feature, 
        "Accessibility feature - please verify with employer"
    )
