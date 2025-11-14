import mysql.connector as my
import pandas as pd
from logging_confg import setup_logger

logger = setup_logger("load_batch_to_db")


def load_batch_to_db(df_batch, db_conf, threshold=20):
    """
    Load a single batch into the database using district_id:
    1. Insert/update district_stats
    2. Insert reviews
    3. Update notifications (status yes/no based on threshold)
    """
    if df_batch.empty:
        logger.warning("Batch is empty. Skipping DB load.")
        return

    conn = None
    cursor = None

    try:
        conn = my.connect(**db_conf)
        cursor = conn.cursor()
        logger.info("Connected to DB")

        # --- 1️⃣ Update/Insert district_stats and get district_id ---
        stats_df = (
            df_batch.groupby(["governorate", "district"])
            .agg(
                total_reviews=("review", "count"),
                num_positive=("predicted_sentiment", lambda x: (x == "إيجابي").sum()),
                num_negative=("predicted_sentiment", lambda x: (x == "سلبي").sum()),
                num_neutral=("predicted_sentiment", lambda x: (x == "محايد").sum()),
            )
            .reset_index()
        )

        district_ids = {}

        for _, row in stats_df.iterrows():
            cursor.execute(
                """
                SELECT district_id FROM district_stats
                WHERE governorate=%s AND district=%s
            """,
                (row["governorate"], row["district"]),
            )
            res = cursor.fetchone()

            if res:
                district_id = res[0]
                cursor.execute(
                    """
                    UPDATE district_stats
                    SET total_reviews=%s, num_positive=%s, num_negative=%s, num_neutral=%s
                    WHERE district_id=%s
                """,
                    (
                        row["total_reviews"],
                        row["num_positive"],
                        row["num_negative"],
                        row["num_neutral"],
                        district_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO district_stats (governorate,district,total_reviews,num_positive,num_negative,num_neutral)
                    VALUES(%s,%s,%s,%s,%s,%s)
                """,
                    (
                        row["governorate"],
                        row["district"],
                        row["total_reviews"],
                        row["num_positive"],
                        row["num_negative"],
                        row["num_neutral"],
                    ),
                )
                district_id = cursor.lastrowid

            district_ids[(row["governorate"], row["district"])] = district_id

        conn.commit()
        logger.info("district_stats updated")

        # --- 2️⃣ Insert reviews ---
        vals = [
            (
                district_ids[(row["governorate"], row["district"])],
                row["review"],
                row["predicted_sentiment"],
                row["stars"],
            )
            for _, row in df_batch.iterrows()
        ]

        cursor.executemany(
            """
            INSERT INTO reviews (district_id, review_text, predicted_sentiment, stars)
            VALUES (%s,%s,%s,%s)
        """,
            vals,
        )
        conn.commit()
        logger.info(f"{len(vals)} reviews inserted")

        # --- 3️⃣ Update notifications ---
        for _, row in stats_df.iterrows():
            district_id = district_ids[(row["governorate"], row["district"])]
            num_neg = row["num_negative"]

            cursor.execute(
                """
                SELECT num_negative, status FROM notifications
                WHERE district_id=%s
            """,
                (district_id,),
            )
            res = cursor.fetchone()

            if res:
                prev_num, status = res
                if status == "no":
                    new_num = prev_num + num_neg
                    new_status = "yes" if new_num >= threshold else "no"
                    cursor.execute(
                        """
                        UPDATE notifications
                        SET num_negative=%s, status=%s
                        WHERE district_id=%s
                    """,
                        (new_num, new_status, district_id),
                    )
            else:
                new_status = "yes" if num_neg >= threshold else "no"
                cursor.execute(
                    """
                    INSERT INTO notifications(district_id,num_negative,threshold,status)
                    VALUES(%s,%s,%s,%s) 
                    WHERE num_negative >= 0
                """,
                    (district_id, num_neg, threshold, new_status),
                )

        conn.commit()
        logger.info("notifications updated")

    except Exception as e:
        logger.exception(f"Error loading batch: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("DB connection closed")
