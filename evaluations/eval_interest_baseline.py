import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.recommender import CareerRecommender

def evaluate_interest_baseline():
    """
    Evaluates the 'Interest-Only' baseline.
    This simulates recommendations based PURELY on user text similarity,
    ignoring market demand and eligibility constraints.
    """
    print("--- Interest-Only Baseline Evaluation ---")
    rec = CareerRecommender()
    
    test_inputs = [
        "I love coding and building software.",
        "I want to help sick people in hospitals.",
        "I am good at math and money management."
    ]
    
    print(f"{'Input Text':<45} | {'Predicted Interest':<25} | {'Score':<5}")
    print("-" * 85)
    
    for text in test_inputs:
        # We only really care about the classifier output here
        # But we can access it via the recommender's classifier
        scores = rec.classifier.classify(text)
        top_dept = max(scores, key=scores.get)
        print(f"{text:<45} | {top_dept:<25} | {scores[top_dept]:.2f}")

if __name__ == "__main__":
    evaluate_interest_baseline()
