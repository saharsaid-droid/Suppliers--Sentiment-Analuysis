import os
import pandas as pd
import regex as re
import numpy as np
from logging_confg import setup_logger

logger = setup_logger("preprocess_text")


def preprocess_text_batch(df, col_name, batch_number, output_dir=None):
    """
    Cleans and preprocesses a single batch of Arabic text data, drops empty rows,
    and saves the batch to CSV.

    Args:
        df (pandas.DataFrame): Input batch DataFrame.
        col_name (str): Name of the column containing the text.
        batch_number (int): Number of the batch (used for file naming).
        output_dir (str): Directory to save the cleaned batch. If None, uses default path.

    Returns:
        str: Path to the saved cleaned batch CSV.
    """
    if output_dir is None:
        output_dir = os.path.join(
            os.path.dirname(__file__), "..", "project", "output", "clean_batches"
        )

    logger.info(f"Starting preprocessing for batch {batch_number}.")

    if df is None or df.empty:
        logger.error("The input DataFrame is empty or None.")
        raise ValueError("The input DataFrame is empty or None.")
    if not isinstance(col_name, str) or col_name not in df.columns:
        logger.error(f"Invalid or missing column name: {col_name}")
        raise KeyError(
            f"The specified column '{col_name}' does not exist in the DataFrame."
        )

    # --- Text cleaning ---
    df = df.drop_duplicates().copy()
    df["clean_review"] = df[col_name].apply(
        lambda x: re.sub(r"[^ء-ي\s]", "", str(x)).strip()
    )
    df["clean_review"] = df["clean_review"].str.replace("\n", "", regex=False)
    df["clean_review"] = df["clean_review"].replace(r"^\s*$", np.nan, regex=True)

    # --- Drop empty rows ---
    df = df.dropna(subset=["clean_review"]).reset_index(drop=True)
    if df.empty:
        logger.warning(f"Batch {batch_number} is empty after cleaning.")
    logger.info(f"Batch {batch_number} cleaned. Remaining rows: {len(df)}")

    # --- Save batch ---
    os.makedirs(output_dir, exist_ok=True)
    batch_file = os.path.join(output_dir, f"cleaned_batch_{batch_number}.csv")
    df.to_csv(batch_file, index=False)
    logger.info(f"Batch {batch_number} saved at: {batch_file}")

    return batch_file
