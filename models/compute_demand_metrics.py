import pandas as pd
import os

def compute_demand_metrics(jobs_csv_path="data/myjobmag_jobs.csv", output_path="data/job_demand_metrics.csv"):
    """
    Compute job demand metrics from scraped jobs data.

    Args:
        jobs_csv_path (str): Path to the scraped jobs CSV
        output_path (str): Path to save the metrics CSV

    Returns:
        pd.DataFrame: Demand metrics
    """
    if not os.path.exists(jobs_csv_path):
        raise FileNotFoundError(f"Jobs CSV not found: {jobs_csv_path}")

    df = pd.read_csv(jobs_csv_path)

    # Group by Department and count jobs
    demand_df = df.groupby('Department').size().reset_index(name='job_count')

    # Normalize to get demand score (0-1)
    max_count = demand_df['job_count'].max()
    demand_df['demand_score'] = demand_df['job_count'] / max_count

    # Save to CSV
    demand_df.to_csv(output_path, index=False)

    print(f"Demand metrics saved to {output_path}")
    return demand_df

if __name__ == "__main__":
    compute_demand_metrics()