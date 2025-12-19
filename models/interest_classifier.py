from .interest_vectorizer import InterestVectorizer
import torch
import torch.nn.functional as F
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class InterestClassifier:
    def __init__(self):
        self.vectorizer = InterestVectorizer()
        self.dept_bert_vectors = self.vectorizer.get_department_bert_vectors()
        self.dept_tfidf_matrix = self.vectorizer.get_department_tfidf_vectors()
        self.departments = self.vectorizer.departments

    def classify(self, text: str, bert_weight: float = 0.5, tfidf_weight: float = 0.5) -> dict:
        """
        Classify student interest text to career departments using a hybrid BERT + TF-IDF approach.

        Returns similarity scores for each department.

        Args:
            text (str): Raw student input
            bert_weight (float): Weight for BERT semantic similarity
            tfidf_weight (float): Weight for TF-IDF keyword similarity

        Returns:
            dict: department -> similarity score
        """
        # BERT Similarity
        student_bert = self.vectorizer.vectorize_bert(text)
        bert_scores = {}
        for dept, dept_vector in self.dept_bert_vectors.items():
            s_vec = student_bert.detach().cpu().flatten()
            d_vec = dept_vector.detach().cpu().flatten()
            
            if s_vec.shape[0] != d_vec.shape[0]:
                print(f"DEBUG: Mismatch for {dept}: {s_vec.shape[0]} vs {d_vec.shape[0]}")
                bert_scores[dept] = 0.0
                continue
                
            sim = F.cosine_similarity(s_vec.unsqueeze(0), d_vec.unsqueeze(0))
            bert_scores[dept] = float(sim.item())

        # TF-IDF Similarity
        student_tfidf = self.vectorizer.vectorize_tfidf(text)
        tfidf_similarities = cosine_similarity(student_tfidf, self.dept_tfidf_matrix).flatten()
        tfidf_scores = {dept: float(score) for dept, score in zip(self.departments, tfidf_similarities)}

        # Combine Scores
        final_scores = {}
        processed_text = text.lower()
        
        for dept in self.dept_bert_vectors:
            b_score = bert_scores.get(dept, 0.0)
            t_score = tfidf_scores.get(dept, 0.0)
            
            # Combine
            score = (bert_weight * b_score) + (tfidf_weight * t_score)
            
            # CONTEXTUAL DISAMBIGUATION (Heuristics)
            # 1. Tech vs. Construction Disambiguation for "building"
            if "build" in processed_text or "building" in processed_text:
                tech_context = any(w in processed_text for w in ["app", "software", "code", "python", "java", "script", "mobile", "web"])
                if tech_context and dept == "Information Technology":
                    score *= 1.2  # Boost IT if "building" is used in a coding context
                elif tech_context and dept in ["Engineering", "Architecture & Construction"]:
                    score *= 0.6  # Penalize construction depts if context is clearly tech
            
            # 2. Healthcare vs. Science Disambiguation
            if "doctor" in processed_text or "patient" in processed_text:
                if dept == "Healthcare & Medical":
                    score *= 1.1

            final_scores[dept] = score

        return final_scores

    def get_top_departments(self, text: str, top_n: int = 5) -> list:
        """Get top N departments by hybrid similarity."""
        scores = self.classify(text)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_n]
