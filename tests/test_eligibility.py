import unittest
import os
import sys
import json
import pandas as pd # type: ignore
from typing import Any, Dict, List, Optional, ClassVar # type: ignore

# Add the project root to sys.path to allow imports from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.recommender import CareerRecommender # type: ignore

class TestEligibilityLogic(unittest.TestCase):
    recommender: ClassVar[CareerRecommender]

    @classmethod
    def setUpClass(cls):
        """Set up the recommender which loads real data (if available) or defaults."""
        cls.recommender = CareerRecommender()

    def test_eligible_student(self):
        """Test a student who should be eligible for Computer Science."""
        results = {
            "mean_grade": "A",
            "subjects": {
                "Mathematics": "A",
                "Physics": "A",
                "English": "A",
                "Kiswahili": "A",
                "Chemistry": "A",
                "Biology": "A"
            }
        }
        # Find a CS program in requirements
        cs_prog = "BACHELOR OF SCIENCE (COMPUTER SCIENCE)"
        status, reason, details = self.recommender.check_eligibility(cs_prog, results)
        
        self.assertEqual(status, "ELIGIBLE")
        self.assertIn("Meets all criteria", reason)

    def test_aspirational_student(self):
        """Test a student who is missing a requirement by 1 point."""
        results = {
            "mean_grade": "C+",
            "subjects": {
                "Mathematics": "C", # Required C+ for many degrees
                "Physics": "C+",
                "English": "C+",
                "Kiswahili": "C+"
            }
        }
        # CS usually requires C+ in Math
        cs_prog = "BACHELOR OF SCIENCE (COMPUTER SCIENCE)"
        status, reason, details = self.recommender.check_eligibility(cs_prog, results)
        
        # Check if it correctly identifies as ASPIRATIONAL if only missing by 1 grade point
        # In our logic, C is 1 point below C+.
        self.assertEqual(status, "ASPIRATIONAL")
        self.assertIn("Slightly below requirement", reason)

    def test_not_eligible_student(self):
        """Test a student who is far from requirements."""
        results = {
            "mean_grade": "C-",
            "subjects": {
                "Mathematics": "D+",
                "Physics": "D",
                "English": "C-"
            }
        }
        cs_prog = "BACHELOR OF SCIENCE (COMPUTER SCIENCE)"
        status, reason, details = self.recommender.check_eligibility(cs_prog, results)
        
        self.assertEqual(status, "NOT ELIGIBLE")
        self.assertIn("Does not meet requirements", reason)

    def test_diploma_redirection(self):
        """Test if the recommender suggests a Diploma when degree is not eligible."""
        user_text = "I want to work with computers and build software"
        results = {
            "mean_grade": "C-",
            "subjects": {
                "Mathematics": "C-",
                "Physics": "D+",
                "English": "C-"
            }
        }
        # Recommend for an IT interest
        recommendations = self.recommender.recommend(user_text, kcse_results=results)
        
        # Find the IT recommendation
        it_rec: Optional[Dict[str, Any]] = next((r for r in recommendations if "Information Technology" in r['dept'] or "IT" in r['dept']), None)
        
        self.assertIsNotNone(it_rec)
        if it_rec is not None:
            self.assertEqual(it_rec['dept_status'], "ELIGIBLE (DIPLOMA)")
            # Check if diploma programs are actually added to eligibility map
            elig_details: Dict[str, Any] = it_rec.get('eligibility', {})
            diplomas = [name for name in elig_details.keys() if "DIPLOMA" in name]
            self.assertGreater(len(diplomas), 0)

if __name__ == '__main__':
    unittest.main()
