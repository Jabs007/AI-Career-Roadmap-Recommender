# 🔮 Project Roadmap & Future Improvements

This document outlines the planned technical and documentation enhancements to bring the AI Career Roadmap Recommender to a fully robust, academic standard.

## 🚧 A. Strengthen Test Coverage
To ensure system reliability and reproducibility:
- [ ] **Eligibility Logic Tests**: Create unit tests in `tests/test_eligibility.py` using dummy KCSE inputs (e.g., "All As", "All Cs") to verify the `check_eligibility` function's filtering accuracy.
- [ ] **Interest Classification Tests**: Benchmark the NLP engine against a labeled dataset of "Career Dreams" to verify correct department mapping.
- [ ] **Baseline vs. Hybrid Tests**: Automated checks to confirm that the Hybrid Model produces different (and higher quality) rankings than simple Interest-Only baselines.

## 📊 B. Advanced Evaluation Metrics
To strengthen the academic rigor of the project (Chapter 4):
- [ ] **Create `evaluations/` Module**:
    - `eval_interest_baseline.py`: Measure raw TF-IDF matching performance.
    - `eval_market_baseline.py`: Measure demand-based ranking performance.
    - `eval_hybrid.py`: Compare the fused score against single-objective models.
- [ ] **Refine Metrics**: Implement standard Information Retrieval metrics:
    - **Precision@k**: Relevance of top k recommendations.
    - **Recall**: Ability to find all relevant paths.
    - **Rank Correlation**: Consistency of rankings across different inputs.

## 📐 C. Visual Documentation & Architecture
To improve clarity for assessment panels:
- [ ] **System Architecture Diagram**: Create `docs/system_architecture.png` illustrating the end-to-end pipeline:
    `User Input (KCSE + Text) -> NLP Engine -> Eligibility Filter -> Market Analyzer -> UI Pipeline (Streamlit)`
- [ ] **Data Flow Graph**: Visualizing how data moves from `scraped_jobs.csv` and `kuccps_courses.csv` into the `CareerRecommender` class.

## 📸 D. Expanded Example Scenarios
To help reviewers understand system behavior without running code, we will add a "Gallery of Scenarios" to the README:
- [ ] **"The Eligible Student"**: Screenshots/Logs showing a clear Degree path.
- [ ] **"The Aspirational Student"**:  Outputs showing "Missed by 1 point" messages and bridging options.
- [ ] **"The Recovery Strategy"**: Full outputs ensuring "Not Eligible" results dignifiedly pivot to Diploma/TVET options.

## ⚠️ E. Ethical Disclaimers (Completed)
- [x] **Referential Data Warning**: Explicitly state that recommendations are based on historical data and do not guarantee placement.
- [x] **Independent Verification**: Advise users to cross-check with the official KUCCPS portal.
