
import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# Add project root to path for local imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Standard imports
try:
    from models.recommender import CareerRecommender # type: ignore
except ImportError:
    # Use Any for fallbacks to avoid linter confusion if path resolution fails
    from typing import Any
    CareerRecommender = Any # type: ignore

try:
    from .job_accessibility_tags import AccessibilityTagStore # type: ignore
    _has_tag_store = True
except (ImportError, ValueError):
    try:
        from accessibility.job_accessibility_tags import AccessibilityTagStore # type: ignore
        _has_tag_store = True
    except Exception:
        _has_tag_store = False
        from typing import Any
        AccessibilityTagStore = Any # type: ignore


@dataclass
class AccessibilityRequirement:
    feature: str
    priority: str = "medium"
    category: str = "physical"
    is_negotiable: bool = True
    alternatives: List[str] = field(default_factory=list)


class InclusiveRecommender:
    """
    Enhanced recommender that:
    1. Proactively searches for KUCCPS programs designed for disabled applicants.
    2. Injects a "Specialized Inclusive Pathways" card at the top of results.
    3. Boosts accessible career fields using an Accessibility Fit score.
    """

    # Keywords used to identify disability-specific programs in KUCCPS
    IMPAIRED_KEYWORDS = ["IMPAIRED", "DISABLED", "SPECIAL NEEDS", "SNE"]

    # Which departments naturally support which accessibility features
    DEPT_ACCESSIBILITY_MAP = {
        "Information Technology":    ["remote_work", "screen_reader_compatible", "flexible_schedule", "quiet_workspace"],
        "Data Science & Analytics":  ["remote_work", "flexible_schedule", "quiet_workspace"],
        "Business":                  ["flexible_schedule", "wheelchair_accessible", "accessible_restroom"],
        "Finance & Accounting":      ["flexible_schedule", "wheelchair_accessible"],
        "Education":                 ["structured_tasks", "sign_language_interpreter", "wheelchair_accessible"],
        "Healthcare & Medical":      ["sign_language_interpreter", "accessible_restroom", "wheelchair_accessible"],
        "Social Sciences & Community": ["flexible_schedule", "sign_language_interpreter"],
        "Law":                       ["screen_reader_compatible", "wheelchair_accessible"],
        "Marketing & Sales":         ["remote_work", "flexible_schedule"],
    }

    def __init__(self, base_recommender: Optional[Any] = None):
        # Base recommender initialization
        if base_recommender is not None:
            self.recommender = base_recommender
        else:
            # Type ignore to satisfy linter if import was fuzzy
            self.recommender = CareerRecommender() # type: ignore
            
        self.requirements: List[AccessibilityRequirement] = []
        self.disability_type: Optional[str] = None
        # Use defensive check for the store class
        if _has_tag_store and callable(AccessibilityTagStore):
            self.tag_store = AccessibilityTagStore()
        else:
            self.tag_store = None

    def set_accessibility_requirements(self, requirements: List[AccessibilityRequirement]):
        """Set the user's specific accessibility needs."""
        self.requirements = requirements

    def set_disability_type(self, disability_type: str):
        """Set the user's disability type for specialized KUCCPS matching."""
        self.disability_type = disability_type

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC: Main entry point
    # ─────────────────────────────────────────────────────────────────────────
    def recommend(self, student_text: str, top_n: int = 5, alpha: float = 0.75, 
                  beta: float = 0.25, kcse_results: Optional[Dict] = None, **kwargs) -> List[Dict]:
        """
        Produce inclusive recommendations.

        Steps:
          1. Run the standard recommender to get a broad candidate list.
          2. Scan KUCCPS for programs tagged for disabled/impaired applicants and check
             if the student actually qualifies for them.
          3. If any found, inject a high-priority "Specialized Inclusive Pathways" card.
          4. Re-score every recommendation with an Accessibility Fit component.
          5. Return top_n sorted results.
        """
        # Step 1 – base recommendations (fetch extra so we can re-rank)
        base_recs = self.recommender.recommend(
            student_text, top_n=top_n * 2, alpha=alpha, beta=beta, kcse_results=kcse_results, **kwargs
        )

        # Step 2 – find disability-specific KUCCPS programmes
        special_progs = self._find_inclusive_programmes(kcse_results)

        # Step 3 – build inclusive rec list
        inclusive_recs: List[Dict] = []

        # (a) Inject specialised card at the front if any matches found
        if special_progs:
            prog_list_str = "\n".join(
                f"• {name} ({info['level']})" for name, info in special_progs.items()
            )
            special_card = {
                "dept": "♿ Specialized Inclusive Pathways",
                "dept_status": "ELIGIBLE (SPECIAL)",
                "final_score": 0.97,
                "interest_score": 0.95,
                "demand_score": 0.80,
                "accessibility_fit": 1.0,
                "confidence": "High",
                "job_count": "Specially Adapted Roles",
                "why_best": (
                    "These KUCCPS programmes are specifically designed for applicants with "
                    "disabilities. They have adapted entry requirements AND campus environments. "
                    f"You are **ELIGIBLE** for {len(special_progs)} of them:\n\n{prog_list_str}"
                ),
                "eligibility": special_progs,
                "university_mapping": {},
            }
            inclusive_recs.append(special_card)

        # (b) Re-score standard recommendations
        for rec in base_recs:
            acc_score = self._calculate_accessibility_fit(rec)
            
            # If actual job tags are available, we can augment the score
            if self.tag_store:
                verified_match_rate = self._get_verified_match_rate(rec)
                if verified_match_rate > 0:
                    # Verified matches are worth more than heuristic maps
                    acc_score = (acc_score * 0.7) + (verified_match_rate * 0.3)
            
            orig_match = float(rec.get("final_score", 0.0))
            if self.requirements:
                # Avoid round() which is causing linter issues in this environment
                final_val = float(orig_match * 0.8 + acc_score * 0.2)
                rec["final_score"] = int(final_val * 1000) / 1000.0
            rec["accessibility_fit"] = int(float(acc_score) * 1000) / 1000.0
            inclusive_recs.append(rec)

        # Step 4 – sort and trim
        inclusive_recs.sort(key=lambda x: float(x.get("final_score", 0.0)), reverse=True)
        return [inclusive_recs[i] for i in range(min(len(inclusive_recs), top_n))]

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    def _find_inclusive_programmes(self, kcse_results: Optional[Dict]) -> Dict:
        """
        Scan kuccps_requirements for programmes explicitly designed for
        disabled/impaired students and return those the student qualifies for.
        """
        if not self.disability_type or not kcse_results:
            return {}

        matches: Dict = {}
        for prog_name, req in self.recommender.kuccps_requirements.items():
            if any(kw in prog_name.upper() for kw in self.IMPAIRED_KEYWORDS):
                status, reason, _ = self.recommender.check_eligibility(prog_name, kcse_results)
                if status in ("ELIGIBLE", "ASPIRATIONAL"):
                    matches[prog_name] = {
                        "status": f"ELIGIBLE (INCLUSIVE)" if status == "ELIGIBLE" else "ASPIRATIONAL (INCLUSIVE)",
                        "reason": reason,
                        "level": req.get("level", "Degree"),
                    }
        return matches

    def _calculate_accessibility_fit(self, rec: Dict) -> float:
        """
        Score how well a career department fits the student's accessibility
        requirements.  Returns a value between 0.0 and 1.0.
        """
        if not self.requirements:
            return 1.0

        dept = rec.get("dept", "")
        supported_features = self.DEPT_ACCESSIBILITY_MAP.get(dept, [])

        total = len(self.requirements)
        if total == 0:
            return 1.0

        score = 0.0
        for req in self.requirements:
            if req.feature in supported_features:
                score += 1.0
            elif req.is_negotiable:
                score += 0.4  # partial credit for negotiable needs

        return min(score / total, 1.0)

    def _get_verified_match_rate(self, rec: Dict) -> float:
        """
        Calculates how many verified jobs in this department match the 
        student's requirements.
        """
        if not self.tag_store or not self.requirements:
            return 0.0

        dept = rec.get("dept", "")
        required_features = [req.feature for req in self.requirements]
        
        # In a real system, we'd filter jobs by department AND requirement.
        # Here we check if the store has jobs matching these features.
        matching_tags = []
        # Explicit assertion for linter
        tag_store = self.tag_store
        if tag_store is not None:
             matching_tags = tag_store.find_jobs_with_features(required_features) # type: ignore
        
        if not matching_tags:
            return 0.0
            
        # Simplified: Check if any matches belong to this dept
        # This assumes we can cross-reference job_id back to dept from the recommender
        # For now, return a basic ratio to signify "verified data exists"
        return min(len(matching_tags) / 10, 1.0)
