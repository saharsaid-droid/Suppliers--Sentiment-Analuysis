import os
import sys
import yaml
import traceback

# Ensure imports work across folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Load configuration ---
confg_path = os.path.join(os.path.dirname(__file__), "../config/setting.yaml")
with open(confg_path, "r", encoding="utf-8") as file:
    confg = yaml.safe_load(file)

# --- Import pipeline components ---
import extract_data
import transform_data
from scripts import model_utilies
import load_data
from alert_system import load_negative_reviews_alerts, send_alert_emails

# --- Logger setup ---
from logging_confg import setup_logger

etl_logger = setup_logger("etl_logger")


def run_etl():
    """
    Executes the full ETL (Extract, Transform, Load) pipeline for Arabic product reviews.
    All stages are logged to file via `logger_config`.
    """
    etl_logger.info("ETL process started")

    try:
        # === 1. Extract ===
        etl_logger.info("Starting data extraction...")
        extracted_data = extract_data.extract_data("Amazon_reviews.csv")
        etl_logger.info(
            f"Extraction completed. Records extracted: {len(extracted_data)}"
        )

        # === 2. Transform ===
        etl_logger.info("Starting data transformation...")
        transformed_data = transform_data.preprocess_text(extracted_data, "Review")
        clean_path = os.path.join("Data", "clean", "cleaned_Amazon_reviews.csv")
        transformed_data.to_csv(clean_path, index=False)
        etl_logger.info(f"Data cleaned and saved to: {clean_path}")

        # === 3. Predict ===
        etl_logger.info("Starting sentiment prediction...")
        predictions = model_utilies.predict_sentiment(
            input_path=clean_path,
            output_path="Data/predictions/predicted_Amazon_reviews.csv",
            model_dir="marbert_model",
            tokenizer_dir="tokenizer",
            sample_size=300,
        )
        etl_logger.info("Sentiment prediction completed.")

        # === 4. Load ===
        etl_logger.info("Starting data load to database...")
        load_data.load_data(
            path_of_df="../Data/predictions/predicted_Amazon_reviews.csv",
            path_of_config="../config/setting.yaml",
        )
        etl_logger.info("Data successfully loaded into database.")

        # === 5. Alerts ===
        etl_logger.info("Checking for products with high negative reviews...")
        alerts = load_negative_reviews_alerts("../config/setting.yaml")
        if alerts:
            etl_logger.info(
                f"{len(alerts)} alerts generated. Sending email notifications..."
            )
            send_alert_emails(alerts, confg)
            etl_logger.info("Alert emails sent successfully.")
        else:
            etl_logger.info("No alerts to send.")

        etl_logger.info("ETL process completed successfully.")
        return predictions

    except FileNotFoundError as e:
        etl_logger.error(f"File not found: {e}")
        etl_logger.debug(traceback.format_exc())
        raise
    except Exception as e:
        etl_logger.critical(f"Unexpected ETL error: {e}")
        etl_logger.debug(traceback.format_exc())
        raise


if __name__ == "__main__":
    run_etl()
