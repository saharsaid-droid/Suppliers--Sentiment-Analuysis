import os, traceback
import yaml
import pandas as pd
from extract_data import extract_batch
from transform_data import preprocess_text_batch
from model_utilies import predict_sentiment_batch
from load_data import load_batch_to_db as load_data
from alert_system import load_district_negative_alerts, send_district_alert_emails

CONFIG_PATH = r"D:\Product Sentiment analysis\config\setting.yaml"


# --------------------------- Load Config --------------------------- #
def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------------------- Main Pipeline --------------------------- #
def main():
    print("\n--- Sentiment Pipeline Started ---\n")

    config = load_config()

    try:
        # 1️⃣ Extract
        print("Extracting batch...")
        df = extract_batch("reviews_data.csv")

        # 2️⃣ Transform
        print("Cleaning text...")
        df = preprocess_text_batch(df)

        # 3️⃣ Prediction
        print("Predicting sentiment...")
        df = predict_sentiment_batch(
            df,
            model_dir=config["model_settings"]["model_dir"],
            tokenizer_dir=config["model_settings"]["tokenizer_dir"],
            batch_number=config["batch_settings"]["batch_number"],
        )

        # 4️⃣ Load
        print("Loading to database...")
        load_batch_to_db(df)

        # 5️⃣ Alerts
        print("Checking alert rules...")
        alerts = load_district_negative_alerts()

        if alerts:
            send_district_alert_emails(alerts, config["email_settings"])
            print("\nAlert emails have been sent.\n")
        else:
            print("\nNo alert triggered.\n")

        print("\n--- Pipeline Finished Successfully ---\n")

    except Exception as e:
        error_message = traceback.format_exc()

        print("\n❌ Pipeline Failed!\n")
        print(error_message)

        # 🔴 Send failure email
        send_district_alert_emails(
            [
                {
                    "district_id": "SYSTEM",
                    "alert_message": f"Pipeline Failed:\n{error_message}",
                }
            ],
            config.get("email_settings", {}),
        )


# --------------------------- Run Script --------------------------- #
if __name__ == "__main__":
    main()
