
import pandas as pd
import os

def clean_kuccps_data():
    raw_file = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\Kuccps\Programmes_with_Departments.csv"
    output_file = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\Kuccps\kuccps_courses.csv"
    
    print(f"Reading raw data from: {raw_file}")
    
    # Read the raw csv
    try:
        # We read all lines first to filter out the embedded headers manually or use pandas logic
        # pandas can handle this if we just read it and then filter rows that repeat the header
        df = pd.read_csv(raw_file, dtype=str) # Read as string to avoid type errors on weird rows
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    original_count = len(df)
    print(f"Original Row Count: {original_count}")

    # The raw file has repeated headers like: "PROG CODE", "INSTITUTION NAME", ...
    # We identify them by checking if a column value matches the header name
    
    # Assume 'Program_Code' is the first column header in the clean version
    # The dirty rows often start with "PROG" or contain "CODE" in the first column
    
    # Filter out rows where the first column is "PROG" or "Program_Code" (except the first one, but pandas read header already)
    # Actually, pandas uses the first row as header. 
    # Subsequent repeated headers will appear as data rows.
    
    # Filter out rows where 'Program_Code' column contains header-like text
    # The invalid rows seem to contain "PROG CODE" or "Program_Code" or "CODE"
    
    # Let's inspect what likely garbage looks like based on file view:
    # Line 56: "PROG"
    # Line 57: "CODE", INSTITUTION NAME...
    
    # We can just filter out rows where 'Institution_Name' is 'INSTITUTION NAME' or 'Institution_Name'
    # The header in file is: Program_Code,Institution_Name,Depertments,Programme_Name,Cutoff_2023,Cutoff_2022,...
    
    # Standardize column names (strip whitespace)
    df.columns = df.columns.str.strip()
    
    # Cleaning criteria: Remove rows where 'Institution_Name' contains 'INSTITUTION NAME' (case insensitive)
    # Also remove rows where 'Program_Code' is null/empty if that's invalid
    
    df_clean = df[
        (~df['Program_Code'].astype(str).str.contains('PROG', na=False, case=False)) &
        (~df['Program_Code'].astype(str).str.contains('CODE', na=False, case=False)) &
        (~df['Institution_Name'].astype(str).str.contains('INSTITUTION NAME', na=False, case=False))
    ].copy()
    
    # Fix the typo 'Depertments' to 'Department' if needed, or keep logic consistent
    # The file has 'Depertments' AND 'Department'. Let's coalesce them.
    if 'Depertments' in df_clean.columns and 'Department' in df_clean.columns:
        # Use Department if available, else Depertments
        df_clean['Department'] = df_clean['Department'].fillna(df_clean['Depertments'])
        # Drop the typo column
        df_clean.drop(columns=['Depertments'], inplace=True)
        print("Fixed 'Depertments' typo column.")
    
    # Rename columns to standard lowercase if preferred, or keep as is.
    # config.ini expects specific columns? The logic usually looks for specific names.
    # Let's clean up column names to be Python friendly
    # But for now, let's strictly fix the "Duplicate Header" issue
    
    final_count = len(df_clean)
    print(f"Cleaned Row Count: {final_count}")
    print(f"Removed {original_count - final_count} garbage rows.")
    
    # Save
    df_clean.to_csv(output_file, index=False)
    print(f"Successfully saved cleaned data to: {output_file}")

if __name__ == "__main__":
    clean_kuccps_data()
