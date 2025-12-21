from fpdf import FPDF
from fpdf.enums import XPos, YPos

def generate_pdf_report(recommendations):
    """Generates a PDF report of the career recommendations using FPDF."""
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)  # Set reasonable margins
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Your Personalized Career Success Plan", 0, 1, "C")
    pdf.ln(10)

    # Introduction
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(
        0,
        6,
        "This report provides a comprehensive analysis of your career prospects based on your interests and academic background. "
        "It includes tailored recommendations, strategic rationale, and actionable steps to guide you toward a successful future."
    )
    pdf.ln(10)

    def clean_text(text):
        """Sanitize text to avoid FPDF errors with long words."""
        if not text:
            return ""
        # Ensure text is string
        text = str(text)
        # Break very long words (e.g. > 50 chars) by inserting spaces
        words = text.split(' ')
        cleaned_words = []
        for word in words:
            if len(word) > 50:
                # Chunk it
                chunks = [word[i:i+50] for i in range(0, len(word), 50)]
                cleaned_words.append(" ".join(chunks))
            else:
                cleaned_words.append(word)
        return " ".join(cleaned_words)

    # Process each recommendation
    for rec in recommendations:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Top Recommendation: {clean_text(rec['dept'])}", 0, 1)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Strategic Rationale", 0, 1)
        pdf.set_font("Arial", "", 11)
        pdf.set_x(15)
        pdf.multi_cell(180, 6, clean_text(rec['comprehensive_rationale']))
        pdf.ln(5)

        # Eligibility
        if 'eligibility' in rec and rec['eligibility']:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Eligibility Status:", 0, 1)
            pdf.set_font("Arial", "", 11)
            for course, details in rec['eligibility'].items():
                status = details.get('status', 'N/A')
                reason = details.get('reason', 'No reason provided')
                line_text = f"- {course}: {status} ({reason})"
                
                # Attempt to print; if it fails, try printing a simplified version
                try:
                    pdf.set_x(15)
                    pdf.multi_cell(180, 6, clean_text(line_text))
                except Exception:
                    # Fallback: Truncate or simplify
                    try:
                        short_text = f"- {course}: {status}"
                        pdf.set_x(15)
                        pdf.multi_cell(180, 6, clean_text(short_text))
                    except Exception:
                        pdf.set_x(15)
                        pdf.multi_cell(180, 6, "Error printing course details.")

            pdf.ln(5)

        # University Mapping
        if 'university_mapping' in rec and rec['university_mapping']:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, "Potential Universities:", 0, 1)
            pdf.set_font("Arial", "", 11)
            for course, universities in rec['university_mapping'].items():
                uni_list = ", ".join(universities[:3])  # Limit to first 3 universities to avoid overflow
                line_text = f"- {course}: {uni_list}"
                try:
                    pdf.set_x(15)
                    pdf.multi_cell(180, 6, clean_text(line_text))
                except Exception:
                    pdf.set_x(15)
                    pdf.multi_cell(180, 6, f"- {course}: [List truncated]")
            pdf.ln(10)

    return bytes(pdf.output(dest="S"))