
import pdfplumber # type: ignore
import pandas as pd # type: ignore
import json
import re
import os
from typing import cast, Any, List, Optional # type: ignore

def extract_2024_cutoffs(pdf_path):
    print(f"Extracting 2024 cutoffs from {pdf_path}...")
    data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                
                header = None
                for row in table:
                    if row and any('PROG CODE' in str(cell).upper() for cell in row):
                        header = row
                        break
                
                if not header:
                    continue
                
                header_list = cast(List[Any], header)
                try:
                    code_idx = [i for i, text in enumerate(header_list) if text and 'PROG' in text.upper() and 'CODE' in text.upper()][0]
                    cutoff_2024_idx = [i for i, text in enumerate(header_list) if text and '2024' in text.upper()][0]
                    
                    for row in table:
                        if not row or row == header:
                            continue
                        code = str(row[code_idx]).strip().replace('\n', '')
                        if code.isdigit():
                            cutoff_2024 = str(row[cutoff_2024_idx]).strip().replace('\n', '')
                            data.append({'Program_Code': code, 'Cutoff_2024': cutoff_2024})
                except Exception:
                    continue
    except Exception as e:
        print(f"Error reading cutoff PDF: {e}")
    return pd.DataFrame(data)

def extract_2025_programmes(pdf_path):
    print(f"Extracting 2025 programmes from {pdf_path}...")
    data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                
                header = None
                for row in table:
                    if row and any('PROG CODE' in str(cell).upper() for cell in row):
                        header = row
                        break
                
                if not header:
                    continue
                
                header_list = cast(List[Any], header)
                try:
                    code_idx = [i for i, text in enumerate(header_list) if text and 'PROG' in text.upper() and 'CODE' in text.upper()][0]
                    inst_idx = [i for i, text in enumerate(header_list) if text and 'INSTITUTION' in text.upper()][0]
                    prog_idx = [i for i, text in enumerate(header_list) if text and 'PROGRAMME' in text.upper()][0]
                    cutoff_23_idx = [i for i, text in enumerate(header_list) if text and '2023' in text.upper()][0]
                    cutoff_22_idx = [i for i, text in enumerate(header_list) if text and '2022' in text.upper()][0]
                    subj_indices = [i for i, text in enumerate(header_list) if text and 'SUBJECT' in text.upper()]
                    
                    for row in table:
                        if not row or row == header:
                            continue
                        code = str(row[code_idx]).strip().replace('\n', '')
                        if code.isdigit():
                            entry = {
                                'Program_Code': code,
                                'Institution_Name': str(row[inst_idx]).strip().replace('\n', ' '),
                                'Programme_Name': str(row[prog_idx]).strip().replace('\n', ' '),
                                'Cutoff_2023': str(row[cutoff_23_idx]).strip().replace('\n', ''),
                                'Cutoff_2022': str(row[cutoff_22_idx]).strip().replace('\n', ''),
                            }
                            for i, s_idx in enumerate(subj_indices): # type: ignore
                                if s_idx < len(row):
                                    entry[f'Subject_{i+1}'] = str(row[s_idx]).strip().replace('\n', ' ') # type: ignore
                                else:
                                    entry[f'Subject_{i+1}'] = ''
                            
                            data.append(entry)
                except Exception:
                    continue
    except Exception as e:
        print(f"Error reading programme PDF: {e}")
    return pd.DataFrame(data)

def extract_tvet_requirements(pdf_path):
    print(f"Extracting TVET requirements from {pdf_path}...")
    data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table:
                    continue
                
                # identify if it has the '#' column
                # The table might span multiple pages without header
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    
                    row_list = cast(List[Any], row)
                    # Skip header-like rows
                    row_str = " ".join([str(c) for c in row_list if c]).upper()
                    if 'PROGRAMME' in row_str and 'CATEGORY' in row_str:
                        continue
                    
                    # Detect offset
                    offset = 0
                    if str(row_list[0]).strip().isdigit() or not row_list[0]:
                        offset = 1
                    
                    if len(row_list) < 4 + offset:
                        continue

                    category = str(row_list[0+offset]).strip().replace('\n', ' ')
                    level = str(row_list[1+offset]).strip().replace('\n', ' ')
                    min_grade = str(row_list[2+offset]).strip().replace('\n', ' ')
                    subj_req_raw = str(row_list[3+offset]).strip().replace('\n', ' ')
                    
                    if not category or category.isdigit() or category.upper() == 'NONE':
                        continue

                    if level and min_grade:
                        name = f"{level.upper()} IN {category.upper()}"
                        
                        # Better Subject Splitting
                        # Identify pairs like "SUBJECT(S) - GRADE"
                        # Common pattern: ... - [GRADE] ...
                        # We look for grades like "C plain", "D (minus)", "C+" etc.
                        # Then we know the text before it is the subject.
                        
                        # Find all occurrences of " - [Grade pattern]"
                        # Grade patterns: [A-E]\s+(?:\(plain\)|\(minus\)|\(plus\))|[A-E][+-]?|[A-E]\s+plain
                        grade_regex = r'([A-E]\s+(?:\(plain\)|\(minus\)|\(plus\))|[A-E][+-]?|[A-E]\s+plain)'
                        matches = list(re.finditer(r'\s*-\s*' + grade_regex, subj_req_raw))
                        
                        subj_slots = {'Subject_1': subj_req_raw, 'Subject_2': '', 'Subject_3': '', 'Subject_4': ''}
                        
                        if matches:
                            subjects = []
                            last_pos = 0
                            for m in matches:
                                start = m.start()
                                end = m.end()
                                # The subject is everything before the dash, 
                                # starting from the end of the previous match
                                subj_part = subj_req_raw[last_pos:start].strip() # type: ignore
                                grade_part = m.group(1).strip()
                                if subj_part:
                                    # Clean up subj_part if it ends with "MATH" etc.
                                    subjects.append(f"{subj_part}: {grade_part}")
                                last_pos = end
                            
                            for i, s in enumerate(subjects[:4]): # type: ignore
                                subj_slots[f'Subject_{i+1}'] = s
                        
                        data.append({
                            'Program_Code': (str('TVET_') + re.sub(r'\W+', '', category) + "_" + level[:3].upper()), # type: ignore
                            'Institution_Name': 'Multiple TVET Institutions',
                            'Programme_Name': name,
                            'Cutoff_2023': '-',
                            'Cutoff_2022': '-',
                            'Cutoff_2024': '-',
                            'Department': category,
                            **subj_slots
                        })
    except Exception as e:
        print(f"Error reading TVET PDF: {e}")
    return pd.DataFrame(data)

def update_brain():
    prog_pdf = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\Kuccps\DEGREE_PROGRAMMES_2025.pdf"
    cutoff_pdf = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\Kuccps\DEGREE_CUTOFFS_14-07-2025.pdf"
    tvet_pdf = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\Kuccps\TVET_CLUSTER_DOCUMENT_2025.pdf"
    csv_path = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\Kuccps\kuccps_courses.csv"
    output_csv = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\Kuccps\kuccps_courses_2025_updated.csv"
    
    # 1. Extract 2025 Programmes
    df_2025 = extract_2025_programmes(prog_pdf)
    
    # 2. Extract 2024 Cutoffs
    df_2024 = extract_2024_cutoffs(cutoff_pdf)
    
    # 3. Extract TVET
    df_tvet = extract_tvet_requirements(tvet_pdf)
    
    # 4. Merge/Concat
    if not df_2025.empty:
        df = df_2025
        print(f"Extracted {len(df_2025)} 2025 programmes.")
        # Add Department column if missing (logic to infer can be added later)
        if 'Department' not in df.columns:
            df['Department'] = 'Unknown'
    else:
        print("Warning: Base extraction failed. Using original CSV structure if it exists.")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Ensure we don't have duplicate cutoff columns
            if 'Cutoff_2024' in df.columns: df.drop(columns=['Cutoff_2024'], inplace=True)
        else:
            df = pd.DataFrame()

    if not df.empty and not df_2024.empty:
        df = df.merge(df_2024.drop_duplicates('Program_Code'), on='Program_Code', how='left')
        print(f"Merged {len(df_2024)} 2024 cutoffs.")
    
    if not df_tvet.empty:
        df = pd.concat([df, df_tvet], ignore_index=True)
        print(f"Added {len(df_tvet)} TVET entries.")

    # 5. Save
    if not df.empty:
        df.to_csv(output_csv, index=False)
        print(f"Successfully saved updated brain data to: {output_csv}")
        
        # Backup and replace original
        if os.path.exists(csv_path):
            if os.path.exists(csv_path + ".bak"):
                os.remove(csv_path + ".bak")
            os.rename(csv_path, csv_path + ".bak")
        os.rename(output_csv, csv_path)
        print("Updated master kuccps_courses.csv")
    else:
        print("Error: No data extracted.")

if __name__ == "__main__":
    update_brain()
