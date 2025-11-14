import os
import pandas as pd
from logging_confg import setup_logger

logger = setup_logger("extract_data")


def extract_batch(
    file_name,
    batch_number=1,
    batch_size=500,
    raw_data_dir=None,
    output_dir=None,
):
    """
    Extracts a single batch from a CSV file and saves it to output_dir.
    Returns the path of the saved batch CSV.

    Parameters:
    - file_name: str, name of CSV file
    - batch_number: int, which batch to extract
    - batch_size: int, size of batch
    - raw_data_dir: str, directory of raw CSV files (default: ../Data/raw)
    - output_dir: str, directory to save batch CSV (default: ./output/temp_batches)
    """

    # use default directories if none provided
    if raw_data_dir is None:
        raw_data_dir = os.path.join(os.path.dirname(__file__), "..", "Data", "raw")
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(__file__), "..", "project", "output", "temp_batches"
        )

    os.makedirs(output_dir, exist_ok=True)

    # build file path
    file_path = os.path.join(raw_data_dir, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} does not exist")

    # read data
    df = pd.read_csv(file_path)

    start = (batch_number - 1) * batch_size
    end = start + batch_size
    batch_df = df.iloc[start:end].copy()

    if batch_df.empty:
        logger.warning(
            f"Batch {batch_number} is empty. Check batch_number and batch_size."
        )

    # save batch to CSV
    batch_file = os.path.join(output_dir, f"batch_{batch_number}.csv")
    batch_df.to_csv(batch_file, index=False)

    logger.info(f"Batch {batch_number} saved to {batch_file}")

    return batch_file
