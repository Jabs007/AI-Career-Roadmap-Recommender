import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.recommender import CareerRecommender

def evaluate_hybrid_scenario():
    """
    Evaluates the full Hybrid Engine on a battery of test profiles.
    Compares Interest Score vs. Final Score (Interest + Market).
    """
    rec = CareerRecommender()
    
    test_cases = [
        {
            "id": "Profile_A",
            "text": "I love painting and drawing arts.",
            "desc": "High Artistic Interest, Low Market Demand (Hypothetical)"
        },
        {
            "id": "Profile_B",
            "text": "I want to code software and build apps.",
            "desc": "High Tech Interest, High Market Demand"
        },
        {
            "id": "Profile_C",
            "text": "I like helping people in hospitals.",
            "desc": "High Health Interest, Moderate/High Demand"
        }
    ]
    
    print(f"{'Profile':<15} | {'Description':<40} | {'Top Rec':<25} | {'Interest':<8} | {'Market':<8} | {'Final':<8}")
    print("-" * 120)
    
    for case in test_cases:
        recs = rec.recommend(case['text'], top_n=1)
        if recs:
            top = recs[0]
            print(f"{case['id']:<15} | {case['desc']:<40} | {top['dept']:<25} | {top['interest_score']:.2f}     | {top['demand_score']:.2f}   | {top['final_score']:.2f}")

if __name__ == "__main__":
    evaluate_hybrid_scenario()
