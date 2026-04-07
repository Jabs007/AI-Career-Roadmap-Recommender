import sys
import os
import json
import math
from typing import List, Any, cast, Optional # type: ignore
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.recommender import CareerRecommender # type: ignore

def load_ground_truth():
    """Load evaluation ground truth data."""
    gt_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'evaluation_ground_truth.json')
    with open(gt_path, 'r') as f:
        return json.load(f)

def compute_precision_recall_f1(recommended: List[Any], relevant: List[Any], k: int):
    """Compute precision, recall, F1 at k."""
    if k > len(recommended):
        k = len(recommended)
    recommended_list = cast(list, recommended)
    top_k = recommended_list[:k] # type: ignore
    relevant_set = set(relevant)
    num_relevant = len([r for r in top_k if r in relevant_set])
    precision = num_relevant / k if k > 0 else 0
    recall = num_relevant / len(relevant) if relevant else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1

def compute_ndcg(recommended: List[Any], relevant: List[Any], k: int):
    """Compute NDCG at k for binary relevance."""
    if k > len(recommended):
        k = len(recommended)
    dcg = 0.0
    recommended_list = cast(list, recommended)
    for i, rec in enumerate(recommended_list[:k]): # type: ignore
        rel = 1 if rec in relevant else 0
        dcg += rel / math.log2(i + 2)
    # IDCG: ideal DCG, assuming relevant items are ranked first
    idcg = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant))))
    return dcg / idcg if idcg > 0 else 0

def evaluate_baseline_interest(rec, test_case):
    """Evaluate interest-only baseline."""
    scores = rec.classifier.classify(test_case['student_text'])
    recommended = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return recommended

def evaluate_baseline_market(rec):
    """Evaluate market-only baseline."""
    top_market = rec.demand_df.sort_values('job_count', ascending=False).head(10).index.tolist()
    return top_market

def evaluate_hybrid_scenario():
    """
    Evaluates the full Hybrid Engine on a battery of test profiles with quantitative metrics.
    """
    rec = CareerRecommender()
    ground_truth = load_ground_truth()

    k_values = [1, 3, 5]
    metrics = {k: {'precision': [], 'recall': [], 'f1': [], 'ndcg': []} for k in k_values}

    print("Hybrid Evaluation with Quantitative Metrics")
    print("=" * 60)

    for case in ground_truth:
        print(f"\nEvaluating: {case['id']} - {case['description']}")
        recs = rec.recommend(case['student_text'], top_n=5, kcse_results=case['kcse_results'])
        recommended = [r['dept'] for r in recs]
        relevant = case['relevant_departments']

        print(f"Recommended: {recommended}")
        print(f"Ground Truth: {relevant}")

        for k in k_values:
            p, r, f = compute_precision_recall_f1(recommended, relevant, k)
            n = compute_ndcg(recommended, relevant, k)
            metrics[k]['precision'].append(p)
            metrics[k]['recall'].append(r)
            metrics[k]['f1'].append(f)
            metrics[k]['ndcg'].append(n)
            print(f"@K={k}: P={p:.3f}, R={r:.3f}, F1={f:.3f}, NDCG={n:.3f}")

    # Average metrics
    print("\nAverage Metrics Across All Test Cases:")
    print("-" * 50)
    for k in k_values:
        avg_p = float(sum(metrics[k]['precision'])) / len(metrics[k]['precision'])
        avg_r = float(sum(metrics[k]['recall'])) / len(metrics[k]['recall'])
        avg_f = float(sum(metrics[k]['f1'])) / len(metrics[k]['f1'])
        avg_n = float(sum(metrics[k]['ndcg'])) / len(metrics[k]['ndcg'])
        print(f"@K={k}: Precision={avg_p:.3f}, Recall={avg_r:.3f}, F1={avg_f:.3f}, NDCG={avg_n:.3f}")

def compare_baselines():
    """
    Compare interest-only, market-only, and hybrid baselines.
    """
    rec = CareerRecommender()
    ground_truth = load_ground_truth()

    k = 3  # Use top 3 for comparison
    baselines = {'interest': [], 'market': [], 'hybrid': []}

    print("\nBaseline Comparison @K=3")
    print("=" * 40)

    for case in ground_truth:
        # Interest baseline
        interest_rec = evaluate_baseline_interest(rec, case)
        p_i, r_i, f_i = compute_precision_recall_f1(interest_rec, case['relevant_departments'], k)
        baselines['interest'].append((p_i, r_i, f_i))

        # Market baseline
        market_rec = evaluate_baseline_market(rec)
        p_m, r_m, f_m = compute_precision_recall_f1(market_rec, case['relevant_departments'], k)
        baselines['market'].append((p_m, r_m, f_m))

        # Hybrid
        recs = rec.recommend(case['student_text'], top_n=k, kcse_results=case['kcse_results'])
        hybrid_rec = [r['dept'] for r in recs]
        p_h, r_h, f_h = compute_precision_recall_f1(hybrid_rec, case['relevant_departments'], k)
        baselines['hybrid'].append((p_h, r_h, f_h))

        print(f"{case['id']}: Interest(P={p_i:.3f}, R={r_i:.3f}, F1={f_i:.3f}) | Market(P={p_m:.3f}, R={r_m:.3f}, F1={f_m:.3f}) | Hybrid(P={p_h:.3f}, R={r_h:.3f}, F1={f_h:.3f})")

    # Average
    print("\nAverage Baseline Comparison:")
    for baseline, scores in baselines.items():
        avg_p = float(sum(s[0] for s in scores)) / len(scores)
        avg_r = float(sum(s[1] for s in scores)) / len(scores)
        avg_f = float(sum(s[2] for s in scores)) / len(scores)
        print(f"{baseline.capitalize()}: Precision={avg_p:.3f}, Recall={avg_r:.3f}, F1={avg_f:.3f}")

if __name__ == "__main__":
    evaluate_hybrid_scenario()
    compare_baselines()
