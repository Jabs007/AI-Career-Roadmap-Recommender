# 🌉 TVET & Diploma Redirection Strategy

This document explains the "Semantic Honesty" approach used to guide students who do not meet initial degree requirements in the AI Career Roadmap Recommender.

## 🥅 Objective
To provide a dignified and actionable "Comeback Plan" for students who miss academic cut-offs, ensuring they see viable pathways rather than simple "Not Eligible" rejections.

## 🛠️ Implementation Logic

### 1. The Redirection Trigger
The system searches for Diploma alternatives if:
- The student is **NOT ELIGIBLE** for any degree in their top department match.
- The student is in the **ASPIRATIONAL** zone (missing degree requirements by 1-2 points).

### 2. Matching Mechanism
The recommender performs a keyword-based search on the `kuccps_requirements.json` file for entries where `level == "Diploma"`.
- It calculates eligibility for these Diplomas using the same rules as Degrees.
- Because Diplomas typically have lower mean grade requirements (e.g., C- rather than C+), students are far more likely to qualify.

### 3. Display in UI
Qualified Diploma pathways are displayed as **"ELIGIBLE (DIPLOMA)"** status.
- The system suggests up to 3 specific programs (e.g., "DIPLOMA IN COMPUTING" for an IT interest).
- The rationale clearly explains that the Diploma is a **Bridge** to a later Degree.

## 🎓 Academic Value
This feature aligns with the **Dignity of Labor** and **Technical Literacy** goals in the Kenyan 2030 Vision, highlighting TVET institutions as high-value entry points for the job market.
