import sys
import os
import pandas as pd

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.recommender import CareerRecommender

def evaluate_market_impact():
    """
    Evaluates the 'Market-Only' baseline. 
    This checks which careers would be recommended purely based on job volume,
    ignoring user interest.
    """
    print("--- Market-Only Baseline Evaluation ---")
    rec = CareerRecommender()
    
    # Get top demand sectors directly
    top_market = rec.demand_df.sort_values('job_count', ascending=False).head(10)
    print("\nTop 10 High-Demand Sectors (Market Signal):")
    print(top_market[['job_count']])
    
    return top_market

if __name__ == "__main__":
    evaluate_market_impact()
