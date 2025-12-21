import unittest
import pandas as pd
import json
import os
import configparser
from models.recommender import CareerRecommender

class TestCareerRecommender(unittest.TestCase):
    def setUp(self):
        """Set up a test environment with dummy data and config."""
        # 1. Create dummy data
        self.create_dummy_data()

        # 2. Create a dummy config.ini
        self.create_dummy_config()

        # 3. Initialize the recommender
        # It will use the dummy config.ini we just created
        self.recommender = CareerRecommender()

    def create_dummy_data(self):
        """Creates dummy data files for testing."""
        # Dummy Job Demand Metrics
        demand_df = pd.DataFrame({
            'Department': ['Information Technology', 'Business', 'Health'],
            'job_count': [150, 80, 50]
        })
        demand_df.to_csv('test_demand.csv', index=False)

        # Dummy Career Skill Map
        skill_map = {
            "Information Technology": {"skills": ["Python", "SQL", "Cloud Computing"], "programs": ["BSc. Computer Science"]},
            "Business": {"skills": ["Marketing", "Financial Analysis"], "programs": ["BBA"]},
            "Health": {"skills": ["Anatomy", "Patient Care"], "programs": ["BSc. Nursing"]}
        }
        with open('test_skill_map.json', 'w') as f:
            json.dump(skill_map, f)

        # Dummy Scraped Jobs
        jobs_df = pd.DataFrame({
            'title': ['Software Engineer', 'Data Analyst', 'Marketing Manager'],
            'description': ['Writes code', 'Analyzes data', 'Manages marketing'],
            'department': ['Technology', 'Technology', 'Business']
        })
        jobs_df.to_csv('test_jobs.csv', index=False)

        # Dummy KUCCPS Courses
        courses_df = pd.DataFrame({
            'course': ['BSc. Computer Science', 'BBA', 'BSc. Nursing'],
            'department': ['Technology', 'Business', 'Health']
        })
        courses_df.to_csv('test_courses.csv', index=False)

        # Dummy KUCCPS Requirements
        requirements = {
            "BSc. Computer Science": {
                "level": "Degree", "min_mean_grade": "C+",
                "required_subjects": {"Mathematics": "B-", "Physics": "C+"}
            },
            "BBA": {
                "level": "Degree", "min_mean_grade": "C+",
                "required_subjects": {"Mathematics": "C+", "English": "B-"}
            }
        }
        with open('test_requirements.json', 'w') as f:
            json.dump(requirements, f)

    def create_dummy_config(self):
        """Creates a dummy config.ini file pointing to test data."""
        config = configparser.ConfigParser()
        config['paths'] = {
            'demand_csv': 'test_demand.csv',
            'skill_map_json': 'test_skill_map.json',
            'jobs_csv': 'test_jobs.csv',
            'kuccps_csv': 'test_courses.csv',
            'requirements_json': 'test_requirements.json'
        }
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def tearDown(self):
        """Clean up all created test files."""
        files_to_delete = [
            'test_demand.csv', 'test_skill_map.json', 'test_jobs.csv',
            'test_courses.csv', 'test_requirements.json', 'config.ini'
        ]
        for f in files_to_delete:
            if os.path.exists(f):
                os.remove(f)

    def test_recommendation_logic(self):
        """Test the main recommend method."""
        user_text = "I love coding with python and building websites."
        kcse_results = {
            "mean_grade": "B+",
            "subjects": {"Mathematics": "A", "Physics": "B", "English": "B"}
        }
        
        recommendations = self.recommender.recommend(user_text, kcse_results=kcse_results)
        
        # Assertions
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0, "Should return at least one recommendation")
        
        # Check the structure of the first recommendation
        first_rec = recommendations[0]
        self.assertIn('dept', first_rec)
        self.assertIn('final_score', first_rec)
        self.assertIn('comprehensive_rationale', first_rec)
        self.assertIn('programs', first_rec)
        
        # Check if Technology is the top recommendation
        self.assertEqual(first_rec['dept'], 'Technology')

if __name__ == '__main__':
    unittest.main()