# System Architecture

## High-Level Data Flow

```mermaid
graph TD
    User[Student] -->|Input: Career Dream + Grades| UI[Streamlit Frontend]
    
    subgraph "Backend Logic"
        UI --> NLP[NLP Preprocessing]
        NLP -->|Tokens| Vectorizer[TF-IDF / BERT Engine]
        Vectorizer -->|Interest Score| Recommender[Hybrid Recommender]
        
        DB[(Job Market DB)] -->|Demand Data| Recommender
        Rules[(KUCCPS Rules)] -->|Eligibility Check| Recommender
        
        Recommender -->|Ranked Careers| Strategy[Strategy Engine]
    end
    
    Strategy -->|Roadmap + Advice| UI
    Strategy -->|Degree/Diploma?| Eligibility[Eligibility Filter]
```

## Component Breakdown

1.  **Frontend**: Streamlit-based UI for real-time interaction.
2.  **NLP Pipeline**:
    *   Tokenization & Lemmatization (NLTK)
    *   Vectorization (TF-IDF + BERT fallback)
    *   Similarity Matching (Cosine Similarity)
3.  **Market Engine**:
    *   Scraper (Selenium) -> `scraped_jobs.csv`
    *   Metrics Aggregator -> `job_demand_metrics.csv`
4.  **Eligibility Engine**:
    *   Input: Student Mean Grade + Subject Clusters.
    *   Logic: Compares against `kuccps_requirements.json`.
    *   Output: `ELIGIBLE`, `NOT ELIGIBLE`, `ASPIRATIONAL`.
