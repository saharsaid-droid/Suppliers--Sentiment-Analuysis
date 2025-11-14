import os
import yaml
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from logging_confg import setup_logger

logger = setup_logger("predict_sentiment_batches")


def load_yaml_config(yaml_path):
    """Load configuration from a YAML file."""
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg
    except Exception as e:
        logger.warning(f"Could not read YAML file {yaml_path}: {e}")
        return {}


def get_output_dir(output_dir=None, yaml_path=None):
    """Determine the output directory from argument, YAML, or default."""
    if output_dir:
        return output_dir
    if yaml_path:
        cfg = load_yaml_config(yaml_path)
        yaml_dir = cfg.get("paths", {}).get("predict_batches_dir")
        if yaml_dir:
            return yaml_dir
    # Default path relative to project
    return os.path.join(
        os.path.dirname(__file__), "..", "project", "output", "predict_batches"
    )


def predict_sentiment_batch(
    df: pd.DataFrame,
    model_dir: str,
    tokenizer_dir: str,
    batch_number: int,
    output_dir: str = None,
    yaml_path: str = None,
    text_column: str = "clean_review",
) -> pd.DataFrame:
    """
    Predict sentiment for a batch and save to output_dir.

    Args:
        df: Cleaned DataFrame batch.
        model_dir: Path to fine-tuned model.
        tokenizer_dir: Path to tokenizer.
        batch_number: Batch number for saving.
        output_dir: Optional directory to save predictions.
        yaml_path: Optional YAML config path to read output_dir.
        text_column: Column name containing text.

    Returns:
        DataFrame with predicted sentiments.
    """
    if df.empty:
        logger.warning(f"Batch {batch_number} is empty. Skipping prediction.")
        return df

    output_dir = get_output_dir(output_dir, yaml_path)
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)

        df = df.dropna(subset=[text_column])
        texts = df[text_column].astype(str).tolist()
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)
            preds = torch.argmax(outputs.logits, dim=1)

        label_map = {0: "سلبي", 1: "محايد", 2: "إيجابي"}
        df["predicted_sentiment"] = [
            label_map.get(p.item(), "غير معروف") for p in preds
        ]

        # Save batch
        output_path = os.path.join(output_dir, f"batch_{batch_number}.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        logger.info(f"Batch {batch_number} saved successfully at: {output_path}")

        return df

    except Exception as e:
        logger.exception(f"Error predicting batch {batch_number}: {e}")
        raise
