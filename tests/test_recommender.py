import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import json
import sys
import os

# Import the class to test
# Note: We need to make sure the import path works. 
# In a real scenario, we might install the project in editable mode or manipulate sys.path.
# Handle complex imports by mocking the heavy NLP components BEFORE importing reommender
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the InterestClassifier and its dependencies to avoid loading NLP models
mock_classifier_module = MagicMock()
sys.modules['models.interest_classifier'] = mock_classifier_module
sys.modules['models.interest_vectorizer'] = MagicMock()
sys.modules['models.nlp_preprocessing'] = MagicMock()

# Now we can import the class under test
from models.recommender import CareerRecommender

class TestCareerRecommender:

    @pytest.fixture
    def mock_recommender(self):
        """
        Creates a CareerRecommender instance with mocked data sources.
        """
        # Mock the Internal Classifier instance itself
        with patch('models.recommender.InterestClassifier') as MockClassifier, \
             patch('pandas.read_csv') as mock_read_csv, \
             patch('builtins.open', new_callable=MagicMock) as mock_open, \
             patch('json.load') as mock_json_load:
            
            # Setup Mock CSV Data (Jobs Demand)
            mock_demand_df = pd.DataFrame({
                'Department': ['Information Technology', 'Medicine'],
                'job_count': [100, 50]
            })
            mock_read_csv.return_value = mock_demand_df
            
            # Setup Mock JSON Data (Skill Map & Requirements)
            mock_json_load.side_effect = [
                # Skill Map
                {
                    "IT": {"skills": ["Python", "AWS"], "programs": ["Bachelor of Science in Computer Science"]},
                    "Health Sciences": {"skills": ["Anatomy"], "programs": ["Bachelor of Medicine and Bachelor of Surgery"]}
                },
                # Requirements
                {
                    "Bachelor of Science in Computer Science": {
                        "level": "Degree",
                        "min_mean_grade": "C+",
                        "required_subjects": {"Mathematics": "B", "Physics": "C+"}
                    },
                    "Bachelor of Medicine and Bachelor of Surgery": {
                        "level": "Degree",
                        "min_mean_grade": "B+",
                        "required_subjects": {"Biology": "B+", "Chemistry": "B+"}
                    }
                }
            ]
            
            recommender = CareerRecommender()
            # Manually inject the mocked data to be ensuring (init might have complex logic)
            # But with the mocks above, init should populate self.demand_df, self.skill_map, etc.
            
            # Overwrite specific attributes for reliable testing if init logic is complex
            recommender.kuccps_requirements = {
                "Computer Science": {
                    "level": "Degree",
                    "min_mean_grade": "C+",
                    "required_subjects": {"Mathematics": "C+", "Physics": "C"}
                },
                "Medicine": {
                    "level": "Degree",
                    "min_mean_grade": "B+",
                    "required_subjects": {"Biology": "B", "Chemistry": "B"}
                }
            }
            
            return recommender

    def test_eligibility_eligible(self, mock_recommender):
        """Test a student who MEETS all requirements."""
        student_results = {
            "mean_grade": "A",
            "subjects": {"Mathematics": "A", "Physics": "A", "English": "A"}
        }
        status, reason = mock_recommender.check_eligibility("Computer Science", student_results)
        assert status == "ELIGIBLE"
        assert "Meets all criteria" in reason

    def test_eligibility_grade_fail(self, mock_recommender):
        """Test a student who FAILS the Mean Grade check."""
        student_results = {
            "mean_grade": "D+", # Requirement is C+
            "subjects": {"Mathematics": "A", "Physics": "A"}
        }
        status, reason = mock_recommender.check_eligibility("Computer Science", student_results)
        assert status == "NOT ELIGIBLE"
        assert "Mean Grade" in reason

    def test_eligibility_subject_fail(self, mock_recommender):
        """Test a student who FAILS a specific Subject check."""
        student_results = {
            "mean_grade": "A", 
            "subjects": {"Mathematics": "D", "Physics": "A"} # Math req is C+
        }
        status, reason = mock_recommender.check_eligibility("Computer Science", student_results)
        assert status == "NOT ELIGIBLE"
        assert "Subject Mathematics grade" in reason

    def test_eligibility_aspirational(self, mock_recommender):
        """Test 'Aspirational' logic (missing by 1 grade point)."""
        # Req: C+ (7 pts). Student has C (6 pts)
        # Math C+ (7), Student has C (6) -> Aspirational?
        # Recommender logic says: if status == ELIGIBLE (implied mean grade pass) AND subject is -1 point
        
        student_results = {
            "mean_grade": "B",
            "subjects": {"Mathematics": "C", "Physics": "C"} 
        }
        # Math is C (6), Req is C+ (7). Diff is 1.
        status, reason = mock_recommender.check_eligibility("Computer Science", student_results)
        assert status == "ASPIRATIONAL"
        assert "is slightly below" in reason

