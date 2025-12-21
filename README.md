# 🎓 AI Career Roadmap Recommender (Kenyan Edition)

> **Bridging the gap between KCSE results, personal passion, and market reality.**

This application is a specialized **Decision Support System (DSS)** designed for Kenyan students negotiating the transition from High School (KCSE) to Higher Education (University/TVET). Unlike standard portals that only list courses, this AI-powered tool acts as a strategic career planner, aligning academic performance with professional ambitions and current economic demands.

## 🚀 Key Features

*   **🧠 Intelligent Career Matching**: Uses NLP semantic analysis to map a student's unstructured "Career Dreams" text to over 1,500+ KUCCPS programs.
*   **⚖️ Automatic Eligibility Check**: Instantly validates KCSE Cluster Requirements (Subject-specific grades) against real KUCCPS/University criteria, flagging "Eligible," "Aspirational," or "Not Eligible" paths.
*   **🛡️ Recovery & Redirection Strategy**: For students who miss degree cut-offs, the system provides "Semantic Honesty"—offering dignified, viable Diploma and TVET bridges rather than false hope.
*   **📊 Market-Driven Insights**: Hybird recommendation logic weights results not just by interest but by **Live Job Market Demand** (scraped from platforms like MyJobMag and BrighterMonday).
*   **🛤️ Strategic Roadmaps**: Generates actionable 4-step plans: *Academic Foundation -> Skill Acquisition -> Professional Registration -> Market Entry*.
*   **💬 AI Career Advisor**: Built-in chatbot for instant guidance on salaries, skills, and industry trends (Offline/Local inference).

## 🛠️ Technology Stack

*   **Frontend**: [Streamlit](https://streamlit.io/) (Python-based interactive web UI).
*   **Backend Logic**: Python 3.10+.
*   **Data Processing**: Pandas, NumPy.
*   **Recommendation Engine**: TF-IDF Vectorization & Cosine Similarity (Scikit-learn).
*   **Visualization**: Plotly Interactive Charts.
*   **ETL Pipeline**: Selenium (for job market data scraping).

## 📂 Project Structure

```bash
├── app.py                     # Main Streamlit application entry point
├── models/
│   ├── recommender.py         # Core hybrid recommendation engine
│   └── nlp_preprocessing.py   # Text cleaning and vectorization logic
├── Kuccps/
│   ├── kuccps_requirements.json # Rules engine for grade validation
│   └── kuccps_courses.csv       # Database of unversity programs
├── data/
│   └── scraped_jobs.csv       # Real-time job market data
├── etl/                       # Scripts for scraping job boards
└── requirements.txt           # Python dependencies
```

## ⚡ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/Jabs007/AI-Career-Roadmap-Recommender.git
    cd AI-Career-Roadmap-Recommender
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

5.  **🔄 Update Job Market Data (Optional)**
    
    To get the latest job market data for more accurate recommendations:
    ```bash
    python update_jobs.py
    ```
    
    This automatically:
    - Scrapes fresh jobs from MyJobMag Kenya
    - Updates demand metrics
    - Refreshes the recommendation engine
    
    💡 **Tip**: Set up daily automated updates! See [`docs/AUTO_UPDATE_GUIDE.md`](docs/AUTO_UPDATE_GUIDE.md) for details.

## 🔍 How It Works

1.  **Phase 1: Academic Identity**: User enters their KCSE Mean Grade and specific subject scores (Math, Eng, Sciences, etc.).
2.  **Phase 2: Vision**: User describes their dream career in plain English (e.g., *"I want to build apps that help farmers"*).
3.  **Analysis**:
    *   The **NLP Engine** finds courses semantically related to "building apps" and "farmers".
    *   The **Eligibility Engine** filters these courses against the user's Math/Science grades.
    *   The **Market Engine** boosts courses with high job vacancy counts.
4.  **Result**: A prioritized list of Degree or Diploma options, complete with a "Skill Bridge" and "Professional Roadmap."

## 🏗️ System Architecture

For a detailed visual breakdown of the NLP pipeline, Hybrid Engine, and Eligibility Filter, please see our [Architecture Documentation](docs/architecture.md).

## 📸 Example Scenarios

The system dynamically adapts its output based on the student's eligibility status:

| Student Profile | Input | System Result | Strategy |
| :--- | :--- | :--- | :--- |
| **Grade A (Premium)** | "I want to be a doctor." | **Eligible**: Bachelor of Medicine | **Professional Roadmap**: Internships, KMA Registration. |
| **Grade C (Average)** | "I want to be a doctor." | **Not Eligible**: Medicine | **Recovery**: Suggests *Diploma in Clinical Medicine* as a bridge. |
| **Grade B (Aspirational)** | "I want to study CS." | **Aspirational**: Computer Science | **Gap Analysis**: "You missed Math Requirement by 1 point. Consider a Bridging Course." |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## ⚠️ Disclaimer

*   **Referential Data**: Recommendations are based on historical KUCCPS data and scraped market trends. They do not guarantee university placement or employment.
*   **Independent Verification**: Users should always cross-check requirements with the official [KUCCPS Portal](https://students.kuccps.net/).

## 📝 License

This project is open-source and available under the MIT License.
