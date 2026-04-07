from typing import Dict, List, Any, cast, Optional, Tuple # type: ignore
from .interest_vectorizer import InterestVectorizer # type: ignore
import torch # type: ignore
import torch.nn.functional as F # type: ignore
from sklearn.metrics.pairwise import cosine_similarity # type: ignore
import numpy as np # type: ignore
import re

class InterestClassifier:
    def __init__(self):
        self.vectorizer = InterestVectorizer()
        self.dept_bert_vectors = self.vectorizer.get_department_bert_vectors()
        self.dept_tfidf_matrix = self.vectorizer.get_department_tfidf_vectors()
        self.departments = self.vectorizer.departments

        # Mutual-exclusion groups: if a strong indicator fires, softly penalise competing depts
        self._signal_groups = [
            # (trigger_keywords, boosted_dept, penalised_depts, boost, penalty)
            (
                ["nurse", "doctor", "physician", "medicine", "hospital", "patient", "surgery",
                 "pharmacy", "dentist", "clinical", "therapist", "pathology"],
                "Healthcare & Medical",
                ["Information Technology", "Engineering", "Finance & Accounting"],
                1.30, 0.60
            ),
            (
                ["software", "app", "mobile", "code", "coding", "programming", "developer",
                 "python", "javascript", "java", "flutter", "react", "backend", "frontend",
                 "devops", "cloud", "cyber", "algorithm", "machine learning", "deep learning"],
                "Information Technology",
                ["Education", "Arts & Media", "Hospitality & Tourism", "Agriculture & Environmental"],
                1.35, 0.50
            ),
            (
                ["data scientist", "data analyst", "big data", "tableau", "power bi",
                 "predictive", "statistics", "visualization", "sql", "data mining"],
                "Data Science & Analytics",
                ["Education", "Hospitality & Tourism", "Agriculture & Environmental"],
                1.30, 0.55
            ),
            (
                ["civil engineer", "structural", "mechanical", "electrical engineer",
                 "construction site", "quantity surveyor", "roads", "bridges"],
                "Engineering",
                ["Information Technology", "Arts & Media"],
                1.25, 0.70
            ),
            (
                ["lawyer", "advocate", "litigation", "court", "law firm", "justice",
                 "constitution", "legal", "paralegal", "judiciary"],
                "Law",
                ["Information Technology", "Healthcare & Medical", "Agriculture & Environmental"],
                1.30, 0.65
            ),
            (
                ["farm", "crop", "soil", "livestock", "agronomy", "horticulture",
                 "irrigation", "agribusiness", "agriculture"],
                "Agriculture & Environmental",
                ["Information Technology", "Finance & Accounting", "Law"],
                1.25, 0.65
            ),
        ]

        # Normalize group dept names (use exact keys from department_keywords)
        self._dept_aliases = {
            "Healthcare & Medical": "Healthcare & Medical",
            "Information Technology": "Information Technology",
            "Data Science & Analytics": "Data Science & Analytics",
            "Engineering": "Engineering",
            "Law": "Law",
            "Agriculture & Environmental": "Agriculture & Environmental",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_signal_groups(self, text_lower: str, scores: Any) -> Any:
        """Soft signal-based rescoring using mutual-exclusion groups."""
        for triggers, boost_dept, penalise_depts, boost_factor, penalty_factor in self._signal_groups:
            hit_count = sum(1 for kw in triggers if kw in text_lower)
            if hit_count == 0:
                continue

            # Graduated strength: 1 hit → 50 % of boost; full boost at 3+ hits
            strength = min(hit_count / 3.0, 1.0)
            effective_boost = 1.0 + (boost_factor - 1.0) * strength
            effective_penalty = 1.0 - (1.0 - penalty_factor) * strength

            if boost_dept in scores:
                scores[boost_dept] *= effective_boost # type: ignore
            for dept in penalise_depts:
                if dept in scores:
                    scores[dept] *= effective_penalty # type: ignore

        return scores

    def _job_description_signal(self, text: str, jobs_df: Any) -> Dict[str, float]:
        """
        Compute a soft third-signal by TF-IDF-matching the student text against
        real job descriptions grouped by DeptNorm.
        Returns a dict {dept: normalised_score}.
        """
        try:
            if jobs_df is None or jobs_df.empty:
                return {}
            if 'Description' not in jobs_df.columns or 'DeptNorm' not in jobs_df.columns:
                return {}

            from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
            from sklearn.metrics.pairwise import cosine_similarity as cos_sim # type: ignore

            grouped = jobs_df.groupby('DeptNorm')['Description'].apply(
                lambda texts: ' '.join(texts.dropna().astype(str).tolist())
            )
            if grouped.empty:
                return {}

            corpus = grouped.tolist()
            labels = grouped.index.tolist()
            all_texts = [text] + corpus

            tfidf = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), sublinear_tf=True)
            mat = tfidf.fit_transform(all_texts)
            query_vec = mat[0]
            dept_vecs = mat[1:]

            sims = cos_sim(query_vec, dept_vecs).flatten()
            max_sim = sims.max() if sims.max() > 0 else 1.0
            return {label: float(sim / max_sim) for label, sim in zip(labels, sims)} # type: ignore
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def classify(self, text: str, bert_weight: float = 0.45, tfidf_weight: float = 0.35,
                 job_signal_weight: float = 0.20, jobs_df: Any = None) -> Dict[str, float]:
        """
        Classifiy student interest text using a THREE-LAYER hybrid engine:
          1. BERT semantic similarity (45 %)
          2. TF-IDF keyword similarity against department keyword corpora (35 %)
          3. TF-IDF against REAL job descriptions from the CSV (20 %)
        After blending, soft mutual-exclusion groups refine the ranking.

        Args:
            text (str): Raw student input
            bert_weight (float): BERT layer weight
            tfidf_weight (float): TF-IDF keyword layer weight
            job_signal_weight (float): Job-description layer weight
            jobs_df: Optional DataFrame with 'DeptNorm' and 'Description' columns
        Returns:
            dict: department → similarity score
        """
        text_lower = text.lower()

        # ── Layer 1: BERT Similarity ──────────────────────────────────
        student_bert = self.vectorizer.vectorize_bert(text)
        bert_scores = {}
        for dept, dept_vector in self.dept_bert_vectors.items():
            s_vec = student_bert.detach().cpu().flatten()
            d_vec = dept_vector.detach().cpu().flatten()
            if s_vec.shape[0] != d_vec.shape[0]:
                bert_scores[dept] = 0.0
                continue
            sim = F.cosine_similarity(s_vec.unsqueeze(0), d_vec.unsqueeze(0))
            bert_scores[dept] = float(sim.item())

        # ── Layer 2: TF-IDF keyword similarity ───────────────────────
        student_tfidf = self.vectorizer.vectorize_tfidf(text)
        tfidf_similarities = cosine_similarity(student_tfidf, self.dept_tfidf_matrix).flatten()
        tfidf_scores = {dept: float(score) for dept, score in zip(self.departments, tfidf_similarities)}

        # ── Layer 3: Real Job-Description semantic match ──────────────
        job_scores = self._job_description_signal(text, jobs_df) if jobs_df is not None else {}

        # ── Blend all three layers ────────────────────────────────────
        final_scores = {}
        for dept in self.dept_bert_vectors:
            b = bert_scores.get(dept, 0.0)
            t = tfidf_scores.get(dept, 0.0)
            j = job_scores.get(dept, 0.0)

            # Recalculate effective weights if job signal is absent
            if not job_scores:
                w_b, w_t, w_j = bert_weight + job_signal_weight * 0.5, tfidf_weight + job_signal_weight * 0.5, 0.0
            else:
                w_b, w_t, w_j = bert_weight, tfidf_weight, job_signal_weight

            score = (w_b * b) + (w_t * t) + (w_j * j)
            final_scores[dept] = score

        # ── Soft signal group rescoring ───────────────────────────────
        final_scores = self._apply_signal_groups(text_lower, final_scores)

        return final_scores


    def get_top_departments(self, text: str, top_n: int = 5, jobs_df: Any = None) -> List[Tuple[str, float]]:
        """Get top N departments by hybrid similarity."""
        scores = self.classify(text, jobs_df=jobs_df)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_n] # type: ignore
