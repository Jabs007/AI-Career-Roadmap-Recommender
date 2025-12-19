# AI-Powered Career Path Recommender: Project Analysis & Progress Report

## 🚀 Project Overview
An advanced AI-driven recommendation system designed to align student interests with real-world market demand in Kenya. The system bridges the gap between academic aspirations and industry requirements by mapping user input to KUCCPS programs and live job opportunities.

---

## 🛠 Core Architecture

### 1. NLP & Classification Engine
- **Hybrid Modeling**: Utilizes a blend of **BERT (DistilBERT)** embeddings for semantic understanding and **TF-IDF** for keyword precision.
- **Interest Vectorization**: Features a high-resolution `department_keywords` dictionary covering 20+ career sectors in Kenya.
- **Preprocessing Pipeline**: Includes NLTK-driven tokenization, stopword removal, and lemmatization to ensure high-accuracy matching.

### 2. Recommendation Logic (The Alpha-Beta Model)
- **Primary Scorer**: Uses a weighted formula: `Score = 0.75 * Interest + 0.25 * Market Demand`.
- **Dynamic Pivot**: Automatically shifts weights for uncertain students (Low Signal) to `0.30 * Interest + 0.70 * Market Demand` to prioritize economic stability.
- **Discovery Thresholds**: Implements progressive filtering (0.08 default / 0.02 low-signal) to ensure zero-fail performance.

---

## ✨ Recent Major Updates & Enhancements

### v2.1.0-Premium: Academic Rigor & Transparency (Current)
*   **Explainable AI (XAI)**: Quantitative score breakdown (Interest vs. Market contribution) for Every recommendation.
*   **Confidence Scoring**: Real-time evaluation of input signal strength (High/Medium/Low).
*   **Baseline Benchmarking**: Proof-of-improvement comparison against Interest-only and Market-only primitive models.
*   **Ethical Disclosure**: Built-in awareness of Digital Bias, Urban Centricity, and Informal Sector data gaps.
*   **Advisory Chatbot**: Retrieval-based interactive Layer for personalized career guidance.

## Architecture
- **NLP Engine**: Hybrid BERT (SBERT) + TF-IDF (vector-space model).
- **Recommendation Model**: Alpha-Beta weighted composite scoring.
- **Data Sync**: Automated ETL pipeline from MyJobMag Kenya.
- **UX**: Streamlit-based Glassmorphism interface with Plotly Express visualizations.

### 1. Intelligence & Accuracy
- **Dynamic Discovery Modes**: Integrated a strategy selector allowing users to toggle between **Passion-First** (intrinsic motivation) and **Market-Priority** (job security/salary) modes.
- **Strategy-Aware Rationale**: The AI now generates explanations tailored to the user's chosen discovery mode (e.g., highlighting market volume for career stability).
- **Hybrid Recommendation Weights**: Implemented real-time slider controls to allow manual fine-tuning of Interest vs. Market Demand scores.
- **Resolution of Tensor Mismatch**: Fixed a critical `RuntimeError` by standardizing the dimension of fallback embeddings (768) to match the BERT hidden state layer.

### 2. Premium User Experience (UX)
- **Glassmorphism Design**: Rebuilt the interface with modern glass-morphism aesthetics, using backdrop blurs, vibrant gradients, and premium typography.
- **Live Action Buttons**: Every recommendation now features a **"Search Live Jobs"** button that dynamically generates context-aware vacancy searches for the Kenyan market.
- **Improved Data Visualization**: Enhanced Plotly scatter maps with strategy-based tooltips and dynamic scaling of "Sweet Spot" results.
- **Skill Bridge Visualization**: Re-engineered the academic-to-industry mapping tab with interactive, styled skill categories.

---

## 📊 Market Data Integration
- **Live Scraper Sync**: Data derived from real-time analysis of Kenyan portals (MyJobMag, BrighterMonday) with a live status indicator in the sidebar.
- **KUCCPS Alignment**: Direct mapping of career paths to verified Kenyan university programs.
- **Skill-to-Role Bridge**: Explains exactly how a specific skill (e.g., Clinical Diagnosis) enables a specific role (e.g., Medical Officer).

---

## 🔧 Maintenance & Stability
- **Fixed RuntimeError (Dimension Mismatch)**: Implemented module-level caching and dimension standardization for fallback vectors to prevent crashes during inconsistent BERT model loads.
- **Defensive Similarity Scoring**: Added shape validation in the `InterestClassifier` to gracefully handle embedding failures without crashing the UI.
- **Resolved KeyError**: Fixed market demand key access for "Legal & Compliance."
- **Resolved Plotly ValueError**: Synchronized DataFrame column names for stable visualization.

---

## 📈 Future Roadmap
- [ ] **Real-time API Integration**: Directly connecting to job board APIs for hourly updates.
- [ ] **Student Profile Persistence**: Allowing users to save and track their career evolution.
- [ ] **Advanced Interdisciplinary Matching**: Suggesting double-major or minor combinations for mixed-interest students.