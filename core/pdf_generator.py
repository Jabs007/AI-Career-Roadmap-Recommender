from fpdf import FPDF # type: ignore
import datetime

def generate_pdf_report(recommendations):
    """Generates a PDF report of the career recommendations using FPDF."""
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)  # Set reasonable margins
    pdf.add_page()

    def clean_text(text):
        """Sanitize text for FPDF compatibility."""
        if not text:
            return ""
        # Ensure text is string and handle potential encoding issues
        try:
            text = str(text).encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            text = str(text)
            
        # Break extremely long words
        from typing import Any
        text_any: Any = text
        words = str(text_any).split(' ')
        cleaned_words = []
        for word in words:
            if len(word) > 40:
                # Use Any for slicing if linter is confused
                word_any: Any = word
                chunks = [str(word_any[i:i+40]) for i in range(0, len(word), 40)] # type: ignore
                cleaned_words.append(" ".join(chunks)) # type: ignore
            else:
                cleaned_words.append(str(word)) # type: ignore
        return " ".join(cleaned_words)

    # Title Header
    pdf.set_fill_color(30, 58, 138)  # Deep Blue
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 20, "Career Success Roadmap", 0, 1, "C", True)
    pdf.ln(5)

    # Introduction
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, "This personalized report analyzes your interest profile and academic results against the current Kenyan job market and KUCCPS requirements.")
    pdf.ln(8)

    # Process each recommendation
    for idx, rec in enumerate(recommendations[:5]):
        # Recommendation Header
        pdf.set_fill_color(241, 245, 249)
        pdf.set_text_color(30, 58, 138)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 12, f" {idx+1}. {clean_text(rec['dept'])}", ln=True, fill=True)
        pdf.ln(4)

        # Basic Stats
        pdf.set_text_color(71, 85, 105)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(60, 8, f"Match Score: {int(rec['final_score']*100)}%")
        pdf.cell(60, 8, f"Market Demand: {rec.get('job_count', 'N/A')} active roles")
        pdf.cell(60, 8, f"Status: {rec.get('dept_status', 'UNKNOWN')}")
        pdf.ln(10)

        # Rationale
        pdf.set_text_color(30, 41, 59)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Strategic Rationale", ln=True)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 5, clean_text(rec.get('comprehensive_rationale', 'No rationale provided.')))
        pdf.ln(4)

        # Eligibility Table
        if 'eligibility' in rec and rec['eligibility']:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Academic Eligibility Breakdown:", ln=True)
            
            for course, elig_data in rec['eligibility'].items():
                status = elig_data.get('status', 'N/A')
                
                pdf.set_fill_color(248, 250, 252)
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 8, f"  > {clean_text(course)}: {status}", ln=True, fill=True)
                
                # Subject Details Table
                if elig_data.get('details'):
                    pdf.set_font("Arial", "B", 8)
                    pdf.set_fill_color(226, 232, 240)
                    pdf.set_x(20)
                    pdf.cell(60, 6, "Requirement", 1, 0, "C", True)
                    pdf.cell(25, 6, "Required", 1, 0, "C", True)
                    pdf.cell(25, 6, "Your Grade", 1, 0, "C", True)
                    pdf.cell(25, 6, "Status", 1, 1, "C", True)
                    
                    pdf.set_font("Arial", "", 8)
                    for detail in elig_data['details']:
                        pdf.set_x(20)
                        pdf.cell(60, 5, clean_text(detail['criterion']), 1)
                        pdf.cell(25, 5, detail['required'], 1, 0, "C")
                        pdf.cell(25, 5, detail['actual'], 1, 0, "C")
                        pdf.cell(25, 5, detail['status'], 1, 1, "C")
                pdf.ln(2)

        # Universities
        if 'university_mapping' in rec and rec['university_mapping']:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 8, "Where to Study:", ln=True)
            pdf.set_font("Arial", "", 9)
            for course, unis in rec['university_mapping'].items():
                if unis:
                    try:
                        # Defensive rendering: Ensure X is at start and use a small width buffer
                        pdf.set_x(15) 
                        u_text = clean_text(f"- {course}: {', '.join(unis[:3])}")
                        pdf.multi_cell(0, 5, u_text)
                    except Exception:
                        pdf.set_x(15)
                        pdf.cell(0, 5, f"- {clean_text(course)}: [University data omitted due to layout constraints]", ln=True)
            pdf.ln(5)

    # Footer
    if pdf.get_y() > 230:
        pdf.add_page()
    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 10, f"Generated by AI Career Recommender on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 0, "C")
    pdf.cell(0, 10, f"Page {pdf.page_no()}", 0, 0, "R")

    return bytes(pdf.output(dest="S"))
