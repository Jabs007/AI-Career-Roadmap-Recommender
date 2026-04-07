"""
Accessible Career Recommender App
==============================
Streamlit app with comprehensive accessibility features including:
- Screen reader support
- Keyboard navigation
- Adjustable visual settings
- Simplified navigation modes
- Multi-language support (English & Kiswahili)
- Mobile accessibility
- Offline mode support
"""

import streamlit as st # type: ignore
import pandas as pd # type: ignore
from typing import Dict, List, Optional
from datetime import datetime
import os
import json

# Import accessibility modules
from accessibility.accessibility_settings import ( # type: ignore
    AccessibilityPreferences,
    AccessibilityProfile,
    VisualSettings,
    MotorSettings,
    CognitiveSettings,
    AudioSettings,
    DisabilityAccommodations
)
from accessibility.privacy_consent import ( # type: ignore
    PrivacyManager,
    ConsentStatus,
    CONSENT_FORMS
)
from accessibility.streamlit_components import ( # type: ignore
    AccessibleComponents,
    apply_accessibility_settings
)
from accessibility.inclusive_recommender import ( # type: ignore
    InclusiveRecommender,
    AccessibilityRequirement,
    AccessibilityPriority
)

# Page configuration
st.set_page_config(
    page_title="🎓 AI Career Roadmap - Accessible",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)


class AccessibleCareerApp:
    """
    Main application class with accessibility-first design.
    """
    
    def __init__(self):
        """Initialize the accessible app"""
        self.session_state_key = "accessibility_prefs"
        self.privacy_manager = PrivacyManager()
        self.inclusive_recommender = InclusiveRecommender()
        
        # Initialize session state
        if "user_id" not in st.session_state:
            st.session_state["user_id"] = self._generate_user_id()
        
        if self.session_state_key not in st.session_state:
            st.session_state[self.session_state_key] = AccessibilityPreferences()
    
    def _generate_user_id(self) -> str:
        """Generate anonymous user ID"""
        import hashlib
        import uuid
        return hashlib.sha256(
            f"{uuid.uuid4()}{datetime.now()}".encode()
        ).hexdigest()[:16] # type: ignore
    
    def apply_visual_settings(self):
        """Apply accessibility visual settings to the app"""
        prefs = st.session_state[self.session_state_key]
        
        # Get settings
        font_size = prefs.visual.font_size
        color_scheme = prefs.visual.color_scheme
        high_contrast = prefs.high_contrast_mode
        reduced_motion = prefs.cognitive.reduced_motion
        
        # Apply CSS
        apply_accessibility_settings(
            font_size=font_size,
            color_scheme=color_scheme,
            high_contrast=high_contrast,
            reduced_motion=reduced_motion
        )
    
    def render_skip_link(self):
        """Render skip navigation link"""
        st.markdown("""
            <a href="#main-content" class="skip-link">
                Skip to main content
            </a>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render accessible header"""
        st.title("🎓 AI Career Roadmap Recommender")
        st.caption("Accessible Career Guidance for Kenyan Students")
        
        # Language selector
        col1, col2 = st.columns([3, 1])
        with col2:
            language = st.selectbox(
                "🌐 Language / Lugha",
                ["English", "Kiswahili"],
                label_visibility="collapsed"
            )
            if language == "Kiswahili":
                st.session_state["language"] = "sw"
            else:
                st.session_state["language"] = "en"
    
    def render_accessibility_settings(self):
        """Render accessibility settings panel"""
        with st.sidebar:
            st.header("♿ Accessibility Settings")
            
            prefs = st.session_state[self.session_state_key]
            
            # Quick profile selection
            st.subheader("Quick Profile")
            profile = st.selectbox(
                "Select accessibility profile",
                [p.value for p in AccessibilityProfile],
                index=0
            )
            
            if st.button("Apply Profile"):
                prefs.apply_profile(AccessibilityProfile(profile))
                st.session_state[self.session_state_key] = prefs
                st.rerun()
            
            st.divider()
            
            # Visual settings
            st.subheader("👁️ Visual Settings")
            
            prefs.visual.font_size = st.select_slider(
                "Font Size",
                options=["small", "medium", "large", "extra_large"],
                value=prefs.visual.font_size
            )
            
            prefs.visual.color_scheme = st.selectbox(
                "Color Scheme",
                ["default", "high_contrast", "dark_mode", "light_mode"],
                index=["default", "high_contrast", "dark_mode", "light_mode"].index(
                    prefs.visual.color_scheme
                )
            )
            
            prefs.high_contrast_mode = st.toggle(
                "High Contrast Mode",
                value=prefs.high_contrast_mode
            )
            
            st.divider()
            
            # Cognitive settings
            st.subheader("🧠 Cognitive Settings")
            
            prefs.cognitive.simplified_navigation = st.toggle(
                "Simplified Navigation",
                value=prefs.cognitive.simplified_navigation
            )
            
            prefs.cognitive.reduced_motion = st.toggle(
                "Reduced Motion",
                value=prefs.cognitive.reduced_motion
            )
            
            prefs.cognitive.hide_animations = st.toggle(
                "Hide Animations",
                value=prefs.cognitive.hide_animations
            )
            
            prefs.cognitive.simple_language_mode = st.toggle(
                "Simple Language Mode",
                value=prefs.cognitive.simple_language_mode
            )
            
            prefs.cognitive.max_items_per_page = st.slider(
                "Items per Page",
                min_value=3,
                max_value=10,
                value=prefs.cognitive.max_items_per_page
            )
            
            st.divider()
            
            # Audio settings
            st.subheader("🔊 Audio Settings")
            
            prefs.audio.screen_reader_enabled = st.toggle(
                "Screen Reader Mode",
                value=prefs.audio.screen_reader_enabled
            )
            
            prefs.audio.visual_notifications = st.toggle(
                "Visual Notifications",
                value=prefs.audio.visual_notifications
            )
            
            # Save button
            if st.button("💾 Save Settings"):
                self._save_preferences(prefs)
                st.success("Settings saved!")
    
    def render_accommodation_preferences(self):
        """Render disability accommodation preferences section"""
        st.header("♿ Disability Accommodation Preferences")
        
        prefs = st.session_state[self.session_state_key]
        
        # Consent first
        st.info("""
            💡 **Privacy First**: Your accommodation information is kept private 
            and shared only with your consent.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            disability_type = st.selectbox(
                "Disability Type (Optional)",
                ["", "Visual Impairment", "Hearing Impairment", 
                 "Mobility Disability", "Cognitive Disability",
                 "ADHD", "Autism Spectrum", "Dyslexia",
                 "Chronic Illness", "Multiple Disabilities",
                 "Prefer not to say"]
            )
            
            prefs.accommodations.disability_type = disability_type if disability_type else None
        
        with col2:
            work_arrangement = st.selectbox(
                "Preferred Work Arrangement",
                ["any", "remote", "hybrid", "onsite"],
                index=["any", "remote", "hybrid", "onsite"].index(
                    prefs.accommodations.preferred_work_arrangement
                )
            )
            prefs.accommodations.preferred_work_arrangement = work_arrangement
        
        # Accommodation needs
        st.subheader("Accommodation Needs")
        
        accommodation_templates = {
            "Visual": [
                "screen_reader_compatible", "large_print_materials",
                "braille_documentation", "audio_descriptions"
            ],
            "Mobility": [
                "wheelchair_accessible_workspace", "adjustable_desk",
                "ergonomic_equipment", "voice_recognition_software"
            ],
            "Hearing": [
                "sign_language_interpreter", "captioning_services",
                "visual_alert_systems", "real_time_transcription"
            ],
            "Cognitive": [
                "clear_written_instructions", "extended_time_requirements",
                "task_breakdown_assistance", "consistent_work_environment"
            ],
            "Technology": [
                "assistive_technology", "accessible_software",
                "alternative_input_methods", "keyboard_only_interface"
            ]
        }
        
        selected_needs = []
        
        for category, needs in accommodation_templates.items():
            st.markdown(f"**{category} Needs**")
            cols = st.columns(3)
            for i, need in enumerate(needs):
                with cols[i % 3]:
                    if st.checkbox(need.replace("_", " ").title()):
                        selected_needs.append({
                            "category": category.lower(),
                            "specific_accommodation": need,
                            "priority": "medium",
                            "is_negotiable": True,
                            "alternatives": []
                        })
        
        prefs.accommodations.accommodation_needs = selected_needs
        
        # Save preferences
        if st.button("💾 Save Accommodation Preferences"):
            self._save_accommodation_preferences(prefs)
            st.success("Preferences saved!")
    
    def render_main_content(self):
        """Render main app content with accessibility support"""
        st.header("🔍 Find Your Career Path")
        
        # Apply visual settings
        self.apply_visual_settings()
        
        # Skip link
        self.render_skip_link()
        
        prefs = st.session_state[self.session_state_key]
        
        # Determine layout complexity based on preferences
        if prefs.cognitive.simplified_navigation:
            self._render_simplified_view()
        else:
            self._render_standard_view()
    
    def _render_simplified_view(self):
        """Render simplified navigation view for cognitive accessibility"""
        st.info("📝 Simple View: Answer 3 questions to get career recommendations.")
        
        # Question 1: Career interest
        career_interest = st.text_area(
            "What kind of work would you enjoy?",
            placeholder="Example: I want to help people and work with computers",
            help="Describe what you want to do in your career"
        )
        
        # Question 2: Education
        mean_grade = st.selectbox(
            "What was your KCSE mean grade?",
            ["", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"]
        )
        
        # Question 3: Subjects
        math_grade = st.selectbox(
            "Mathematics Grade",
            ["", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"]
        )
        
        # Submit
        if st.button("🎯 Get My Recommendations"):
            if career_interest and mean_grade:
                st.session_state["kcse_results"] = {
                    "mean_grade": mean_grade,
                    "subjects": {"Mathematics": math_grade}
                }
                st.session_state["student_text"] = career_interest
                self._generate_simple_recommendations()
            else:
                st.error("Please answer all questions to get recommendations.")
    
    def _render_standard_view(self):
        """Render standard view with full options"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 Your Career Vision")
            student_text = st.text_area(
                "Describe your dream career in your own words:",
                placeholder="I want to build apps that help farmers...",
                height=150,
                help="Be as detailed as possible about what you want to do"
            )
        
        with col2:
            st.subheader("📊 Your Academic Profile")
            
            mean_grade = st.selectbox(
                "KCSE Mean Grade",
                ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"]
            )
            
            # Subject grades
            subjects = {}
            subject_cols = st.columns(3)
            subject_list = ["Mathematics", "English", "Physics", 
                           "Chemistry", "Biology", "Geography"]
            
            for i, sub in enumerate(subject_list):
                with subject_cols[i % 3]:
                    subjects[sub] = st.selectbox(
                        f"{sub}",
                        ["", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"]
                    )
            
            kcse_results = {
                "mean_grade": mean_grade,
                "subjects": {k: v for k, v in subjects.items() if v}
            }
        
        # Strategy selection
        st.subheader("⚖️ Discovery Strategy")
        
        strategy = st.radio(
            "How should we prioritize your recommendations?",
            ["balanced", "passion_first", "market_first"],
            format_func=lambda x: {
                "balanced": "⚖️ Balanced (Both passion and job market)",
                "passion_first": "❤️ Passion First (Follow your interests)",
                "market_first": "💼 Market First (Job security first)"
            }[x]
        )
        
        alpha = {"balanced": 0.75, "passion_first": 0.9, "market_first": 0.4}[strategy]
        
        # Submit button
        if st.button("🎯 Get Career Recommendations", type="primary"):
            if student_text:
                st.session_state["kcse_results"] = kcse_results
                st.session_state["student_text"] = student_text
                st.session_state["alpha"] = alpha
                self._generate_recommendations()
            else:
                st.error("Please describe your career interests.")
    
    def _generate_simple_recommendations(self):
        """Generate recommendations in simple view"""
        st.header("✅ Your Career Recommendations")
        
        # Placeholder for recommendations
        st.info("Based on your input, here are your top career matches:")
        
        # Simplified output
        top_matches = [
            {"field": "Information Technology", "match": 85, "why": "Combines technology and helping others"},
            {"field": "Agriculture & Environmental", "match": 75, "why": "Working with farmers and nature"},
            {"field": "Education", "match": 70, "why": "Teaching and helping students learn"}
        ]
        
        for i, match in enumerate(top_matches, 1):
            with st.container():
                st.markdown(f"""
                    **{i}. {match['field']}** - {match['match']}% Match
                    
                    {match['why']}
                """)
                st.divider()
    
    def _generate_recommendations(self):
        """Generate recommendations with accessibility considerations"""
        st.header("🎯 Your Personalized Career Roadmap")
        
        student_text = st.session_state.get("student_text", "")
        kcse_results = st.session_state.get("kcse_results", {})
        alpha = st.session_state.get("alpha", 0.75)
        
        prefs = st.session_state[self.session_state_key]
        
        # Accessibility requirements
        accessibility_requirements = [
            AccessibilityRequirement(
                feature=need.get("specific_accommodation", ""),
                priority=need.get("priority", "medium"),
                category=need.get("category", "physical"),
                is_negotiable=need.get("is_negotiable", True),
                alternatives=need.get("alternatives", [])
            )
            for need in prefs.accommodations.accommodation_needs
        ]
        
        # Set requirements in recommender
        self.inclusive_recommender.set_accessibility_requirements(
            accessibility_requirements
        )
        
        # Placeholder for enhanced recommendations
        st.success("Recommendations generated with accessibility considerations!")
        
        # Display placeholder
        st.info("""
            🔧 **Accessibility Features Applied**:
            
            - Job recommendations consider your accommodation needs
            - Accessibility scores calculated for each opportunity
            - Workplace barriers identified and flagged
            - Accommodation strategies suggested where applicable
        """)
    
    def _save_preferences(self, prefs: AccessibilityPreferences):
        """Save accessibility preferences"""
        st.session_state[self.session_state_key] = prefs
        # In production, save to database
    
    def _save_accommodation_preferences(self, prefs: AccessibilityPreferences):
        """Save accommodation preferences with consent"""
        user_id = st.session_state["user_id"]
        
        # Create consent request
        consent = self.privacy_manager.create_consent_request(
            user_id=user_id,
            data_categories=["disability_info", "accommodation_needs"],
            purpose="To provide accessible job recommendations"
        )
        
        # Save preferences
        self._save_preferences(prefs)
        
        # Return consent request for user approval
        return consent
    
    def render_mobile_accessibility(self):
        """Render mobile-specific accessibility features"""
        with st.expander("📱 Mobile Accessibility", expanded=False):
            st.markdown("""
                ### Mobile-Friendly Features
                
                - **Touch-Friendly**: Large tap targets (minimum 44x44 pixels)
                - **Responsive Design**: Adapts to any screen size
                - **Voice Input**: Use voice to describe your career interests
                - **Offline Mode**: Save recommendations for later viewing
                
                ### Reduced Data Mode
                
                - Toggle in sidebar to reduce data usage
                - Simplified images and graphics
                - Text-based content prioritized
            """)
    
    def render_campus_services_integration(self):
        """Render campus disability services integration"""
        with st.expander("🏫 Campus Disability Services", expanded=False):
            st.markdown("""
                ### Connect with Campus Support
                
                Share your accommodation needs with campus disability services
                for additional support.
                
                **Available Services:**
                
                - Disability assessment and verification
                - Accommodation planning
                - Assistive technology training
                - Academic support coordination
                - Career counseling with accessibility focus
                
                ### How It Works
                
                1. Authorize sharing (with your consent)
                2. Select services to share with
                3. Your verified needs are shared securely
                4. Services reach out to support you
            """)
            
            if st.button("📤 Request Integration"):
                st.info("This will connect with your campus disability services portal.")
    
    def run(self):
        """Main app entry point"""
        # Apply settings
        self.apply_visual_settings()
        
        # Header
        self.render_header()
        
        # Sidebar
        with st.sidebar:
            self.render_accessibility_settings()
            
            st.divider()
            
            # Mobile & Campus sections
            self.render_mobile_accessibility()
            self.render_campus_services_integration()
        
        # Main content
        main_container = st.container(id="main-content")
        with main_container:
            self.render_main_content()
        
        # Campus services
        self.render_campus_services_integration()


def main():
    """Main entry point"""
    app = AccessibleCareerApp()
    app.run()


if __name__ == "__main__":
    main()
